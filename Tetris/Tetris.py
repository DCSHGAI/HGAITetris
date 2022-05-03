# Tetris in Python
# Modified by Bryce Bartlett
# Original code from https://levelup.gitconnected.com/writing-tetris-in-python-2a16bddb5318

import pygame
import random
import sys
from pywinauto import Application

# Use the number keys to toggle between windows
def Set_Focus(number_to_focus):
    try:
        app = Application().connect(title_re="ARL A.I Tetris " + number_to_focus)
        dlg = app.top_window()
        dlg.set_focus()
    except:
        print("Game " + number_to_focus + " does not exist.")

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
    # There are 7 blocks currently you can add your own.
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
    ]

    # The x and y values determine where the figure will appear on the screen
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures) - 1)
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

    def encourage(self, score_to_add):
        self.reward += score_to_add
   
    # Modify this to change how scoring works
    def update_score(self, score_to_add):
        self.score += score_to_add

    def state_evaluation(self):
        # Self.field contains the playing field if there is a non-zero number in the array
        # then that space is occupied by a shape.

        # This function tries to move pieces as far to the left as possible without overlapping.
       
        # Check down and to the left to see if its clear for an object
        field_index_to_check_y = (self.figure.y + 1) % 20
        field_index_to_check_x = (self.figure.x - 1) % 10

        if(self.field[field_index_to_check_y][field_index_to_check_x] == 0):
            self.go_side(-1)
        else:
            self.go_side(2)

        #print("Do something based on the state here in state_evaluation")

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

# If there aren't arguements just set the panel's name to 1
if len(sys.argv) != 0:
    pygame.display.set_caption("ARL A.I Tetris " + str(sys.argv[1]))
else:
    pygame.display.set_caption("ARL A.I Tetris 1")

done = False
clock = pygame.time.Clock()
fps = 30
game = Tetris(20, 10)
counter = 0
pressing_down = False
training_model_file_location = ""

# Main game infinite loop
while not done:
    if game.figure is None:
        game.new_figure()
    counter += .25 # Adjust speed here currently set to a quarter of the normal speed
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
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
            if event.key == pygame.K_SPACE:
                game.go_space()
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)
            if event.key == pygame.KSCAN_KP_ENTER:
                game.encourage(1)
            # Used number keys to switch panels if they exist
            if event.key == pygame.K_0:
                Set_Focus("0")
            if event.key == pygame.K_1:
                Set_Focus("1")           
            if event.key == pygame.K_2:
                Set_Focus("2")
            if event.key == pygame.K_3:
                Set_Focus("3")
            if event.key == pygame.K_4:
                Set_Focus("4")
            if event.key == pygame.K_5:
                Set_Focus("5")
            if event.key == pygame.K_6:
                Set_Focus("6")
            if event.key == pygame.K_7:
                Set_Focus("7")
            if event.key == pygame.K_8:
                Set_Focus("8")
            if event.key == pygame.K_9:
                Set_Focus("9")
          
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


    if game.figure_queue[0].type is not None:
        game.draw_queue(game.figure_queue[0], 0, screen)
    if game.figure_queue[1].type is not None:
        game.draw_queue(game.figure_queue[1], 1, screen)
    if game.figure_queue[2].type is not None:
        game.draw_queue(game.figure_queue[2], 2, screen)

    screen.blit(text, [0, 0])
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])

    game.state_evaluation()

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()