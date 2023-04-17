# HGAI Tetris
# Unlimited Rights assigned to the U.S. Government
# This material may be reproduced by or for the U.S Government pursuant to the copyright license under the clause at DFARS 252.227-7014.
# This notice must appear in all copies of this file and its derivatives.
# Modified by Bryce Bartlett
# Original code from https://levelup.gitconnected.com/writing-tetris-in-python-2a16bddb5318

from dataclasses import field
from distutils import text_file
from inspect import BlockFinder
import os
import copy
import random
import sys
import re
import time
from tkinter import W
import time
import numpy
import StateEvaluation as gs

try:
    import pygame
except:
    print("Could not import Pygame!")

# These are default values that can be modified in the config file
#game_speed_modifier   = 100
#upper_speed_bound     = 0.1
queue_size            = 4
game_id               = 0
Is_Master             = False
Should_Load_Model     = False
Activate_Hidden_Rule  = False
Activate_Hidden_Piece = False
Activate_Hidden_Delay = 60
Speed_Increase        = False
hidden_piece_timer_elapsed = False
Activate_Immovable_Piece = False
Vertical_Line_Break_Mode = False
ShouldAddInvincibleRowsTypeOne = False
ShouldAddInvincibleRowsTypeTwo = False
ShouldAddInvincibleRowsTypeThree = False
Tetris_Board_X = 100
Tetris_Board_Y = 60
X_Offset       = 100
Row_Delta      = 0
Column_Delta   = 0
Row_Count      = 20
Column_Count   = 10
TetrisBoardYLowBound = 60
TickCounterForInvincibleRows = 30
Pause_Game = True
Saved_Field = []
StartTime = time.time()
GameProgress = 0
GameCanProgress = False
pygame.init()

# RGB Color definitions
colors = [
    (0, 0, 0),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
    (128,128,128)
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
        [[1, 4, 5, 9, 6]]
    ]

    # The x and y values determine where the figure will appear on the screen
    def __init__(self, x, y):
        self.x = x
        self.y = y
        if Activate_Hidden_Piece and hidden_piece_timer_elapsed:
            self.type = random.randint(0, len(self.figures) - 1)
        else:
            self.type = random.randint(0, len(self.figures) - 2)
        self.color = random.randint(1, len(colors) - 2)
        self.rotation = 0       


    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

def Read_Config():
    try:
        filepath = os.path.normpath(os.path.join(os.path.dirname(os.getcwd()), "Tetris/Config.txt"))
        config   = open(filepath, "r")
        lines    = config.readlines()
        if len(lines) > 10:
            global game_speed_modifier
            global queue_size
            global Should_Load_Model
            global Activate_Hidden_Rule
            global Activate_Hidden_Piece
            global Activate_Hidden_Delay
            global Speed_Increase
            global checkPointPath
            global upper_speed_bound
            global Tetris_Board_X
            global Tetris_Board_Y
            global X_Offset
            global Activate_Immovable_Piece
            global Row_Delta
            global Column_Delta
            global TetrisBoardYLowBound
            global ShouldAddInvincibleRowsTypeTwo
            global TickCounterForInvincibleRows
            
            # Variables are read in the order they appear in the config file
            game_speed_modifier = int(re.search(r"\d+", lines[3]).group()) * 0.01
            queue_size          = int(re.search(r"\d+", lines[5]).group())
            
            if lines[7].strip().split(",")[game_id] == "True":
                Activate_Hidden_Rule = True
            else:
                Activate_Hidden_Rule = False
            if lines[9].strip().split(",")[game_id] == "True":
                Activate_Hidden_Piece = True
            else:
                Activate_Hidden_Piece = False
            if lines[11].strip().split(",")[game_id] == "True":
                Speed_Increase = True
            else:
                Speed_Increase = False
                
            Activate_Hidden_Delay = int(lines[16])
            checkPointPath        = str(lines[14]).strip()
            upper_speed_bound     = float(lines[18])
            Tetris_Board_X        = int(lines[20])
            Tetris_Board_Y        = int(lines[21])
            X_Offset              = Tetris_Board_X - 100
            
            if lines[23].strip().split(",")[game_id] == "True":
                Activate_Immovable_Piece = True
            
            Row_Delta    = int(lines[25])
            Column_Delta = int(lines[27])

            if lines[29].strip().split(",")[game_id] == "True":
                ShouldAddInvincibleRowsTypeTwo = True

            TetrisBoardYLowBound = int(lines[31])

            TickCounterForInvincibleRows = int(lines[37])
    except Exception as Reason:
        print("Error Reading Config.txt: " + str(Reason))

# If there aren't arguements just set the panel's name to 1
if len(sys.argv) > 1:
    pygame.display.set_caption("ARL A.I Tetris " + str(sys.argv[1]))
    game_id = int(sys.argv[1])
else:
    pygame.display.set_caption("ARL A.I Tetris " + str(game_id))

#Read_Config()

# Game representation
class Tetris:
    level = 2
    score = 0
    state = "start"
    field = []
    finalStates   = []
    actionTree    = []
    visitedStates = []
    height = 0
    width  = 0
    x      = Tetris_Board_X
    y      = Tetris_Board_Y
    zoom   = 20
    figure = None
    figure_queue = []
    reward       = 0
    sim          = False
    should_flash_reward_text  = False
    reward_text_flash_time    = 90
    reward_text_flash_counter = 0
    feedback  = 0
    newFig    = 0
    lastMove  = -1
    gameid    = 0
    numGames  = 0
    numPieces = 0
    playAI    = False
    New_Figure_Created = False
    Shift_Playing_Field_Up = True
    Current_Shift_Level = 1
    Empty_Field = []

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.reward = 0
        self.state = "start"
        self.numPieces = 0
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        while len(self.figure_queue) < 4:
            adder = self.width/2-5
            adder = int(adder)
            if adder < 0:
                adder = 0
            
            self.figure_queue.append(Figure(3+adder, 0))
        self.figure = self.figure_queue.pop(0)
        self.newFig = 1
        self.numPieces += 1
        self.New_Figure_Created = True

    def intersects(self):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if (
                        i + self.figure.y > self.height - 1
                        or j + self.figure.x > self.width - 1
                        or j + self.figure.x < 0
                        or self.field[i + self.figure.y][j + self.figure.x] > 0
                    ):
                        intersection = True
        return intersection

    def break_lines(self):
        #SG BOMB TEST
        ## BOMB DYNAMICS
        ## 1. BOMBS DELETE WHAT THEY TOUCH BEFORE YOU GET POINTS
        ## 2. BOMBS ALSO DISAPPEAR
        ## 3. BOMBS ARE HARD CODED TO A SHAPE
        if enableBombs:
            for i in range(self.height-1, 0, -1):
                for j in range(self.width):
                    if self.field[i][j] == 100:
                        self.field[i][j] = 0
                        if i < self.height-1 :
                            self.field[i+1][j] = 0
            for i in range(self.height):
                for j in range(self.width):
                    if self.field[i][j] == 100:
                        self.field[i][j] = 0
        ## SG BRICK TEST
        ## BRICK DYNAMICS
        ##   1. BRICKS STAY WHERE THEY ARE AND DON'T DELETE
        ##   2. BRICKS CAN BE USED TO COMPLETE ROWS BUT (see 1)
        ##   3. ONLY WAY TO GET RID OF A BRICK IS
        ##      3.1 WITH A BOMB (see above BOMB test)
        ##      3.2 FORMING AN ENTIRE ROW OF BRICKS (this is a necessity)
        ##   4. BRICKS ARE HARD CODED TO A COLOR
        lines = 0
        if Vertical_Line_Break_Mode:
            for j in range(self.width):
                Line_Length = 0
                Line_Y_Position = 0
                for i in range(0, self.height):
                    if self.field[i][j] != 0 and self.field[i][j] != 7:
                        Line_Length += 1
                    else:
                        Line_Y_Position = i
                        Line_Length = 0
                    if Line_Length >= 10:
                        for jj in range(0,11):
                            nJ = Line_Y_Position+jj
                            if(nJ<self.height):
                                self.field[nJ][j] = 0
                        lines+=1
            game.score += lines*lines

        if not Vertical_Line_Break_Mode:
            for i in range(1, self.height):
                zeros = 0
                brcks = 0
                for j in range(self.width):
                    if self.field[i][j] == 0:
                        zeros += 1
                    if self.field[i][j] == 6:
                        brcks += 1
                if zeros == 0:
                    bricks = []
                    if brcks==self.width:
                        for j in range(self.width):
                            bricks.append(1)
                    else:
                        for j in range(self.width):
                            bricks.append(self.field[i][j])
                    
                    lines += 1
                    for i1 in range(i, 1, -1):
                        for j in range(self.width):
                            if enableBombs:
                                # Everything is being shifted down by one but if it is immovable prevent it from shifting.
                                if(bricks[j] != 6 and self.field[i1 - 1][j] != 6):
                                    self.field[i1][j] = self.field[i1 - 1][j]
                            if Activate_Immovable_Piece:
                                if(bricks[j] != 6 and self.field[i1 - 1][j] == 6):
                                    self.field[i1][j] = 0
                                    bricks[j] = 6
                            else:
                                if(self.field[i1][j] == 7):
                                    return
                                self.field[i1][j] = self.field[i1 - 1][j]
                    #game.score += 1
                    game.score += lines*lines

                    if Activate_Hidden_Rule:
                        Find_Area(self)

            # This is the base scoring system move or change this to modify how your score updates
            #self.update_score(lines**2)

    # Controls for the game

    def go_space(self):
        game.newFig = 0
        self.lastMove = 0  # GO DOWN

        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        game.newFig = 0
        self.lastMove = 0  # GO DOWN
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        #SG BOMB TEST
    
        if self.figure.type == 6 and self.figure.color>0 and enableBombs:
            for i in range(4):
                for j in range(4):
                    if i * 4 + j in self.figure.image():
                        self.field[i + self.figure.y][j + self.figure.x] = 100
        else:
            for i in range(4):
                for j in range(4):
                    if i * 4 + j in self.figure.image():
                        self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_side(self, dx):
        game.newFig = 0

        if dx > 0:
            self.lastMove = 1
        else:
            self.lastMove = 2
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        game.newFig = 0

        self.lastMove = 3

        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def update_reward(self, score_to_add):
        self.reward += score_to_add

    def encourage(self, score_to_add):
        # self.reward += score_to_add
        self.feedback = score_to_add

    def update_score(self, score_to_add):
        self.score += score_to_add

    # Modify this to change how scoring works
    def update_score(self, score_to_add):
        self.score += score_to_add

    # Draw rectangles off to the right to represent the next 3 shapes in the queue.
    def draw_queue(self, figure, position_in_queue, screen):
        color = colors[figure.color]
        xo    = 25
        if figure.type == 0:
            # Column
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 100) + 50, 100, 25)
            )
        elif figure.type == 1:
            # Slide
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 100) + 50, 50, 25)
            )
            pygame.draw.rect(
                screen, color, (375 + xo, (position_in_queue * 100) + 75, 50, 25)
            )
        elif figure.type == 2:
            # Other Slide
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 100) + 75, 50, 25)
            )
            pygame.draw.rect(
                screen, color, (375 + xo, (position_in_queue * 100) + 50, 50, 25)
            )
        elif figure.type == 3:
            # Bottom L
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 110) + 50, 25, 50)
            )
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 110) + 25, 50, 25)
            )
        elif figure.type == 4:
            # Top L
            pygame.draw.rect(
                screen, color, (375 + xo, (position_in_queue * 100) + 50, 25, 75)
            )
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 100) + 50, 25, 25)
            )
        elif figure.type == 5:
            # Half Plus
            pygame.draw.rect(
                screen, color, (350 + xo, (position_in_queue * 100) + 75, 75, 25)
            )
            pygame.draw.rect(
                screen, color, (375 + xo, (position_in_queue * 100) + 50, 25, 50)
            )
        elif figure.type == 6:
            # Square
            pygame.draw.rect(
                screen, color, (375 + xo, (position_in_queue * 100) + 50, 50, 50)
            )

# Define some colors for the UI
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY  = (128, 128, 128)
RED   = (255, 0, 0)

# Define the screen size and settings
size   = (500, 500)
screen = pygame.display.set_mode(size)
number_of_games_played = 0
last_figure_appearance = -1
done  = False
clock = pygame.time.Clock()
fps   = 10
game  = Tetris(Row_Count, Column_Count)
StartTime = time.time()
counter   = 0

# CHANGE THIS TO ENABLE BOMBS & BRICKS
# CURRENTLY BOMBS AND BRICKS ARE A PACKAGE DEAL
enableBombs   = False

# CHANGE THIS TO ENABLE RESIZING OF BOARD
# CURRENTLY BOARD GROWS BY 1 COL EVERY 4 GAMES
resizeGame    = False
pressing_down = False
last_move     = ""
auto_restart  = False
game.gameid   = game_id
counter       = 0
pressing_down = False
last_move     = ""
auto_restart  = True
rewardLearn   = False
gameCounter   = 0
prevx      = 0
prevy      = 0
runQuick   = False
game_stats = []

# Find the area of occupied space and if it exceeds
# a certain amount apply a bonus to the score
def Find_Area(game):
    if Activate_Hidden_Rule:
        Area = 0
        for row in game.field:
            for position in row:
                if position > 1:
                    Area += 1
        if Area > 40 and Area < 50:
            game.score += 100
            game.should_flash_reward_text = True

# Shift the playing field up or down
def Shift_Playing_Field(game):
    Field = game.field

    # This shifts up the field evenly
    if not ShouldAddInvincibleRowsTypeThree:
        if game.Shift_Playing_Field_Up:
            game.Current_Shift_Level += 1
            Field[0][0] = 7
            Field[0][1] = 7
            Field[0][2] = 7
            Field[0][3] = 7
            Field[0][4] = 7
            Field[0][5] = 7
            Field[0][6] = 7
            Field[0][7] = 7
            Field[0][8] = 7
            Field[0][9] = 7
            Field = numpy.roll(Field, -1, 0)
            game.field = Field
        else:
            Field = numpy.roll(Field, 1, 0)
            game.Current_Shift_Level -= 1
            Field[0][0] = 0
            Field[0][1] = 0
            Field[0][2] = 0
            Field[0][3] = 0
            Field[0][4] = 0
            Field[0][5] = 0
            Field[0][6] = 0
            Field[0][7] = 0
            Field[0][8] = 0
            Field[0][9] = 0
            game.field = Field
    else:
    # This shifts up the field unevenly
         if game.Shift_Playing_Field_Up:
            game.Current_Shift_Level += 1
            #Field[0][0] = 7
            Field[0][1] = 7
            #Field[0][2] = 7
            Field[0][3] = 7
            #Field[0][4] = 7
            Field[0][5] = 7
            #Field[0][6] = 7
            Field[0][7] = 7
            #Field[0][8] = 7
            Field[0][9] = 7
            Field = numpy.roll(Field, -1, 0)
            game.field = Field
         else:
            Field = numpy.roll(Field, 1, 0)
            game.Current_Shift_Level -= 1
            Field[0][0] = 0
            #Field[0][1] = 0
            Field[0][2] = 0
            #Field[0][3] = 0
            Field[0][4] = 0
            #Field[0][5] = 0
            Field[0][6] = 0
            #Field[0][7] = 0
            Field[0][8] = 0
            #Field[0][9] = 0
            game.field = Field

current_key = 0
textfile = open("gameStats" + str(game.gameid) + ".csv", "a")

# Main game infinite loop
while not done:
    if game.figure is None:
        game.new_figure()
        last_figure_appearance = pygame.time.Clock()
    counter += 1
    if counter > 100000:
        counter = 0

    # Oscillating Rows Control: Modifiable via TetrisBoardYLowBound and ShouldAddInvincibleRowsTypeTwo in the config file
    if ShouldAddInvincibleRowsTypeThree == True and counter % TickCounterForInvincibleRows == 0:
        # Set upper limit and reverse
        if(game.Current_Shift_Level >= 10):
            game.Shift_Playing_Field_Up = False
        if(game.Current_Shift_Level <= 4):
            game.Shift_Playing_Field_Up = True
        Shift_Playing_Field(game)

    if ShouldAddInvincibleRowsTypeTwo == True and counter % TickCounterForInvincibleRows == 0:
        # Set upper limit and reverse
        if(game.Current_Shift_Level >= 10):
            game.Shift_Playing_Field_Up = False
        if(game.Current_Shift_Level <= 4):
            game.Shift_Playing_Field_Up = True
        Shift_Playing_Field(game)

    if ShouldAddInvincibleRowsTypeOne and game.New_Figure_Created:
        # Set upper limit and reverse
        if(game.Current_Shift_Level >= 10):
            game.Shift_Playing_Field_Up = False
        if(game.Current_Shift_Level <= 4):
            game.Shift_Playing_Field_Up = True
        Shift_Playing_Field(game)
        game.New_Figure_Created = False

    # GET COPY OF EVENTS
    events = pygame.event.get()
    tamerFilename = gs.GameStateEvaluation(game,events,Vertical_Line_Break_Mode,current_key,runQuick)
    
    #if runQuick == False:
        #pygame.time.wait(500)
    
    prevx = game.figure.x
    prevy = game.figure.y
    
    if game.playAI == False:
        if counter % (fps // game.level // 2) == 0 or pressing_down:
            if game.state == "start":
                game.go_down()
                

    # Listens for keypresses and calls their respective functions
    for event in events:
        if event.type == pygame.QUIT:
            done = True
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            if not (textfile.closed):
                textfile.write(event.unicode)

            if event.key == pygame.K_1:
                ShouldAddInvincibleRowsTypeTwo = False
                ShouldAddInvincibleRowsTypeThree = False
                if(ShouldAddInvincibleRowsTypeOne == True):
                    ShouldAddInvincibleRowsTypeOne = False
                else:
                    ShouldAddInvincibleRowsTypeOne = True
                    
            # if event.key == pygame.K_2:
            #     ShouldAddInvincibleRowsTypeOne = False
            #     ShouldAddInvincibleRowsTypeThree = False
            #     if(ShouldAddInvincibleRowsTypeTwo == True):
            #         ShouldAddInvincibleRowsTypeTwo = False
            #     else:
            #         ShouldAddInvincibleRowsTypeTwo = True
            
            # if event.key == pygame.K_3:
            #     ShouldAddInvincibleRowsTypeOne = False
            #     ShouldAddInvincibleRowsTypeTwo = False
            #     if(ShouldAddInvincibleRowsTypeThree == True):
            #         ShouldAddInvincibleRowsTypeThree = False
            #     else:
            #         ShouldAddInvincibleRowsTypeThree = True
            
            if event.key == pygame.K_4:
                current_key = 4
                
            if event.key == pygame.K_5:
                current_key = 5
            
            if event.key == pygame.K_6:
                current_key = 6
            
            if event.key == pygame.K_7:
                current_key = 7
            
            if event.key == pygame.K_8:
                current_key = 8
            
            if event.key == pygame.K_9:
                current_key = 9
                
            if event.key == pygame.K_h:
                current_key = 20
                
            if event.key == pygame.K_v:
                current_key = 10
                
            if event.key == pygame.K_UP:
                game.rotate()
                last_move   = 'rotate'
                #game.playAI = False
    
            if event.key == pygame.K_DOWN:
                pressing_down = True
                last_move     = "down"
                #game.playAI   = False
                
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
                last_move   = "left"
                #game.playAI = False
                
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
                last_move   = "right"
                #game.playAI = False
                
            if event.key == pygame.K_SPACE:
                game.go_space()
                last_move   = "down"
                game.playAI = False
                
            if event.key == pygame.K_ESCAPE:
                game.newFig   = 0
                game.lastMove = 0

            if event.key == pygame.K_p:
                Pause_Game = True
                number_of_games_played += 1
                game.numGames          = game.numGames + 1
                last_move              = "restart"
            
            if event.key == pygame.K_j:
                game.encourage(1)
                last_move = "encourage"
            
            if event.key == pygame.K_k:
                game.encourage(-1)
                last_move = "discourage"
            
            if event.key == pygame.K_a:
                if game.playAI == False:
                    game.playAI = True
                else:
                    game.playAI = False
                last_move = "Toggle AI"

            if event.key == pygame.K_t:
                if Vertical_Line_Break_Mode:
                    Vertical_Line_Break_Mode = False
                else:
                    Vertical_Line_Break_Mode = True
                
            if event.key == pygame.K_q:
                if runQuick == True:
                    runQuick = False
                else:
                    runQuick = True
                last_move = "Toggle Speed"
            
            if event.key == pygame.K_g:
                textfile = open("gameStats" + str(game.gameid) + ".csv", "w")
                for s in range(len(game_stats)):
                    tmp = game_stats[s]
                    textfile.write(
                        str(tmp[0]) + "," + str(tmp[1]) + "," + str(tmp[2]) + "\n"
                    )
                textfile.write(
                    str(game.numGames)
                    + ","
                    + str(game.numPieces)
                    + ","
                    + str(game.score)
                    + "\n"
                )
                textfile.close()

    if event.type == pygame.KEYUP:
        if event.key == pygame.K_DOWN:
            pressing_down = False

    screen.fill(WHITE)

    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(
                screen,
                GRAY,
                [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom],
                1,
            )
            if game.field[i][j] > 0:
                pygame.draw.rect(
                screen,
                colors[game.field[i][j]],
                        [
                            game.x + game.zoom * j + 1,
                            game.y + game.zoom * i + 1,
                            game.zoom - 2,
                            game.zoom - 1,
                        ],
                )

    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(
                        screen,
                        colors[game.figure.color],
                        [
                            game.x + game.zoom * (j + game.figure.x) + 1,
                            game.y + game.zoom * (i + game.figure.y) + 1,
                            game.zoom - 2,
                            game.zoom - 2,
                        ],
                    )

    current_time = time.time()
        
    font                  = pygame.font.SysFont("Calibri", 18, True, False)#25
    small_font = pygame.font.SysFont("Calibri", 10, True, False)#65
    text                  = font.render("Total Score: " + str(game.score), True, BLACK)

    if(gs.tamer != None):
        ai_text           = font.render('', True, BLACK)
    else:
        ai_text           = font.render('', True, BLACK)
        
    text_game_over        = font.render("Game Over", True, (255, 125, 0))
    text_game_over1       = font.render("Press ESC", True, (255, 215, 0))
    text_last_button_used = font.render(last_move, True, (0, 0, 0))
    
    if (game.should_flash_reward_text and game.reward_text_flash_counter < game.reward_text_flash_time):
        if game.reward_text_flash_counter % 2 == 0:
            #reward_text = font.render("Reward: " + str(game.reward), True, RED)
            text        = font.render("Score: " + str(game.score), True, RED)
        game.reward_text_flash_counter += 1
    else:
        #reward_text = font.render("Reward: " + str(game.reward), True, BLACK)
        text        = font.render("Score: " + str(game.score), True, BLACK)
        game.should_flash_reward_text = False
        game.reward_text_flash_counter = 0

    # Game Progress BLAH
    if (int(time.time() - StartTime) % 60 == 0) and GameCanProgress:
        GameProgress += 1
        GameCanProgress = False
        game.score = 0
        StartTime = time.time()
        if GameProgress == 1:
            Vertical_Line_Break_Mode = True
        if GameProgress == 2:
            game.playAI = True
            Vertical_Line_Break_Mode = False
        if GameProgress == 3:
            game.playAI = True
            Vertical_Line_Break_Mode = True
        Pause_Game = True

    # Activate the hidden rule after specified delay in config file
    if counter > Activate_Hidden_Delay:
        hidden_piece_timer_elapsed = True
    if game.figure_queue[0].type is not None:
        game.draw_queue(game.figure_queue[0], 0, screen)
    if game.figure_queue[1].type is not None:
        game.draw_queue(game.figure_queue[1], 1, screen)
    if game.figure_queue[2].type is not None:
        game.draw_queue(game.figure_queue[2], 2, screen)
    if game.state == "gameover":
        gameCounter += 1
        game.Current_Shift_Level = 1
        
        if auto_restart:
            
            #THIS IS WHERE GAME RESIZING HAPPENS
            cc    = int(Column_Count)
            nsize = [500+(cc-10)*25,500]
            if nsize[0] != size[0] or nsize[1] != size[1]:
                screen = pygame.display.set_mode(nsize)
                size   = nsize
                
            game.__init__(Row_Count, cc)
            if resizeGame:
                Column_Count += 0.25
            number_of_games_played += 1
            game.numGames          += 1
        Saved_Field = game.Empty_Field
        if game.playAI == False:
            Pause_Game = True

    # Control Text
    Game_Count_Text = font.render("Game Count: " + str(number_of_games_played), True, (0, 0, 0))
    Control_Text = font.render("CONTROLS", True, (0, 0, 0))
    Left_Text = small_font.render("← - Go Left", True, (0, 0, 0))
    Up_Text = small_font.render("↑ - Rotate Piece", True, (0, 0, 0))
    Right_Text = small_font.render("→ - Go Right", True, (0, 0, 0))
    Down_Text = small_font.render("↓ - Go Down", True, (0, 0, 0))
    #AI_Text = small_font.render("A Key - Toggle A.I", True, (0, 0, 0))
    Encourage_Text = small_font.render("J Key - Encourage A.I", True, (0, 0, 0))
    Discourage_Text = small_font.render("K Key - Discourage A.I", True, (0, 0, 0))
    #Vertical_Toggle_Text = small_font.render("Vertical Mode", True, (0, 0, 0))
    Pause_Toggle_Text = font.render("Press P to Start the Game", True, (0, 0, 0))
    #AI_Status_ON_Text = font.render("A.I ON", True, (0, 0, 0))
    #AI_Status_OFF_Text = font.render("A.I OFF", True, (0, 0, 0))
    Version_Text_Vertical = font.render("Vertical Mode", True, (0, 0, 0))
    Version_Text_Horizontal = font.render("Horizontal Mode", True, (0, 0, 0))
    ai_weights = small_font.render("AI "+tamerFilename,True,(0,0,0))
    Time_Label_Text = font.render("Time:", True, (0,0,0))
    Time_Text = font.render(str(round(time.time() - StartTime, 2)), True, (0, 0, 0))

    # Image work
    Base_Path = os.path.dirname(__file__)
    Image = os.path.join(Base_Path, "Capture.png")
    image_1 = pygame.image.load(Image)
    screen.blit(image_1, (0,0))
    
    screen.blit(Game_Count_Text, [0, 20])
    screen.blit(Time_Label_Text, [150, 0])
    screen.blit(Time_Text, [200,0])

    screen.blit(text, [0, 0])
    screen.blit(ai_text,[0, 19])
    if game.playAI:
        #screen.blit(AI_Status_ON_Text, [0, 38])
        screen.blit(Encourage_Text, [0, 100])
        screen.blit(Discourage_Text, [0, 120])
        screen.blit(ai_weights,[0,320])

    else:
        #screen.blit(AI_Status_OFF_Text, [0, 38])
        screen.blit(Up_Text, [0, 100])
        screen.blit(Left_Text, [0, 120])
        screen.blit(Right_Text, [0, 140])
        screen.blit(Down_Text, [0, 160])
    #screen.blit(AI_Text, [0, 180])
    #screen.blit(Vertical_Toggle_Text, [0, 240])
    screen.blit(Control_Text, [0, 80])

    
    if Pause_Game:
        screen.blit(Pause_Toggle_Text, [105, 40])
        pygame.display.flip()
    else:
        if Vertical_Line_Break_Mode:
            screen.blit(Version_Text_Vertical, [140,30])
        else:
            screen.blit(Version_Text_Horizontal, [140,30])

    pygame.display.flip()
    clock.tick(fps)

    # Write all the game info

    wgts  = gs.tamer.model.layers[1].get_weights()[0]
    bias  = gs.tamer.model.layers[1].get_weights()[1]

    WGTS = numpy.zeros([1, 47])
    for a in range(len(wgts)):
        WGTS[0,a] = wgts[a,0]
    WGTS[0,46] = bias[0]

    if not (textfile.closed):
        textfile.write(str(sum(game.field, [])) + ", Figure: " + str(game.figure.type) + ", Start Time: " + str(StartTime) + ", Time:" + str(time.time()) + ", Score: " + str(game.score) + ", Weights: " + str(wgts).replace('\n', '').replace(' ','') + ", Bias: " + str(bias).replace('\n', '').replace(' ','') + ", Game Count: " + str(gameCounter) + ", Vertical Mode: " + str(Vertical_Line_Break_Mode) + '\n')
    
    while Pause_Game:
        game.__init__(Row_Count, Column_Count)
        pygame.display.flip()
        events = pygame.event.get()
        GameCanProgress = True
        for event in events:
            if event.type == pygame.QUIT:
                done = True
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    Pause_Game = False
                    pressing_down = False
pygame.quit()
textfile.close()