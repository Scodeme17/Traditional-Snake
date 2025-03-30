import pygame
import random
import time
import collections
import os
from datetime import datetime
import numpy as np
from PIL import Image
import gui
from bfs import bfs_search
from dfs import dfs_search
from bidirectional import bidirectional_search

# Initialize Pygame
pygame.init()

# Constants from gui module
WIDTH, HEIGHT = gui.WIDTH, gui.HEIGHT
GRID_SIZE = gui.GRID_SIZE
GRID_WIDTH = gui.GRID_WIDTH
GRID_HEIGHT = gui.GRID_HEIGHT
IDLE, RUNNING, PAUSED, GAME_OVER = gui.IDLE, gui.RUNNING, gui.PAUSED, gui.GAME_OVER

class SnakeGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        
        # Initialize algorithms
        self.algorithms = ["BFS", "DFS", "Bidirectional"]
        self.current_algorithm = 0
        self.algo_button = gui.Button(WIDTH - 120, 10, 110, 30, self.algorithms[self.current_algorithm])
        
        # Initialize game options
        self.two_player_mode = False
        self.game_mode = 'Classic'  # Classic, Challenge, Survival
        self.difficulty = 'Normal'  # Easy, Normal, Hard
        
        # Create renderer
        self.reset_game()
        self.renderer = gui.GameRenderer(self)
        
    def reset_game(self):
        # Game state
        self.state = IDLE
        self.score = 0
        self.ai_score = 0 if self.two_player_mode else 0
        self.frame_count = 0
        self.current_time = time.time()
        self.pause_time = 0
        
        # Flag to track if manual input was received this frame
        self.manual_input = False
        
        # Set difficulty-based attributes
        if hasattr(self, 'difficulty'):
            if self.difficulty == 'Easy':
                self.move_cooldown = 7  # Slower
                self.bonus_food_chance = 0.1
                self.num_obstacles = 0
            elif self.difficulty == 'Normal':
                self.move_cooldown = 5  # Normal speed
                self.bonus_food_chance = 0.2
                self.num_obstacles = 5 if not hasattr(self, 'game_mode') or self.game_mode != 'Classic' else 0
            else:  # Hard
                self.move_cooldown = 3  # Faster
                self.bonus_food_chance = 0.3
                self.num_obstacles = 10 if not hasattr(self, 'game_mode') or self.game_mode != 'Classic' else 3
        else:
            # Default values if difficulty not set yet
            self.move_cooldown = 5
            self.bonus_food_chance = 0.2
            self.num_obstacles = 0
        
        # Initialize player snake
        self.snake = [(GRID_WIDTH // 4, GRID_HEIGHT // 2)]
        self.direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        
        # Initialize AI snake for two-player mode
        if hasattr(self, 'two_player_mode') and self.two_player_mode:
            self.ai_snake = [(GRID_WIDTH * 3 // 4, GRID_HEIGHT // 2)]
            self.ai_direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            self.ai_path = []
        
        # Create obstacles
        self.obstacles = []
        self.create_obstacles()
        
        # Place food
        self.place_food()
        
        # Path finding
        self.path = []
        
        # Score doubling mechanism
        self.double_score_active = False
        self.double_score_start_time = 0
        self.double_score_duration = 10  # seconds
        
        # Challenge mode timer
        if hasattr(self, 'game_mode') and self.game_mode == 'Challenge':
            self.challenge_duration = 60  # 60 seconds for challenge mode
            self.challenge_start_time = 0
        
        # Survival mode properties
        if hasattr(self, 'game_mode') and self.game_mode == 'Survival':
            self.survival_speed_increase = 0
            self.survival_speed_threshold = 5  # Every 5 points, speed increases
        
    def create_obstacles(self):
        """Create obstacles based on difficulty and game mode"""
        self.obstacles = []
        
        # Skip obstacle creation for classic mode on easy difficulty
        if (hasattr(self, 'game_mode') and self.game_mode == 'Classic' and 
            hasattr(self, 'difficulty') and self.difficulty == 'Easy'):
            return
            
        # Create random obstacles
        for _ in range(self.num_obstacles):
            while True:
                obstacle = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                # Make sure obstacles don't spawn on snakes or too close to them
                if (obstacle not in self.snake and 
                    (not hasattr(self, 'ai_snake') or obstacle not in self.ai_snake) and
                    self.is_position_safe(obstacle)):
                    self.obstacles.append(obstacle)
                    break
    
    def is_position_safe(self, pos):
        """Check if a position is safe to place an obstacle (not too close to snake heads)"""
        if len(self.snake) > 0:
            head_x, head_y = self.snake[0]
            pos_x, pos_y = pos
            # Don't place obstacles within 3 units of the snake head
            if abs(head_x - pos_x) <= 3 and abs(head_y - pos_y) <= 3:
                return False
                
        if hasattr(self, 'ai_snake') and len(self.ai_snake) > 0:
            ai_head_x, ai_head_y = self.ai_snake[0]
            pos_x, pos_y = pos
            # Don't place obstacles within 3 units of the AI snake head
            if abs(ai_head_x - pos_x) <= 3 and abs(ai_head_y - pos_y) <= 3:
                return False
                
        return True
        
    def place_food(self):
        while True:
            self.food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if (self.food not in self.snake and 
                self.food not in self.obstacles and
                (not hasattr(self, 'ai_snake') or self.food not in self.ai_snake)):
                break
        
        # Random chance for bonus food
        self.is_bonus_food = random.random() < self.bonus_food_chance
    
    def get_neighbors(self, pos, is_ai=False):
        x, y = pos
        neighbors = []
        
        # Possible moves: right, down, left, up
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            
            # Check if the neighbor is valid (not a wall, obstacle, or snake's body)
            if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and 
                (nx, ny) not in self.obstacles):
                
                if is_ai:
                    # For AI, avoid player snake and its own body except tail
                    if ((nx, ny) not in self.snake and 
                        (nx, ny) not in self.ai_snake[:-1]):
                        neighbors.append((nx, ny))
                else:
                    # For player, avoid AI snake and its own body except tail
                    if ((not hasattr(self, 'ai_snake') or (nx, ny) not in self.ai_snake) and 
                        (nx, ny) not in self.snake[:-1]):
                        neighbors.append((nx, ny))
        
        return neighbors
    
    def find_path(self, is_ai=False):
        """Find path using selected algorithm"""
        if self.algorithms[self.current_algorithm] == "BFS":
            return bfs_search(self, is_ai)
        elif self.algorithms[self.current_algorithm] == "DFS":
            return dfs_search(self, is_ai)
        elif self.algorithms[self.current_algorithm] == "Bidirectional":
            return bidirectional_search(self, is_ai)
    
    def move_player(self):
        """Move the player snake based on keyboard input or AI path"""
        # Get next move from path or calculate new path
        if not self.path:
            self.path = self.find_path()
            
            # If no path found, try to find any safe move
            if not self.path:
                head_x, head_y = self.snake[0]
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    nx, ny = head_x + dx, head_y + dy
                    if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and 
                        (nx, ny) not in self.obstacles and 
                        (nx, ny) not in self.snake[:-1] and
                        (not hasattr(self, 'ai_snake') or (nx, ny) not in self.ai_snake)):
                        self.path = [(nx, ny)]
                        break
                        
                # If still no path, game over
                if not self.path:
                    self.state = GAME_OVER
                    return
        
        # Get next position from path
        next_pos = self.path.pop(0)
        
        # Check if next position is valid
        head_x, head_y = self.snake[0]
        next_x, next_y = next_pos
        
        # Calculate direction vector
        dx, dy = next_x - head_x, next_y - head_y
        self.direction = (dx, dy)
        
        # Move snake
        self.snake.insert(0, next_pos)
        
        # Check if food was eaten
        if next_pos == self.food:
            score_increment = 2 if self.is_bonus_food else 1
            
            # Double score if feature is active
            if self.double_score_active:
                score_increment *= 2
            
            self.score += score_increment
            self.place_food()
            
            # Generate new path
            self.path = []
            
            # Activate double scoring after score reaches threshold
            if self.score >= 10 and not self.double_score_active:
                self.double_score_active = True
                self.double_score_start_time = time.time()
                
            # Survival mode speed increase
            if hasattr(self, 'game_mode') and self.game_mode == 'Survival':
                if self.score // self.survival_speed_threshold > self.survival_speed_increase:
                    self.survival_speed_increase = self.score // self.survival_speed_threshold
                    self.move_cooldown = max(1, self.move_cooldown - 0.5)
        else:
            # Remove tail
            self.snake.pop()
        
        # Check for collision with self, AI snake, or obstacles
        if (next_pos in self.snake[1:] or 
            next_pos in self.obstacles or
            (hasattr(self, 'ai_snake') and next_pos in self.ai_snake)):
            self.state = GAME_OVER
    
    def move_ai(self):
        """Move the AI snake"""
        if not hasattr(self, 'ai_path') or not self.ai_path:
            self.ai_path = self.find_path(is_ai=True)
            
            # If no path found, try to find any safe move
            if not self.ai_path:
                head_x, head_y = self.ai_snake[0]
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    nx, ny = head_x + dx, head_y + dy
                    if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and 
                        (nx, ny) not in self.obstacles and 
                        (nx, ny) not in self.snake and
                        (nx, ny) not in self.ai_snake[:-1]):
                        self.ai_path = [(nx, ny)]
                        break
                
                # If still no path, AI loses
                if not self.ai_path:
                    if self.two_player_mode:
                        self.state = GAME_OVER
                    return
        
        # Get next position from path
        next_pos = self.ai_path.pop(0)
        
        # Calculate direction
        head_x, head_y = self.ai_snake[0]
        next_x, next_y = next_pos
        self.ai_direction = (next_x - head_x, next_y - head_y)
        
        # Move AI snake
        self.ai_snake.insert(0, next_pos)
        
        # Check if food was eaten
        if next_pos == self.food:
            score_increment = 2 if self.is_bonus_food else 1
            self.ai_score += score_increment
            self.place_food()
            self.ai_path = []
        else:
            # Remove tail
            self.ai_snake.pop()
        
        # Check for collision
        if (next_pos in self.ai_snake[1:] or 
            next_pos in self.obstacles or
            next_pos in self.snake):
            if self.two_player_mode:
                self.state = GAME_OVER
    
    def handle_events(self):
        self.manual_input = False  # Reset the manual input flag each frame
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                result = gui.handle_button_events(self.renderer, self, mouse_pos)
                if result == 'restart':
                    self.reset_game()
                    
            if event.type == pygame.KEYDOWN:
                if self.state == RUNNING:
                    current_direction = self.direction
                    if event.key == pygame.K_RIGHT and current_direction != (-1, 0):
                        self.direction = (1, 0)
                        self.manual_input = True
                        self.path = []  # Clear AI path when manual control is used
                    elif event.key == pygame.K_LEFT and current_direction != (1, 0):
                        self.direction = (-1, 0)
                        self.manual_input = True
                        self.path = []
                    elif event.key == pygame.K_UP and current_direction != (0, 1):
                        self.direction = (0, -1)
                        self.manual_input = True
                        self.path = []
                    elif event.key == pygame.K_DOWN and current_direction != (0, -1):
                        self.direction = (0, 1)
                        self.manual_input = True
                        self.path = []
        
        return True
    
    def update(self):
        """Update game state"""
        self.current_time = time.time()
        
        # Store pause time for adjusting challenge timer
        if self.state == PAUSED:
            self.pause_time = self.current_time
        
        # Check challenge mode timer
        if (self.state == RUNNING and 
            hasattr(self, 'game_mode') and self.game_mode == 'Challenge' and
            self.current_time - self.challenge_start_time >= self.challenge_duration):
            self.state = GAME_OVER
        
        # Update double score timer
        if self.double_score_active:
            if self.current_time - self.double_score_start_time > self.double_score_duration:
                self.double_score_active = False
        
        # Move snakes if game is running
        if self.state == RUNNING:
            self.frame_count += 1
            if self.frame_count >= self.move_cooldown:
                # In two-player mode, manually control player snake 
                if self.two_player_mode:
                    # Handle manual control for player snake
                    # Get next position based on direction
                    head_x, head_y = self.snake[0]
                    dx, dy = self.direction
                    next_pos = (head_x + dx, head_y + dy)
                    
                    # Check if next position is valid
                    if (0 <= next_pos[0] < GRID_WIDTH and 0 <= next_pos[1] < GRID_HEIGHT and
                        next_pos not in self.obstacles and
                        next_pos not in self.snake[:-1] and
                        next_pos not in self.ai_snake):
                        
                        # Move snake
                        self.snake.insert(0, next_pos)
                        
                        # Check if food was eaten
                        if next_pos == self.food:
                            score_increment = 2 if self.is_bonus_food else 1
                            if self.double_score_active:
                                score_increment *= 2
                            self.score += score_increment
                            self.place_food()
                        else:
                            # Remove tail
                            self.snake.pop()
                    else:
                        # Collision occurred
                        self.state = GAME_OVER
                    
                    # Move AI snake
                    self.move_ai()
                else:
                    # In one-player mode, check if manual control was used
                    if self.manual_input:
                        # Apply manual control
                        head_x, head_y = self.snake[0]
                        dx, dy = self.direction
                        next_pos = (head_x + dx, head_y + dy)
                        
                        # Validate and execute manual move
                        if (0 <= next_pos[0] < GRID_WIDTH and 0 <= next_pos[1] < GRID_HEIGHT and
                            next_pos not in self.obstacles and
                            next_pos not in self.snake[:-1]):
                            
                            # Move snake
                            self.snake.insert(0, next_pos)
                            
                            # Check if food was eaten
                            if next_pos == self.food:
                                score_increment = 2 if self.is_bonus_food else 1
                                if self.double_score_active:
                                    score_increment *= 2
                                self.score += score_increment
                                self.place_food()
                            else:
                                # Remove tail
                                self.snake.pop()
                        else:
                            # Collision occurred
                            self.state = GAME_OVER
                    else:
                        # Use AI if no manual control
                        self.move_player()
                
                self.frame_count = 0
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            
            # Update game state
            self.update()
            
            # Drawing
            self.renderer.update_game_state(self)
            self.renderer.draw()
            
            # Take screenshot for GIF if game is running
            if self.state == RUNNING:
                self.renderer.take_screenshot(self.current_time)
            
            # Cap the frame rate
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()