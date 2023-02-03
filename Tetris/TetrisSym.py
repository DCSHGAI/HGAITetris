# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 14:28:43 2022

@author: sgordon
"""
import numpy
import copy

class TetrisSym:
    level = 2
    score = 0
    state = "start"
    field = []
    finalStates    = []
    actionTree     = []
    visitedStates  = []
    finalLocations = []
    height = 0
    width = 0
    x = 100
    y = 60
    zoom = 20
    figure = None
    figure_queue = []
    reward = 0
    sim = False
    should_flash_reward_text = False
    reward_text_flash_time = 90
    reward_text_flash_counter = 0
    feedback  = 0
    newFig    = 0
    lastMove  = -1
    gameid    = 0
    numGames  = 0
    numPieces = 0
    playAI    = False
    Vertical_Line_Break_Mode = False
    use_all_dynamics = True
    

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.reward = 0
        self.state     = "start"
        self.numPieces = 0

        # Hand-crafted Tetris Features (for TAMER, i.e. example AI)
        self.NUM_FEATS = 2 * (2*self.width+3)#46
        self.COL_HT_START_I = 0
        self.MAX_COL_HT_I = self.width#10
        self.COL_DIFF_START_I = self.width+1#11
        self.NUM_HOLES_I = 2*self.width#self.height#20
        self.MAX_WELL_I = 2*self.width+1#21
        self.SUM_WELL_I = 2*self.width+2#22
        self.SQUARED_FEATS_START_I = 2*self.width+3#23
        self.SCALE_ALL_SQUARED_FEATS = False
        self.HT_SQ_SCALE = 100.0

        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    ## SIMULATION FUNCTION
    def intersectsSym(self, board, figure):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in figure.image():
                    if (
                        i + figure.y > self.height - 1
                        or j + figure.x > self.width - 1
                        or j + figure.x < 0
                        or board[i + figure.y][j + figure.x] > 0
                    ):
                        intersection = True
        return intersection

    ## SIMULATION FUNCTION
    def break_linesSym(self, board):
        lines = 0
        if self.use_all_dynamics:
                
            if not self.Vertical_Line_Break_Mode:
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
             
            if self.Vertical_Line_Break_Mode:
                for j in range(self.width):
                    Line_Length = 0
                    Line_Y_Position = 0
                    for i in range(0, self.height):
                        if board[i][j] != 0:
                            Line_Length += 1
                        else:
                            Line_Y_Position = i
                            Line_Length = 0
                        if Line_Length >= 10:
                            board[Line_Y_Position][j] = 0
                            board[Line_Y_Position + 1][j] = 0
                            board[Line_Y_Position + 2][j] = 0
                            board[Line_Y_Position + 3][j] = 0
                            board[Line_Y_Position + 4][j] = 0
                            board[Line_Y_Position + 5][j] = 0
                            Line_Length = 0
                        
        return board
        # This is the base scoring system move or change this to modify how your score updates
        self.update_score(lines**2)

    # Controls for the game
    ## SIMULATION FUNCTION
    def go_downSym(self, board, figure):
        fig = copy.deepcopy(figure)
        brd = copy.deepcopy(board)
        fig.y += 1
        symStopped = False
        if self.intersectsSym(brd, fig):
            fig.y -= 1
            brd = self.freezeSym(brd, fig)
            symStopped = True
        return brd, fig, symStopped

    ## SIMULATION FUNCTION
    def freezeSym(self, board, figure):
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
        if self.intersectsSym(board, fig):
            fig.x = old_x
        return fig

    def rotateSym(self, board, figure):
        fig = copy.deepcopy(figure)
        old_rotation = figure.rotation
        fig.rotate()
        if self.intersectsSym(board, fig):
            fig.rotation = old_rotation

        return fig

    def getFeatures(self, board):
        featsArray = (numpy.zeros(self.NUM_FEATS,)- 1)
        featsArray[self.NUM_HOLES_I] = 0
        featsArray[self.SUM_WELL_I] = 0
        board = numpy.array(board)

        for row in range(self.height + 1):
            for col in range(self.width):
                if board[row][col] > 0:  # FILLED CELL
                    if featsArray[self.COL_HT_START_I + col] == -1:
                        featsArray[self.COL_HT_START_I + col] = row
                    if featsArray[self.MAX_COL_HT_I] == -1:
                        featsArray[self.MAX_COL_HT_I] = row
                else:  # empty cell
                    if featsArray[self.COL_HT_START_I + col] != -1:
                        featsArray[self.NUM_HOLES_I] += 1
        if featsArray[self.MAX_COL_HT_I] == -1:
            featsArray[self.MAX_COL_HT_I] = self.rows

        # get column difference features
        for col in range(self.width - 1):
            featsArray[self.COL_DIFF_START_I + col] = abs(
                featsArray[self.COL_HT_START_I + col]
                - featsArray[self.COL_HT_START_I + col + 1]
            )

        # get well depth features
        for col in range(self.width):
            wellDepth = self.getWellDepth(col, board)
            featsArray[self.SUM_WELL_I] += wellDepth
            if wellDepth > featsArray[self.MAX_WELL_I]:
                featsArray[self.MAX_WELL_I] = wellDepth

        # get squared features and scale them so they're not too big
        for i in range(self.SQUARED_FEATS_START_I):
            featsArray[self.SQUARED_FEATS_START_I + i] = numpy.square(featsArray[i])
            if i <= self.MAX_COL_HT_I or self.SCALE_ALL_SQUARED_FEATS:
                featsArray[self.SQUARED_FEATS_START_I + i] /= self.HT_SQ_SCALE

        return featsArray

    def getWellDepth(self, col, board):
        depth = 0
        for row in range(self.height):
            if board[row][col] > 0:  # encountered a filled space, stop counting
                return depth
            else:
                if (
                    depth > 0
                ):  # if well-depth count has begun, dont require left or right side to be filled
                    depth += 1
                # check if both the cell to the left if full and if the cell to the right is full
                elif (col == 0 or board[row][col - 1] > 0) and (
                    col == self.width - 1 or board[row][col + 1] > 0
                ):
                    depth += 1
        return depth

    def forwardProject(self, board, figure, alist):
        nlist = copy.deepcopy(alist)
        brd   = copy.deepcopy(board)
        fig   = copy.deepcopy(figure)
        x     = fig.x
        y     = fig.y
        r     = fig.rotation

        if self.visitedStates[x,y,r] == 1:
            return
        
        if len(self.finalStates) > 4*self.width*self.height+1:
            return
        for a in [0,1,2,3]:#range(0, 4):
            symStopped = False
            # TAKE ACTION A
            if a == 0:
                nboard, nfigure, symStopped = self.go_downSym(brd, fig)
                nlist.append(a)
            elif a == 1:
                nfigure = self.go_sideSym(1, brd, fig)
                nboard, nfigure, symStopped = self.go_downSym(brd, nfigure)
                nlist.append(a)
                nlist.append(0)
            elif a == 2:
                nfigure = self.go_sideSym(-1, brd, fig)
                nboard, nfigure, symStopped = self.go_downSym(brd, nfigure)
                nlist.append(a)
                nlist.append(0)
            elif a == 3:
                nfigure = self.rotateSym(brd, fig)
                nboard, nfigure, symStopped = self.go_downSym(brd, nfigure)
                nlist.append(a)
                nlist.append(0)

            if symStopped == False:
                self.forwardProject(nboard, nfigure, nlist)
                nlist.pop()
                if a > 0:
                    nlist.pop()
            else:
                match = False
                if self.finalLocations[x,y,r] == 1:
                    match = True
                    
                if match == False:
                    self.finalLocations[x,y,r] = 1
                    self.finalStates.append(copy.deepcopy(nboard))
                    self.actionTree.append(copy.deepcopy(nlist))
                nlist.pop()
                if a > 0:
                    nlist.pop()

            if len(nlist) > 25:
                # print("POPPING OUT")
                return

        self.visitedStates[x,y,r] = 1
        return