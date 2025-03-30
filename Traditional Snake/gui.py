import pygame
from datetime import datetime
from PIL import Image

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (169, 169, 169)
DARK_RED = (150, 0, 0)
YELLOW = (255, 255, 0)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (120, 120, 220)
BUTTON_TEXT_COLOR = (255, 255, 255)
FONT = pygame.font.SysFont('Arial', 24)
SMALL_FONT = pygame.font.SysFont('Arial', 18)

# Game states
IDLE = 0
RUNNING = 1
PAUSED = 2
GAME_OVER = 3

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = FONT
        
    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) else BUTTON_COLOR
        
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        text_surface = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class GameRenderer:
    def __init__(self, game_state):
        self.game_state = game_state
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game with AI")
        
        # Buttons
        self.start_button = Button(WIDTH // 2 - 60, HEIGHT - 80, 120, 40, "Start")
        self.pause_button = Button(WIDTH // 2 - 60, HEIGHT - 80, 120, 40, "Pause")
        self.restart_button = Button(WIDTH // 2 - 60, HEIGHT - 80, 120, 40, "Restart")
        self.gif_button = Button(WIDTH // 2 - 120, HEIGHT - 30, 240, 30, "Save GIF Replay")
        
        # Player mode buttons
        self.player_mode_button = Button(WIDTH - 120, 50, 110, 30, "1P Mode")
        
        # Game mode buttons
        self.game_mode_button = Button(WIDTH - 120, 90, 110, 30, "Classic")
        
        # Difficulty buttons
        self.difficulty_button = Button(WIDTH - 120, 130, 110, 30, "Normal")
        
        # Screenshots for GIF creation
        self.screenshots = []
        self.last_screenshot_time = 0
        self.screenshot_interval = 0.2  # seconds
    
    def update_game_state(self, game_state):
        self.game_state = game_state
    
    def take_screenshot(self, current_time):
        if current_time - self.last_screenshot_time >= self.screenshot_interval:
            pygame_surface = pygame.Surface((WIDTH, HEIGHT))
            pygame_surface.blit(self.screen, (0, 0))
            pygame_array = pygame.surfarray.array3d(pygame_surface)
            pygame_array = pygame_array.transpose([1, 0, 2])
            self.screenshots.append(pygame_array)
            self.last_screenshot_time = current_time
    
    def save_gif(self):
        if not self.screenshots:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"snake_replay_{timestamp}.gif"
        
        print(f"Saving GIF to {filename}...")
        
        # Convert screenshots to PIL Images
        images = [Image.fromarray(screenshot) for screenshot in self.screenshots]
        
        # Save as GIF
        images[0].save(
            filename,
            save_all=True,
            append_images=images[1:],
            duration=self.screenshot_interval * 1000,  # milliseconds
            loop=0
        )
        
        print(f"GIF saved to {filename}")
    
    def draw_grid(self):
        """Draw a grid on the game board for better visibility"""
        # Grid has been removed
        pass
    
    def draw_obstacles(self):
        """Draw obstacles on the game board"""
        for obstacle in self.game_state.obstacles:
            obstacle_rect = pygame.Rect(
                obstacle[0] * GRID_SIZE, 
                obstacle[1] * GRID_SIZE, 
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(self.screen, GRAY, obstacle_rect)
    
    def draw_food(self):
        """Draw food with different colors for special foods"""
        food_rect = pygame.Rect(
            self.game_state.food[0] * GRID_SIZE, 
            self.game_state.food[1] * GRID_SIZE, 
            GRID_SIZE, GRID_SIZE
        )
        
        # Different color for special food (bonus food)
        if hasattr(self.game_state, 'is_bonus_food') and self.game_state.is_bonus_food:
            pygame.draw.rect(self.screen, YELLOW, food_rect)
        else:
            pygame.draw.rect(self.screen, GREEN, food_rect)
    
    def draw_snake(self, snake, is_player=True):
        """Draw the snake with smooth transitions and different colors for player/AI"""
        for i, (x, y) in enumerate(snake):
            snake_rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            if is_player:
                # Player snake: Dark red head, red body
                color = RED if i > 0 else DARK_RED
            else:
                # AI snake: Dark blue head, blue body
                color = BLUE if i > 0 else (0, 0, 150)
                
            pygame.draw.rect(self.screen, color, snake_rect)
            
            # Draw eyes on the head
            if i == 0:
                self.draw_snake_eyes(x, y, self.game_state.direction if is_player else self.game_state.ai_direction)
    
    def draw_snake_eyes(self, x, y, direction):
        """Draw eyes on the snake's head based on direction"""
        # Determine eye positions based on direction
        if direction == (1, 0):  # Right
            left_eye = (x * GRID_SIZE + GRID_SIZE * 0.7, y * GRID_SIZE + GRID_SIZE * 0.3)
            right_eye = (x * GRID_SIZE + GRID_SIZE * 0.7, y * GRID_SIZE + GRID_SIZE * 0.7)
        elif direction == (-1, 0):  # Left
            left_eye = (x * GRID_SIZE + GRID_SIZE * 0.3, y * GRID_SIZE + GRID_SIZE * 0.3)
            right_eye = (x * GRID_SIZE + GRID_SIZE * 0.3, y * GRID_SIZE + GRID_SIZE * 0.7)
        elif direction == (0, -1):  # Up
            left_eye = (x * GRID_SIZE + GRID_SIZE * 0.3, y * GRID_SIZE + GRID_SIZE * 0.3)
            right_eye = (x * GRID_SIZE + GRID_SIZE * 0.7, y * GRID_SIZE + GRID_SIZE * 0.3)
        else:  # Down
            left_eye = (x * GRID_SIZE + GRID_SIZE * 0.3, y * GRID_SIZE + GRID_SIZE * 0.7)
            right_eye = (x * GRID_SIZE + GRID_SIZE * 0.7, y * GRID_SIZE + GRID_SIZE * 0.7)
            
        # Draw the eyes (white with black pupils)
        pygame.draw.circle(self.screen, WHITE, (int(left_eye[0]), int(left_eye[1])), int(GRID_SIZE * 0.15))
        pygame.draw.circle(self.screen, WHITE, (int(right_eye[0]), int(right_eye[1])), int(GRID_SIZE * 0.15))
        pygame.draw.circle(self.screen, BLACK, (int(left_eye[0]), int(left_eye[1])), int(GRID_SIZE * 0.07))
        pygame.draw.circle(self.screen, BLACK, (int(right_eye[0]), int(right_eye[1])), int(GRID_SIZE * 0.07))
    
    def draw_path(self):
        """Draw the AI path with fading effect"""
        if self.game_state.state in [RUNNING, PAUSED] and hasattr(self.game_state, 'path'):
            for i, (x, y) in enumerate(self.game_state.path):
                path_rect = pygame.Rect(
                    x * GRID_SIZE + GRID_SIZE // 4, 
                    y * GRID_SIZE + GRID_SIZE // 4, 
                    GRID_SIZE // 2, GRID_SIZE // 2
                )
                alpha = 200 - min(i * 10, 150)  # Fade out based on distance
                s = pygame.Surface((GRID_SIZE // 2, GRID_SIZE // 2))
                s.set_alpha(alpha)
                s.fill(BLUE)
                self.screen.blit(s, path_rect)
    
    def draw_ui(self):
        """Draw UI elements like score, game status, buttons, etc."""
        # Draw score
        score_text = FONT.render(f"Score: {self.game_state.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw AI score if in 2P mode
        if hasattr(self.game_state, 'two_player_mode') and self.game_state.two_player_mode:
            ai_score_text = FONT.render(f"AI Score: {self.game_state.ai_score}", True, BLUE)
            self.screen.blit(ai_score_text, (10, 40))
        
        # Draw double score indicator
        if hasattr(self.game_state, 'double_score_active') and self.game_state.double_score_active:
            remaining_time = max(0, self.game_state.double_score_duration - 
                                (self.game_state.current_time - self.game_state.double_score_start_time))
            double_score_text = SMALL_FONT.render(f"DOUBLE SCORE: {remaining_time:.1f}s", True, YELLOW)
            self.screen.blit(double_score_text, (10, 70))
        
        # Draw algorithm name
        if hasattr(self.game_state, 'algorithms'):
            algo_text = SMALL_FONT.render(f"Algorithm:", True, WHITE)
            self.screen.blit(algo_text, (WIDTH - 200, 15))
            
            # Draw algorithm button
            self.game_state.algo_button.draw(self.screen)
        
        # Draw player mode button
        self.player_mode_button.draw(self.screen)
        
        # Draw game mode button
        self.game_mode_button.draw(self.screen)
        
        # Draw difficulty button
        self.difficulty_button.draw(self.screen)
        
        # Draw appropriate button based on game state
        if self.game_state.state == IDLE:
            self.start_button.draw(self.screen)
        elif self.game_state.state == RUNNING:
            self.pause_button.draw(self.screen)
        elif self.game_state.state == PAUSED:
            self.pause_button.draw(self.screen)
        elif self.game_state.state == GAME_OVER:
            self.restart_button.draw(self.screen)
            game_over_text = FONT.render("GAME OVER", True, RED)
            self.screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 20))
            
            # Draw winner in 2P mode
            if hasattr(self.game_state, 'two_player_mode') and self.game_state.two_player_mode:
                if self.game_state.score > self.game_state.ai_score:
                    winner_text = FONT.render("Player Wins!", True, RED)
                elif self.game_state.score < self.game_state.ai_score:
                    winner_text = FONT.render("AI Wins!", True, BLUE)
                else:
                    winner_text = FONT.render("It's a Tie!", True, WHITE)
                self.screen.blit(winner_text, (WIDTH // 2 - 80, HEIGHT // 2 + 20))
        
        # Draw time remaining in challenge mode
        if hasattr(self.game_state, 'game_mode') and self.game_state.game_mode == 'Challenge':
            if self.game_state.state == RUNNING:
                remaining = max(0, self.game_state.challenge_duration - 
                              (self.game_state.current_time - self.game_state.challenge_start_time))
                time_text = FONT.render(f"Time: {remaining:.1f}s", True, YELLOW)
                self.screen.blit(time_text, (WIDTH // 2 - 60, 10))
        
        # Draw GIF button when appropriate
        if self.game_state.state == GAME_OVER or self.game_state.state == PAUSED:
            self.gif_button.draw(self.screen)
    
    def draw(self):
        """Main draw method that renders the complete game screen"""
        self.screen.fill(BLACK)
        
        # Draw grid for better visibility (now removed but function still called)
        self.draw_grid()
        
        # Draw obstacles
        if hasattr(self.game_state, 'obstacles'):
            self.draw_obstacles()
        
        # Draw food
        self.draw_food()
        
        # Draw player snake
        self.draw_snake(self.game_state.snake, True)
        
        # Draw AI snake in 2P mode
        if hasattr(self.game_state, 'two_player_mode') and self.game_state.two_player_mode:
            if hasattr(self.game_state, 'ai_snake'):
                self.draw_snake(self.game_state.ai_snake, False)
        
        # Draw AI path
        self.draw_path()
        
        # Draw UI elements
        self.draw_ui()
        
        # Update display
        pygame.display.flip()


def handle_button_events(renderer, game_state, mouse_pos):
    """Handle all button click events"""
    # Start/Pause/Restart button
    if game_state.state == IDLE and renderer.start_button.is_clicked(mouse_pos):
        game_state.state = RUNNING
        if hasattr(game_state, 'game_mode') and game_state.game_mode == 'Challenge':
            game_state.challenge_start_time = game_state.current_time
    elif game_state.state == RUNNING and renderer.pause_button.is_clicked(mouse_pos):
        game_state.state = PAUSED
    elif game_state.state == PAUSED and renderer.pause_button.is_clicked(mouse_pos):
        game_state.state = RUNNING
        if hasattr(game_state, 'game_mode') and game_state.game_mode == 'Challenge':
            # Adjust challenge start time to account for pause duration
            game_state.challenge_start_time += (game_state.current_time - game_state.pause_time)
    elif game_state.state == GAME_OVER and renderer.restart_button.is_clicked(mouse_pos):
        return 'restart'
    
    # GIF button
    if (game_state.state == GAME_OVER or game_state.state == PAUSED) and renderer.gif_button.is_clicked(mouse_pos):
        renderer.save_gif()
    
    # Algorithm selection button
    if hasattr(game_state, 'algo_button') and game_state.algo_button.is_clicked(mouse_pos):
        game_state.current_algorithm = (game_state.current_algorithm + 1) % len(game_state.algorithms)
        game_state.algo_button.text = game_state.algorithms[game_state.current_algorithm]
        game_state.path = []  # Reset path on algorithm change
    
    # Player mode toggle
    if renderer.player_mode_button.is_clicked(mouse_pos):
        if hasattr(game_state, 'two_player_mode'):
            game_state.two_player_mode = not game_state.two_player_mode
            renderer.player_mode_button.text = "2P Mode" if game_state.two_player_mode else "1P Mode"
            return 'restart'
    
    # Game mode toggle
    if renderer.game_mode_button.is_clicked(mouse_pos):
        if hasattr(game_state, 'game_mode'):
            modes = ['Classic', 'Challenge', 'Survival']
            current_index = modes.index(game_state.game_mode)
            game_state.game_mode = modes[(current_index + 1) % len(modes)]
            renderer.game_mode_button.text = game_state.game_mode
            return 'restart'
    
    # Difficulty toggle
    if renderer.difficulty_button.is_clicked(mouse_pos):
        if hasattr(game_state, 'difficulty'):
            difficulties = ['Easy', 'Normal', 'Hard']
            current_index = difficulties.index(game_state.difficulty)
            game_state.difficulty = difficulties[(current_index + 1) % len(difficulties)]
            renderer.difficulty_button.text = game_state.difficulty
            return 'restart'
    
    return None  