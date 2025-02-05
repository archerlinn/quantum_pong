import pygame
import math
import random
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# Window constants
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Gameplay constants
PLAYER_SPEED = 8
BALL_SPEED = 10
MAX_ANGLE = 60

# Lighting constants
LIGHT_RADIUS = 400

# Particle / FX constants
PARTICLE_COUNT = 100

# Default game settings
DEFAULT_TARGET_SCORE = 5

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plasma Pong - Quantum Edition")
clock = pygame.time.Clock()

# Load assets (replace with your own sound files)
#hit_sound = pygame.mixer.Sound('snd_hit.wav')
#explosion_sound = pygame.mixer.Sound('snd_explosion.wav')

# Create a light texture for the glow effect
light_texture = pygame.Surface((LIGHT_RADIUS * 2, LIGHT_RADIUS * 2))
light_texture.set_colorkey((0, 0, 0))
for i in range(LIGHT_RADIUS * 2):
    alpha = int(255 * (1 - abs(i - LIGHT_RADIUS) / LIGHT_RADIUS))
    pygame.draw.circle(
        light_texture,
        (255, 255, 255, alpha),
        (LIGHT_RADIUS, LIGHT_RADIUS),
        LIGHT_RADIUS - abs(i - LIGHT_RADIUS)
    )

# ----------------------------------------------
#               PARTICLE CLASS
# ----------------------------------------------
class Particle:
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.velocity = [random.uniform(-5, 5), random.uniform(-5, 5)]
        self.lifetime = 255

    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.lifetime -= 8
        # Gradually slow down
        self.velocity[0] *= 0.9
        self.velocity[1] *= 0.9

    def draw(self, surf):
        radius = int(self.lifetime / 50)
        if radius > 0:
            pygame.draw.circle(
                surf,
                (*self.color, self.lifetime),
                (int(self.pos[0]), int(self.pos[1])),
                radius
            )

# ----------------------------------------------
#                 BALL CLASS
# ----------------------------------------------
class Ball:
    def __init__(self):
        self.reset()
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.light_pos = (0, 0)
        self.trail = []

    def reset(self):
        self.rect = pygame.Rect(WIDTH // 2 - 15, HEIGHT // 2 - 15, 30, 30)
        angle = math.radians(random.choice([-MAX_ANGLE, MAX_ANGLE]))
        self.speed = [
            BALL_SPEED * math.copysign(math.cos(angle), random.choice([-1, 1])),
            BALL_SPEED * math.sin(angle)
        ]
        self.trail = []

    def update(self):
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]
        self.light_pos = self.rect.center
        
        # Add trail particle
        if len(self.trail) < 10:
            self.trail.append(Particle(self.rect.center, self.color))
        else:
            self.trail.pop(0)
            self.trail.append(Particle(self.rect.center, self.color))

    def draw(self, surf):
        for p in self.trail:
            p.draw(surf)
        pygame.draw.ellipse(surf, self.color, self.rect)

# ----------------------------------------------
#                PADDLE CLASS
# ----------------------------------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 120)
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.particles = []

    def update(self, dy):
        self.rect.y += dy
        # Keep paddle in bounds
        self.rect.y = max(50, min(HEIGHT - 170, self.rect.y))
        
        # Particle effect if moving
        if dy != 0:
            for _ in range(2):
                self.particles.append(Particle(self.rect.center, self.color))

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=10)
        # Update and draw paddle particles
        for p in self.particles:
            p.update()
            p.draw(surf)
        # Remove dead particles
        self.particles = [p for p in self.particles if p.lifetime > 0]

# ----------------------------------------------
#                 GAME CLASS
# ----------------------------------------------
class Game:
    def __init__(self, mode="pvp", target_score=DEFAULT_TARGET_SCORE):
        """
        :param mode: "pvp" -> Player vs Player, "pvc" -> Player vs Computer
        :param target_score: Score needed to win
        """
        self.mode = mode
        self.target_score = target_score

        # Create paddles
        self.player = Paddle(50, HEIGHT // 2 - 60)
        self.opponent = Paddle(WIDTH - 70, HEIGHT // 2 - 60)

        # Create ball
        self.ball = Ball()

        # Scores
        self.score = [0, 0]

        # Explosion particles
        self.particles = []

        # Light sources (ball + paddles)
        self.light_sources = []

        # Flag to track if game is running
        self.running = True

    def create_explosion(self, pos, color):
        for _ in range(PARTICLE_COUNT):
            self.particles.append(Particle(pos, color))
        #explosion_sound.play()

    def ai_opponent(self):
        """ Simple AI that tries to follow the ball vertically. """
        # Center of the opponent paddle:
        mid_opponent = self.opponent.rect.centery
        ball_center = self.ball.rect.centery

        if mid_opponent < ball_center:
            self.opponent.update(PLAYER_SPEED * 0.75)
        elif mid_opponent > ball_center:
            self.opponent.update(-PLAYER_SPEED * 0.75)

    def run(self):
        while self.running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return

            # Handle player inputs
            keys = pygame.key.get_pressed()

            # Player 1 (W/S)
            if keys[K_w]:
                self.player.update(-PLAYER_SPEED)
            elif keys[K_s]:
                self.player.update(PLAYER_SPEED)
            else:
                self.player.update(0)

            # Player 2 or AI
            if self.mode == "pvp":
                if keys[K_UP]:
                    self.opponent.update(-PLAYER_SPEED)
                elif keys[K_DOWN]:
                    self.opponent.update(PLAYER_SPEED)
                else:
                    self.opponent.update(0)
            elif self.mode == "pvc":
                self.ai_opponent()

            # Update ball
            self.ball.update()

            # Ball collisions with paddles
            if self.ball.rect.colliderect(self.player.rect) or self.ball.rect.colliderect(self.opponent.rect):
                self.ball.speed[0] *= -1.1  # increase speed slightly
                self.ball.color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
                #hit_sound.play()
                self.create_explosion(self.ball.rect.center, self.ball.color)

            # Ball collisions with top/bottom
            if self.ball.rect.top <= 0 or self.ball.rect.bottom >= HEIGHT:
                self.ball.speed[1] *= -1
                #hit_sound.play()

            # Scoring
            if self.ball.rect.left <= 0:
                self.score[1] += 1
                self.ball.reset()
            if self.ball.rect.right >= WIDTH:
                self.score[0] += 1
                self.ball.reset()

            # Check if someone reached the target score
            if self.score[0] >= self.target_score or self.score[1] >= self.target_score:
                self.running = False

            # Update explosion particles
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.lifetime > 0]

            # Update light sources
            self.light_sources = [
                self.ball.light_pos,
                self.player.rect.center,
                self.opponent.rect.center
            ]

            # --- DRAWING ---
            screen.fill((10, 10, 30))

            # Draw paddles and ball
            self.player.draw(screen)
            self.opponent.draw(screen)
            self.ball.draw(screen)

            # Draw the dynamic lighting
            light_overlay = pygame.Surface((WIDTH, HEIGHT))
            light_overlay.fill((0, 0, 0))
            for light in self.light_sources:
                light_overlay.blit(
                    light_texture,
                    (light[0] - LIGHT_RADIUS, light[1] - LIGHT_RADIUS),
                    special_flags=BLEND_RGBA_ADD
                )
            screen.blit(light_overlay, (0, 0), special_flags=BLEND_RGBA_MULT)

            # Draw explosion particles
            for p in self.particles:
                p.draw(screen)

            # Draw scores
            font = pygame.font.Font(None, 74)
            score_text = font.render(f"{self.score[0]}  {self.score[1]}", True, (200, 200, 200))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))

            pygame.display.flip()

        # Game finished, show winner briefly or return to menu
        winner = 0 if self.score[0] >= self.target_score else 1
        self.show_winner(winner)
        pygame.time.delay(2000)  # Show result for a couple of seconds

    def show_winner(self, winner):
        # Simple text display of who won
        font = pygame.font.Font(None, 100)
        text = font.render(f"Player {winner+1} Wins!", True, (255, 255, 100))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.fill((20, 20, 50))
        screen.blit(text, text_rect)
        pygame.display.flip()

# ----------------------------------------------
#               MENU FUNCTIONS
# ----------------------------------------------

def draw_text_centered(text, y, size=60, color=(255, 255, 255)):
    """ Helper function to draw text centered on the screen at y. """
    font = pygame.font.Font(None, size)
    rendered_text = font.render(text, True, color)
    rect = rendered_text.get_rect(center=(WIDTH // 2, y))
    screen.blit(rendered_text, rect)

def main_menu():
    """
    Main Menu loop. Returns a tuple: (mode, target_score)
      mode: 'pvp' or 'pvc'
      target_score: integer
    """
    selected_option = 0
    options = ["Player vs Player", "Player vs Computer", "Custom Score", "Start Game"]
    
    # We'll store the desired mode and score here
    chosen_mode = "pvp"
    chosen_score = DEFAULT_TARGET_SCORE

    menu_running = True
    while menu_running:
        clock.tick(FPS)
        screen.fill((30, 30, 60))

        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return None, None  # Signal to exit entirely
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == K_RETURN:
                    if options[selected_option] == "Player vs Player":
                        chosen_mode = "pvp"
                    elif options[selected_option] == "Player vs Computer":
                        chosen_mode = "pvc"
                    elif options[selected_option] == "Custom Score":
                        # Let user input a custom score
                        score = ask_for_score()
                        if score is not None:
                            chosen_score = score
                    elif options[selected_option] == "Start Game":
                        # Go to the game
                        menu_running = False

        # Draw the menu
        draw_text_centered("PLASMA PONG - QUANTUM EDITION", 100, 80, (255, 200, 50))
        
        y_start = 300
        spacing = 70
        for i, opt in enumerate(options):
            color = (255, 255, 255)
            if i == selected_option:
                color = (255, 0, 0)
            draw_text_centered(opt, y_start + i * spacing, 60, color)

        # Show chosen mode / score
        draw_text_centered(f"Mode: {chosen_mode.upper()}", 600, 40, (200, 200, 200))
        draw_text_centered(f"Target Score: {chosen_score}", 650, 40, (200, 200, 200))

        pygame.display.flip()

    return chosen_mode, chosen_score

def ask_for_score():
    """
    A very simple text input to let the user type a numeric score.
    """
    input_active = True
    user_text = ""

    while input_active:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return None
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    # Validate input is a positive integer
                    if user_text.isdigit():
                        return int(user_text)
                    else:
                        return None
                elif event.key == K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.unicode.isdigit():
                    user_text += event.unicode
                elif event.key == K_ESCAPE:
                    return None  # Cancel input

        # Draw input screen
        screen.fill((50, 50, 80))
        draw_text_centered("Enter target score:", 200, 60, (255, 255, 255))
        draw_text_centered(user_text, 400, 80, (255, 255, 0))
        pygame.display.flip()

# ----------------------------------------------
#                  MAIN LOOP
# ----------------------------------------------
def main():
    while True:
        chosen_mode, chosen_score = main_menu()
        # If the user closed the game from the menu
        if chosen_mode is None and chosen_score is None:
            break
        
        # Run the game with chosen settings
        game = Game(mode=chosen_mode, target_score=chosen_score)
        game.run()

if __name__ == "__main__":
    main()
    pygame.quit()
