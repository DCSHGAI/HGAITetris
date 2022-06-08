# Tetris in Python
# Modified by Bryce Bartlett
# Original code from https://levelup.gitconnected.com/writing-tetris-in-python-2a16bddb5318

import pygame
import random
import platform
import sys
import re

game_speed_modifier = .25
queue_size = 4
Is_Master = False
Should_Load_Model = False
Activate_Hidden_Rule = False
Activate_Hidden_Piece = False
Activate_Hidden_Delay = 60
Speed_Increase = False


# This is an optional import that allows you to switch panels with the number keys (Windows Only)
try:
    from pywinauto import Application
except ImportError:
    print("Could not import pywinauto")

# Use the number keys 0-9 to toggle between windows
def Set_Focus(number_to_focus):
    try:
        app = Application().connect(title_re="ARL A.I Tetris " + str(number_to_focus))
        dlg = app.top_window()
        dlg.set_focus()
        print("ARL A.I Tetris " + str(number_to_focus))
    except:
        print("Game " + str(number_to_focus) + " does not exist.")

# Read the A.I training model and parse it
def Read_Model():
    print("Read model here")

# RGB Color definitions
colors = [
    (0, 0, 0),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]

class Figure:
    x = 0
    y = 0

    # Add new pieces here
    #
    # There are 8 blocks currently you can add your own.
    # Blocks are defined in a grid that looks like this
    #
    # ~~~~~~~~~~~~~
    # |0 |1 |2 |3 |
    # |4 |5 |6 |7 |
    # |8 |9 |10|11|
    # |12|13|14|15|
    # ~~~~~~~~~~~~~
    # 
    # The first figure is defined as 1, 5, 9, 13 which when applied to the grid makes the straight line figure
    # 
    # ~~~~~~~~~~~~~
    # |  |1 |  |  |
    # |  |5 |  |  |
    # |  |9 |  |  |
    # |  |13|  |  |
    # ~~~~~~~~~~~~~
    #
    # The following arrays are the rotations that the shape can have so for the bar it can only
    # be up and down and on its side. The side rotation looks like
    # ~~~~~~~~~~~~~
    # |  |  |  |  |
    # |4 |5 |6 |7 |
    # |  |  |  |  |
    # |  |  |  |  |
    # ~~~~~~~~~~~~~

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
        [[1,4,5,9,6]]
    ]

    # The x and y values determine where the figure will appear on the screen
    def __init__(self, x, y):
        self.x = x
        self.y = y
        if(Activate_Hidden_Piece):
             self.type = random.randint(0, len(self.figures) - 1)
        else:
            self.type = random.randint(0, len(self.figures) - 2)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

class Tetris:
    level = 2
    score = 0
    state = "start"
    field = []
    height = 0
    width = 0
    x = 100
    y = 60
    zoom = 20
    figure = None
    figure_queue = []
    reward = 0
 
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.reward = 0
        self.state = "start"
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        while len(self.figure_queue) < 4:
            self.figure_queue.append(Figure(3,0))
        self.figure = self.figure_queue.pop(0)

    def intersects(self):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True
        return intersection

    def break_lines(self):
        lines = 0
        for i in range(1, self.height):
            zeros = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
                Find_Area(self)

        # This is the base scoring system move or change this to modify how your score updates
        self.update_score(lines ** 2)

    # Controls for the game

    def go_space(self):
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def update_reward(self, score_to_add):
        self.reward += score_to_add
   
    # Modify this to change how scoring works
    def update_score(self, score_to_add):
        self.score += score_to_add

    def state_evaluation(self):
        # Self.field contains the playing field if there is a non-zero number in the array
        # then that space is occupied by a shape.
        a = 1

    # Draw rectangles off to the right to represent the next 3 shapes in the queue.
    def draw_queue(self, figure, position_in_queue, screen):
        color = colors[figure.color]
        if figure.type == 0:
            # Column
            pygame.draw.rect(screen, color, (350, (position_in_queue * 100) + 50, 100, 25))
        elif figure.type == 1:
            # Slide
            pygame.draw.rect(screen, color, (350, (position_in_queue * 100) + 50, 50, 25))
            pygame.draw.rect(screen, color, (375, (position_in_queue * 100) + 75, 50, 25))
        elif figure.type == 2:
            # Other Slide
            pygame.draw.rect(screen, color, (350, (position_in_queue * 100) + 75, 50, 25))
            pygame.draw.rect(screen, color, (375, (position_in_queue * 100) + 50, 50, 25))
        elif figure.type == 3:
            # Bottom L
            pygame.draw.rect(screen, color, (350, (position_in_queue * 110) + 50, 25, 50))
            pygame.draw.rect(screen, color, (350, (position_in_queue * 110) + 25, 50, 25))
        elif figure.type == 4:
            # Top L
            pygame.draw.rect(screen, color, (375, (position_in_queue * 100) + 50, 25, 75))
            pygame.draw.rect(screen, color, (350, (position_in_queue * 100) + 50, 25, 25))
        elif figure.type == 5:
            # Half Plus
            pygame.draw.rect(screen, color, (350, (position_in_queue * 100) + 75, 75, 25))
            pygame.draw.rect(screen, color, (375, (position_in_queue * 100) + 50, 25, 50))
        elif figure.type == 6:
            #Square
             pygame.draw.rect(screen, color, (375, (position_in_queue * 100) + 50, 50, 50))

# Initialize the game engine (Do not delete)
pygame.init()

# Define some colors for the UI
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Define the screen size and settings
size = (500, 500)
screen = pygame.display.set_mode(size)
game_id = 0
number_of_games_played = 0
last_figure_appearance = -1

# If there aren't arguements just set the panel's name to 1
if len(sys.argv) > 1:
    pygame.display.set_caption("ARL A.I Tetris " + str(sys.argv[1]))
    game_id = int(sys.argv[1])
else:
    pygame.display.set_caption("ARL A.I Tetris 0")

done = False
clock = pygame.time.Clock()
fps = 30
game = Tetris(20, 10)
counter = 0
pressing_down = False
last_move = ""
auto_restart = False

   
def Read_Config():
    config = open("Config.txt", "r")
    lines = config.readlines()
    if len(lines) > 10:
       global game_speed_modifier
       global Is_Master
       global queue_size
       global Should_Load_Model
       global Activate_Hidden_Rule
       global Activate_Hidden_Piece
       global Activate_Hidden_Delay
       global Speed_Increase
       game_speed_modifier = int(re.search(r'\d+', lines[1]).group()) * .01
       queue_size = int(re.search(r'\d+', lines[2]).group())
       if(lines[4].strip().split(',')[game_id] == 'True'):
            Is_Master = True
       else:
            Is_Master = False
       if(lines[6].strip().split(',')[game_id] == 'True'):
            Activate_Hidden_Rule = True
       else:
            Activate_Hidden_Rule = False
       if(lines[8].strip().split(',')[game_id] == 'True'):
            Activate_Hidden_Piece = True
       else:
            Activate_Hidden_Piece = False
       if(lines[10].strip().split(',')[game_id] == 'True'):
            Speed_Increase = True
       else:
            Speed_Increase = False
       Activate_Hidden_delay = int(re.search(r'\d+', lines[11]).group())

def Find_Area(game):
    if(Activate_Hidden_Rule):
        Area = 0
        for row in game.field:
            for position in row:
                if position > 1:
                    Area += 1
        if(Area > 40):
            game.score += 100

Read_Config()

# Main game infinite loop
while not done:
    if game.figure is None:
        game.new_figure()
        last_figure_appearance = pygame.time.Clock()
    counter += game_speed_modifier
    if counter > 100000:
        counter = 0

    if counter % (fps // game.level // 2) == 0 or pressing_down:
        if game.state == "start":
            game.go_down()

    # Listens for keypresses and calls their respective functions
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
            if event.key == pygame.K_DOWN:
                pressing_down = True
                last_move = "down"
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
                last_move = "left"
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
                last_move = "right"
            if event.key == pygame.K_SPACE:
                game.go_space()
                last_move = "down"
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)
                number_of_games_played += 1
                last_move = "restart"
            if event.key == pygame.K_h:
                game.update_reward(1)
            # Used number keys to switch panels if they exist
            if event.key == pygame.K_0 and platform.system() == "Windows":
                Set_Focus(0)
            if event.key == pygame.K_1 and platform.system() == "Windows":
                Set_Focus(1)
            if event.key == pygame.K_2 and platform.system() == "Windows":
                Set_Focus(2)
            if event.key == pygame.K_3 and platform.system() == "Windows":
                Set_Focus(3)
            if event.key == pygame.K_4 and platform.system() == "Windows":
                Set_Focus(4)
            if event.key == pygame.K_5 and platform.system() == "Windows":
                Set_Focus(5)
            if event.key == pygame.K_6 and platform.system() == "Windows":
                Set_Focus(6)
            if event.key == pygame.K_7 and platform.system() == "Windows":
                Set_Focus(7)
            if event.key == pygame.K_8 and platform.system() == "Windows":
                Set_Focus(8)
            if event.key == pygame.K_9 and platform.system() == "Windows":
                Set_Focus(9)
          
    if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    screen.fill(WHITE)

    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen, GRAY, [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom], 1)
            if game.field[i][j] > 0:
                pygame.draw.rect(screen, colors[game.field[i][j]],
                                 [game.x + game.zoom * j + 1, game.y + game.zoom * i + 1, game.zoom - 2, game.zoom - 1])

    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color],
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                      game.y + game.zoom * (i + game.figure.y) + 1,
                                      game.zoom - 2, game.zoom - 2])

    font = pygame.font.SysFont('Calibri', 25, True, False)
    font1 = pygame.font.SysFont('Calibri', 65, True, False)
    text = font.render("Score: " + str(game.score), True, BLACK)
    text_game_over = font1.render("Game Over", True, (255, 125, 0))
    text_game_over1 = font1.render("Press ESC", True, (255, 215, 0))
    reward_text = font.render("Reward: " + str(game.reward), True, BLACK)


    if game.figure_queue[0].type is not None:
        game.draw_queue(game.figure_queue[0], 0, screen)
    if game.figure_queue[1].type is not None:
        game.draw_queue(game.figure_queue[1], 1, screen)
    if game.figure_queue[2].type is not None:
        game.draw_queue(game.figure_queue[2], 2, screen)

    screen.blit(text, [0, 0])
    screen.blit(reward_text, [0, 25])
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])
        if auto_restart:
            game.__init__(20, 10)
            

    game.state_evaluation()
    pygame.display.flip()
    clock.tick(fps)

pygame.quit()