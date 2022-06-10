# Tetris in Python
# Modified by Bryce Bartlett
# Original code from https://levelup.gitconnected.com/writing-tetris-in-python-2a16bddb5318

from os import name
from typing import Counter
import pygame
import random
import platform
import sys
import re
import numpy
import copy
import time
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input

checkPointPath = "tamer.hdf5"
game_speed_modifier = .25
upper_speed_bound = .01
queue_size = 4
Is_Master = False
Should_Load_Model = False
Activate_Hidden_Rule = False
Activate_Hidden_Piece = False
Activate_Hidden_Delay = 60
Speed_Increase = False
hidden_piece_timer_elapsed = False

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
        if(Activate_Hidden_Piece and hidden_piece_timer_elapsed):
             self.type = random.randint(0, len(self.figures) - 1)
        else:
            self.type = random.randint(0, len(self.figures) - 2)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

## CURRENT BASIC TAMER IMPLEMENTATION
class Tamer:
    def __init__(self):
        self.compiled = False
        self.model    = None
        self.runRandom = False
        self.compileModel() 
        self.record  = []
        self.arecord = []
        self.frecord = []
        self.load_record = []
        self.load_frecord = []
        
    def compileModel(self, optimizer = None, learning_rate = 0.001, metrics=[]):
        # construct generic model if one is not specified
        #initializer = tf.keras.initializers.Zeros()
        if self.model == None:
            input_shape = 46
            input1      = Input(shape = (input_shape,))
            x1          = Dense(1,kernel_initializer='zeros',bias_initializer='zeros')(input1)
            inputs      = [input1]

            self.model  = Model(inputs, outputs=[x1])#,y2,y3])
            
        # compile the model
        if optimizer == None:
            self.model.compile(optimizer = tf.keras.optimizers.SGD(lr=0.000005 / 47.0), loss='mse')
        else:
            self.model.compile(optimizer = optimizer, loss='mse')
        self.compiled = True
    
    def load_weights(self, filepath):
        if self.compiled==True:
            self.model.load_weights(filepath)
    
    def save_weights(self, filepath):
        if self.compiled==True:
            self.model.save_weights(filepath)
            
    def forward(self, state_state_feats):
        action  = numpy.random.randint(0,len(state_state_feats))
        ssfeats = numpy.zeros([len(state_state_feats),46])
        for s in range(len(state_state_feats)):
            for f in range(46):
                ssfeats[s,f] = state_state_feats[s][f]
        pred_rewards = numpy.zeros(len(state_state_feats))        
        
        rid = numpy.random.randint(0,10)
        
        if rid >= 8 and self.runRandom:
            action = numpy.random.randint(0,len(state_state_feats))
        else:
            if self.compiled == True:
                pred_rewards = self.model.predict(ssfeats,verbose=0)
                action       = numpy.argmax(pred_rewards)
            else:
                action = numpy.random.randint(0,len(state_state_feats))
        
        return action, pred_rewards
    
    def backward(self, prev_state_state_feats, prev_action, human_reward):
        # do a gradient update step
        if human_reward != 0 and prev_state_state_feats is not None and prev_action is not None and self.compiled == True:
            x = numpy.reshape(prev_state_state_feats[prev_action],(1,len(prev_state_state_feats[prev_action]))).astype('float32')
            y = numpy.reshape(numpy.array(human_reward,dtype='float32'),(1))
            self.model.fit(x,y,verbose=0)
    
    def batch_backward(self):
        if len(self.record) > 0:
            ssfeats = numpy.zeros([len(self.record),46])
            yvalue  = numpy.zeros([len(self.frecord)])
            for s in range(len(self.record)):
                tmp       = self.record[s]
                feat      = tmp[self.arecord[s]]
                yvalue[s] = self.frecord[s]
                for f in range(46):
                    ssfeats[s,f] = feat[f]
            self.model.fit(ssfeats,yvalue,verbose=0) 
            
    def all_backward(self):
        ssfeats = numpy.zeros([len(self.load_record),46])
        yvalue  = numpy.zeros([len(self.load_frecord)])
        for s in range(len(self.load_record)):
            tmp       = self.load_record[s]
            #feat      = tmp[self.load_arecord[s]]
            yvalue[s] = self.load_frecord[s]
            for f in range(46):
                ssfeats[s,f] = tmp[f]
        self.model.fit(ssfeats,yvalue,verbose=0) 
    
    def load_data(self,filepath):
        #LOOP ALL TEXTFILES (.CSV) IN DIRECTORY
        testFiles   = os.listdir(filepath)
        self.load_record  = []
        self.load_frecord = []
        for t in range(len(testFiles)):
            with open(filepath+testFiles[t], mode='r') as csv_file:
                csv_reader = csv.reader(csv_file)
                ndata      = list(csv_reader)
                for s in range(len(ndata)):
                    row = ndata[s]
                    self.load_record.append(copy.deepcopy(row[0:(len(row)-1)]))
                    self.load_frecord.append(copy.deepcopy(row[-1]))
        self.all_backward()

    def save_data(self,filename):
        ssfeats = numpy.zeros([len(self.record),46])
        yvalue  = numpy.zeros([len(self.frecord)])
        for s in range(len(self.record)):
            tmp       = self.record[s]
            feat      = tmp[self.arecord[s]]
            yvalue[s] = self.frecord[s]
            for f in range(46):
                ssfeats[s,f] = feat[f]
        textfile = open(filename,"w")
        for s in range(len(self.record)):
            for f in range(46):
                textfile.write(str(ssfeats[s,f]) + ",")
            textfile.write(str(yvalue[s]) + "\n");
        textfile.close()
        
## END TAMER CLASS       
## END TAMER CLASS       

class Tetris:
    level = 2
    score = 0
    state = "start"
    field = []
    finalStates   = []
    actionTree    = []
    visitedStates = []
    height = 0
    width = 0
    x = 100
    y = 60
    zoom = 20
    figure = None
    figure_queue = []
    reward = 0
    sim    = False
    should_flash_reward_text = False
    reward_text_flash_time = 90
    reward_text_flash_counter = 0
    feedback = 0
    newFig   = 0
    lastMove = -1
    gameid   = 0
    numGames = 0
    numPieces = 0

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.reward = 0
        self.state = "start"
        self.numPieces = 0

       # Hand-crafted Tetris Features (for TAMER)
        self.NUM_FEATS        = 46
        self.COL_HT_START_I   = 0
        self.MAX_COL_HT_I     = 10
        self.COL_DIFF_START_I = 11
        self.NUM_HOLES_I      = 20
        self.MAX_WELL_I       = 21
        self.SUM_WELL_I       = 22
        self.SQUARED_FEATS_START_I   = 23
        self.SCALE_ALL_SQUARED_FEATS = False
        self.HT_SQ_SCALE             = 100.0


        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        while len(self.figure_queue) < 4:
            self.figure_queue.append(Figure(3,0))
        self.figure = self.figure_queue.pop(0)
        self.newFig = 1
        self.numPieces += 1

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

    ## SIMULATION FUNCTION
    def intersectsSym(self,board,figure):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in figure.image():
                    if i + figure.y > self.height - 1 or \
                            j + figure.x > self.width - 1 or \
                            j + figure.x < 0 or \
                            board[i + figure.y][j + figure.x] > 0:
                        intersection = True
        return intersection

    ## SIMULATION FUNCTION
    def break_linesSym(self,board):
        lines = 0
        for i in range(1, self.height):
            zeros = 0
            for j in range(self.width):
                if board[i][j] == 0:
                    zeros += 1
            if zeros == 0:
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        board[i1][j] = board[i1 - 1][j]
        return board
        
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
                if(Activate_Hidden_Rule):
                    Find_Area(self)

        # This is the base scoring system move or change this to modify how your score updates
        self.update_score(lines ** 2)

    # Controls for the game

    def go_space(self):
        game.newFig   = 0
        self.lastMove = 0 # GO DOWN

        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    ## SIMULATION FUNCTION
    def go_downSym(self,board,figure):
        fig = copy.deepcopy(figure)
        if fig.x != figure.x:
            print('COPY ERROR')
            time.sleep(10)
        brd = copy.deepcopy(board)
        fig.y += 1
        symStopped = False
        if self.intersectsSym(brd,fig):
            fig.y -= 1
            brd = self.freezeSym(brd,fig)
            symStopped = True
        return brd, fig, symStopped
    
    def go_down(self):
        game.newFig   = 0
        
        self.lastMove = 0 # GO DOWN
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

    ## SIMULATION FUNCTION
    def freezeSym(self,board,figure):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in figure.image():
                    board[i + figure.y][j + figure.x] = figure.color
        board = self.break_linesSym(board)
        return board

    def go_sideSym(self, dx, board, figure):
        fig = copy.deepcopy(figure)
        
        old_x = figure.x
        fig.x += dx
        if self.intersectsSym(board,fig):
            fig.x = old_x
        return fig

    def go_side(self, dx):
        game.newFig   = 0

        if dx > 0:
            self.lastMove = 1
        else:
            self.lastMove = 2
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotateSym(self,board,figure):
        fig = copy.deepcopy(figure)
        old_rotation = figure.rotation
        fig.rotate()
        if self.intersectsSym(board,fig):
            fig.rotation = old_rotation
        
        return fig

    def rotate(self):
        game.newFig   = 0
        
        self.lastMove = 3
        
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def getFeatures(self,board):
        featsArray = numpy.zeros(46,)-1
        featsArray[self.NUM_HOLES_I] = 0
        featsArray[self.SUM_WELL_I]  = 0
        board = numpy.array(board)
        
        for row in range(self.height+1):
            for col in range(self.width):
                if board[row][col] > 0: #FILLED CELL
                    if(featsArray[self.COL_HT_START_I + col] == -1):
                        featsArray[self.COL_HT_START_I + col] = row
                    if(featsArray[self.MAX_COL_HT_I] == -1):
                        featsArray[self.MAX_COL_HT_I] = row
                else:  # empty cell
                    if (featsArray[self.COL_HT_START_I + col] != -1):
                        featsArray[self.NUM_HOLES_I] += 1
        if(featsArray[self.MAX_COL_HT_I] == -1):
            featsArray[self.MAX_COL_HT_I] = self.rows

        # get column difference features
        for col in range(self.width - 1):
            featsArray[self.COL_DIFF_START_I + col] = abs(featsArray[self.COL_HT_START_I + col] - featsArray[self.COL_HT_START_I + col + 1])

        # get well depth features
        for col in range(self.width):
            wellDepth = self.getWellDepth(col, board)
            featsArray[self.SUM_WELL_I] += wellDepth
            if wellDepth > featsArray[self.MAX_WELL_I]:
                featsArray[self.MAX_WELL_I] = wellDepth

        # get squared features and scale them so they're not too big
        for i in range(self.SQUARED_FEATS_START_I):
            featsArray[self.SQUARED_FEATS_START_I + i] = numpy.square(featsArray[i])
            if(i <= self.MAX_COL_HT_I or self.SCALE_ALL_SQUARED_FEATS):
                featsArray[self.SQUARED_FEATS_START_I + i] /= self.HT_SQ_SCALE

        return featsArray
   
    def getWellDepth(self, col, board):
        depth = 0
        for row in range(self.height):
            if(board[row][col] > 0):  # encountered a filled space, stop counting
                return depth
            else:
                if depth > 0:  # if well-depth count has begun, dont require left or right side to be filled
                    depth += 1
                # check if both the cell to the left if full and if the cell to the right is full
                elif (col == 0 or board[row][col-1] > 0) and (col == self.width-1 or board[row][col+1] > 0):
                    depth += 1
        return depth               

    def forwardProject(self,board,figure,alist):
        nlist = copy.deepcopy(alist)
        brd   = copy.deepcopy(board)
        fig   = copy.deepcopy(figure)
        x     = copy.deepcopy(fig.x)
        y     = copy.deepcopy(fig.y)
        r     = copy.deepcopy(fig.rotation)
        
        for m in range(0,len(self.visitedStates)):
            vs = self.visitedStates[m]
            if x == vs[0] and y == vs[1] and r == vs[2]:
                return
        
        if len(self.finalStates) > 50:
            return
        for a in range(0,4):
            symStopped  = False
            # TAKE ACTION A
            if a==0:
                nboard, nfigure, symStopped = self.go_downSym(brd,fig)
                nlist.append(a)
            elif a==1:
                nfigure                     = self.go_sideSym(1,brd,fig)
                nboard, nfigure, symStopped = self.go_downSym(brd,nfigure)
                nlist.append(a)
                nlist.append(0)
            elif a==2:
                nfigure                     = self.go_sideSym(-1,brd,fig)
                nboard, nfigure, symStopped = self.go_downSym(brd,nfigure)
                nlist.append(a)
                nlist.append(0)
            elif a==3:
                nfigure                     = self.rotateSym(brd,fig)
                nboard, nfigure, symStopped = self.go_downSym(brd,nfigure)
                nlist.append(a)
                nlist.append(0)
            
            if symStopped == False:
                self.forwardProject(nboard,nfigure,nlist)
                nlist.pop()
                if a > 0:
                    nlist.pop()
            else:
                match = False
                for s in range(0,len(self.finalStates)):
                    s0 = self.finalStates[s]
                    matched = True
                    for i in range(0,self.height):
                        for j in range(0,self.width):
                            if s0[i][j] != nboard[i][j]:
                                matched = False
                                break
                        if matched == False:
                            break
                    if matched == True:
                        match = True
                        break
                if match == False:
                    self.finalStates.append(copy.deepcopy(nboard))
                    self.actionTree.append(copy.deepcopy(nlist))
                #time.sleep(1.0)
                nlist.pop()
                if a > 0:
                    nlist.pop()
                    
            if len(nlist) > 25:
                #print("POPPING OUT")
                return
       
        self.visitedStates.append([x,y,r])
        return      

    def update_reward(self, score_to_add):
        self.reward += score_to_add

    def encourage(self, score_to_add):
        #self.reward += score_to_add
        self.feedback = score_to_add
   
    def update_score(self, score_to_add):
        self.score += score_to_add

    # Modify this to change how scoring works
    def update_score(self, score_to_add):
        self.score += score_to_add

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
RED = (255, 0, 0)

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
tamer = Tamer()
tamer.load_weights(checkPointPath)
game.gameid = game_id
gameSym = Tetris(20,10)
counter       = 0
pressing_down = False
last_move     = ""
auto_restart = True
playAI       = True
trainAI      = True
rewardLearn  = False
gameCounter  = 0
#lastWrite = 0
#version = 6
prevx = 0
prevy = 0 
actLoc                      = 0
prev_feedback               = 0
prev_prev_feedback          = 0
prev_reward                 = 0
prev_prev_reward            = 0
prev_action                 = None
prev_state_state_feats      = None
prev_prev_state_state_feats = None
state_state_feats           = None
action                      = 0
runQuick                    = False
Q_PLAN                      = False
game_stats 					= []

# TODO: Cleanup config formatting to make it consistent 
def Read_Config():
    try:
        config = open("Config.txt", "r")
        lines = config.readlines()
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
            game_speed_modifier = int(re.search(r'\d+', lines[1]).group()) * .01
            queue_size = int(re.search(r'\d+', lines[2]).group())
            if(lines[4].strip().split(',')[game_id] == 'True'):
                Activate_Hidden_Rule = True
            else:
                Activate_Hidden_Rule = False
            if(lines[6].strip().split(',')[game_id] == 'True'):
                Activate_Hidden_Piece = True
            else:
                Activate_Hidden_Piece = False
            if(lines[8].strip().split(',')[game_id] == 'True'):
                Speed_Increase = True
            else:
                Speed_Increase = False
            Activate_Hidden_Delay = int(re.search(r'\d+', lines[13]).group())
            checkPointPath = str(lines[11])
            upper_speed_bound = float(lines[15])
    except:
        print("Error Reading Config.txt")

def Find_Area(game):
    if(Activate_Hidden_Rule):
        Area = 0
        for row in game.field:
            for position in row:
                if position > 1:
                    Area += 1
        if(Area > 40 and Area < 50):
            game.score += 100
            game.should_flash_reward_text = True

Read_Config()

# Main game infinite loop
while not done:
    move          = False
    if game.figure is None:
        game.new_figure()
        last_figure_appearance = pygame.time.Clock()
    counter += game_speed_modifier
    if counter > 100000:
        counter = 0

    if playAI:
        if game.newFig == 1:
            # LEARN FROM LAST EPISODE FIRST!!!
            if trainAI and game.feedback != 0:
	            tamer.backward(prev_state_state_feats,prev_action,game.feedback)
	            tamer.record.append(prev_state_state_feats)
	            tamer.arecord.append(prev_action)
	            tamer.frecord.append(game.feedback)
                
            # TAMER LOOP
            # STEP 1: DEEP COPY OF GAME
            gameSym = copy.deepcopy(game)
            
            # STEP 2: FORWARD PROJECT OF PIECES
            gameSym.finalStates   = []
            gameSym.actionTree    = []
            gameSym.visitedStates = []
            field  = copy.deepcopy(gameSym.field)
            figure = copy.deepcopy(gameSym.figure)
            gameSym.forwardProject(field,figure,[])
            
            # STEP 2: COMPUTE STATE
            board = [[0 for x in range(10)]
                     for y in range(20)]
            board += [[1 for x in range(10)]]
            for i in range(10):
                for j in range(20):
                    board[j][i] = game.field[j][i]
            
            state0_feat = gameSym.getFeatures(board)
    
            # STEP 3: DIFF STATES
            state1_feats = []
            for piecePlacement in gameSym.finalStates:
                board = [[0 for x in range(10)]
                         for y in range(20)]
                board += [[1 for x in range(10)]]
                for i in range(10):
                    for j in range(20):
                        board[j][i] = piecePlacement[j][i]
                state1_feats.append(gameSym.getFeatures(board))
                
            # get state_state features
            state_state_feats = []
            for state1_feat in state1_feats:
                state_state_feats.append(state1_feat - state0_feat)
                
            # use tamer model to get best action
            action,actionSet = tamer.forward(state_state_feats)
            
            finalStates = copy.deepcopy(gameSym.finalStates)
            actionTree  = copy.deepcopy(gameSym.actionTree)

            if Q_PLAN:
                #QUEUE PROJECT
                # FOR EACH ACTION --> RUN ANOTHER PASS OF FORWARD PROJECT 
                ids = numpy.argsort(actionSet,axis=0)
                ids = numpy.flip(ids)
                total = 8
                if total > len(finalStates):
                    total = len(finalStates)
                for f in range(total):
                    gameSym.finalStates   = []
                    gameSym.actionTree    = []
                    gameSym.visitedStates = []
                    idF      = ids[f,0]
                    field    = copy.deepcopy(finalStates[idF])
                    figure   = copy.deepcopy(gameSym.figure_queue[0])
                    figure.x = gameSym.figure.x
                    figure.y = gameSym.figure.y
                    gameSym.forwardProject(field,figure,[])
                    
                    field = copy.deepcopy(finalStates[idF])
                    board = [[0 for x in range(10)]
                             for y in range(20)]
                    board += [[1 for x in range(10)]]
                    for i in range(10):
                        for j in range(20):
                            board[j][i] = field[j][i]
                    
                    stateX_feat = gameSym.getFeatures(board)
            
                    # STEP 3: DIFF STATES
                    stateY_feats = []
                    for piecePlacement in gameSym.finalStates:
                        board = [[0 for x in range(10)]
                                 for y in range(20)]
                        board += [[1 for x in range(10)]]
                        for i in range(10):
                            for j in range(20):
                                board[j][i] = piecePlacement[j][i]
                        stateY_feats.append(gameSym.getFeatures(board))
                        
                    # get state_state features
                    stateZ_feats = []
                    for stateY_feat in stateY_feats:
                        stateZ_feats.append(stateY_feat - stateX_feat)
                    qaction,qactionSet = tamer.forward(stateZ_feats)
                    actionSet[idF] += numpy.max(qactionSet)
                
                action = numpy.argmax(actionSet)
                
            # STEP 4: DETERMINE COA
            coa = []
            if action < len(actionTree):
                coa = actionTree[action]
            actLoc = 0
            
            # UPDATE PREV STATE VALUES (TO USE ON NEXT ITERATION)
            prev_state_state_feats = copy.deepcopy(state_state_feats)
            prev_action            = copy.deepcopy(action)
            prev_reward            = copy.deepcopy(game.score)
            prev_prev_feedback     = copy.deepcopy(prev_feedback)
            prev_feedback          = copy.deepcopy(game.feedback)
            game.feedback = 0
        
    
        if actLoc < len(coa):
            action = coa[actLoc]
            actLoc += 1
            if action==1:
                game.go_side(1)
            elif action==2:
                game.go_side(-1)
            elif action==3:
                game.rotate()
            else:
                game.go_down()
        else:
            game.go_down()
        if runQuick == False:
            time.sleep(game_speed_modifier)
            if(Speed_Increase):
                # Slowly increase the speed
                game_speed_modifier *= .99
                if(game_speed_modifier < upper_speed_bound):
                    game_speed_modifier = upper_speed_bound
    prevx = game.figure.x
    prevy = game.figure.y 

    if playAI == False:    
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
                game.newFig   = 0
                game.lastMove = 0
                game.__init__(20, 10)
                number_of_games_played += 1
                game.numGames = game.numGames + 1
                last_move = "restart"
            if event.key == pygame.K_j:
                game.encourage(1)
                game.reward += 1
            if event.key == pygame.K_k:
                game.encourage(-1)    
                game.reward -= 1
            if event.key == pygame.K_a:
                tamer.load_data("data\\")
            if event.key == pygame.K_s:
                tamer.save_data("data\\dataRun" + str(game.gameid) + ".csv")
            if event.key == pygame.K_w:
                tamer.save_weights("model\\tamer" + str(game.gameid) + ".hdf5")
            if event.key == pygame.K_b:
                tamer.batch_backward()
            if event.key == pygame.K_q:
                if runQuick == True:
                    runQuick = False
                else:
                    runQuick = True
            if event.key == pygame.K_r:
                if tamer.runRandom == True:
                    tamer.runRandom = False
                    print('Random OFF')
                else:
                    tamer.runRandom = True
                    print('Random ON')
            if event.key == pygame.K_t:
                if rewardLearn == True:
                    rewardLearn = False
                else:
                    rewardLearn = True
            if event.key == pygame.K_g:
                textfile = open("gameStats"+str(game.gameid)+".csv","w")
                for s in range(len(game_stats)):
                    tmp = game_stats[s]
                    textfile.write(str(tmp[0])+","+str(tmp[1])+","+str(tmp[2]) + "\n")
                textfile.write(str(game.numGames)+","+str(game.numPieces)+","+str(game.score)+"\n")
                textfile.close()
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

    if(game.should_flash_reward_text and game.reward_text_flash_counter < game.reward_text_flash_time):
        if(game.reward_text_flash_counter % 2 == 0):
            reward_text = font.render("Reward: " + str(game.reward), True, RED)
        game.reward_text_flash_counter += 1
    else:
        reward_text = font.render("Reward: " + str(game.reward), True, BLACK)
        game.should_flash_reward_text = False
        game.reward_text_flash_counter = 0

    # Activate the hidden rule after specified delay in config file
    if(counter > Activate_Hidden_Delay):
        hidden_piece_timer_elapsed = True

    if game.figure_queue[0].type is not None:
        game.draw_queue(game.figure_queue[0], 0, screen)
    if game.figure_queue[1].type is not None:
        game.draw_queue(game.figure_queue[1], 1, screen)
    if game.figure_queue[2].type is not None:
        game.draw_queue(game.figure_queue[2], 2, screen)
    if game.state == "gameover":
	    game_stats.append([game.numGames,game.numPieces,game.score])
	    textfile = open("gameStats"+str(game.gameid)+".csv","w")
	    for s in range(len(game_stats)):
		    tmp = game_stats[s]
		    textfile.write(str(tmp[0])+","+str(tmp[1])+","+str(tmp[2]) + "\n")
	    textfile.close()	
	    if auto_restart:
		    game.__init__(20, 10)
		    number_of_games_played += 1    
		    game.numGames += 1

    screen.blit(text, [0, 0])
    screen.blit(reward_text, [0, 25])
    pygame.display.flip()
    clock.tick(fps)
pygame.quit()