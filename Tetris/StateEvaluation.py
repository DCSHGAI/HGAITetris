import os
import csv
import numpy
import copy
import pygame
import TetrisSym as ts
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input

class Tamer2:
    def __init__(self):
        self.compiled  = False
        self.model     = None
        self.runRandom = False
        
        self.compileModel()
        
        self.record       = []
        self.arecord      = []
        self.frecord      = []
        self.load_record  = []
        self.load_frecord = []
        
        self.actLoc                 = 0
        self.coa                    = []
        self.state_state_feats      = None
        self.prev_state_state_feats = None
        self.prev_action            = 0
        self.action                 = 0
        self.playAI                 = False

    #COMPILE BASIC MODEL
    def compileModel(self, optimizer=None, learning_rate=0.001, metrics=[]):
        # construct generic model if one is not specified
        # initializer = tf.keras.initializers.Zeros()
        if self.model == None:
            input_shape = 46
            input1      = Input(shape=(input_shape,))
            x1          = Dense(1, kernel_initializer="zeros", bias_initializer="zeros")(input1)
            inputs      = [input1]

            self.model  = Model(inputs, outputs=[x1])  # ,y2,y3])

        # compile the model
        if optimizer == None:
            self.model.compile(
                optimizer=tf.keras.optimizers.SGD(lr=0.000005 / 47.0), loss="mse"
            )
        else:
            self.model.compile(optimizer=optimizer, loss="mse")
        self.compiled = True

    #LOAD PREVIOUS WEIGHTS FILE
    def load_weights(self, filepath):
        if self.compiled == True:
            self.model.load_weights(filepath)

    #SAVE WEIGHTS FILE
    def save_weights(self, filepath):
        if self.compiled == True:
            self.model.save_weights(filepath)

    #FORWARD PROJECT FROM SET OF STATE FEATURE VECTORS TO PREDICT REWARDS & BEST ACTION
    def forward(self, state_state_feats):
        action = numpy.random.randint(0, len(state_state_feats))
        ssfeats = numpy.zeros([len(state_state_feats), 46])
        for s in range(len(state_state_feats)):
            for f in range(46):
                ssfeats[s, f] = state_state_feats[s][f]
        pred_rewards = numpy.zeros(len(state_state_feats))

        rid = numpy.random.randint(0, 10)

        if rid >= 8 and self.runRandom:
            action = numpy.random.randint(0, len(state_state_feats))
        else:
            if self.compiled == True:
                pred_rewards = self.model.predict(ssfeats, verbose=0)
                action = numpy.argmax(pred_rewards)
            else:
                action = numpy.random.randint(0, len(state_state_feats))

        return action, pred_rewards

    #BACKPROJECT REWARD (I.E. FEEDBACK) TO UPDATE MODEL
    def backward(self, prev_state_state_feats, prev_action, human_reward):
        self.record.append(prev_state_state_feats)
        self.arecord.append(prev_action)
        self.frecord.append(human_reward)
        # do a gradient update step
        if (
            human_reward != 0
            and prev_state_state_feats is not None
            and prev_action is not None
            and self.compiled == True
        ):
            x = numpy.reshape(
                prev_state_state_feats[prev_action],
                (1, len(prev_state_state_feats[prev_action])),
            ).astype("float32")
            y = numpy.reshape(numpy.array(human_reward, dtype="float32"), (1))
            self.model.fit(x, y, verbose=0)

    #BATCH OVER ALL PREVIOUS INSTANCES
    def batch_backward(self):
        if len(self.record) > 0:
            ssfeats = numpy.zeros([len(self.record), 46])
            yvalue = numpy.zeros([len(self.frecord)])
            for s in range(len(self.record)):
                tmp       = self.record[s]
                feat      = tmp[self.arecord[s]]
                yvalue[s] = self.frecord[s]
                for f in range(46):
                    ssfeats[s, f] = feat[f]
            self.model.fit(ssfeats, yvalue, verbose=0)

    #BACKPROJECT OVER ALL LOADED INSTANCES
    def all_backward(self):
        ssfeats = numpy.zeros([len(self.load_record), 46])
        yvalue  = numpy.zeros([len(self.load_frecord)])
        for s in range(len(self.load_record)):
            tmp       = self.load_record[s]
            yvalue[s] = self.load_frecord[s]
            for f in range(46):
                ssfeats[s, f] = tmp[f]
        self.model.fit(ssfeats, yvalue, verbose=0)
    
    #LOAD DATA FROM ANOTHER RUN
    def load_data(self, filepath):
        # LOOP ALL TEXTFILES (.CSV) IN DIRECTORY
        testFiles = os.listdir(filepath)
        self.load_record  = []
        self.load_frecord = []
        for t in range(len(testFiles)):
            with open(filepath + testFiles[t], mode="r") as csv_file:
                csv_reader = csv.reader(csv_file)
                ndata = list(csv_reader)
                for s in range(len(ndata)):
                    row = ndata[s]
                    self.load_record.append(copy.deepcopy(row[0 : (len(row) - 1)]))
                    self.load_frecord.append(copy.deepcopy(row[-1]))
        self.all_backward()

    #SAVE DATA FROM ANOTHER RUN
    def save_data(self, filename):
        ssfeats = numpy.zeros([len(self.record), 46])
        yvalue  = numpy.zeros([len(self.frecord)])
        for s in range(len(self.record)):
            tmp       = self.record[s]
            feat      = tmp[self.arecord[s]]
            yvalue[s] = self.frecord[s]
            for f in range(46):
                ssfeats[s, f] = feat[f]
        textfile = open(filename, "w")
        for s in range(len(self.record)):
            for f in range(46):
                textfile.write(str(ssfeats[s, f]) + ",")
            textfile.write(str(yvalue[s]) + "\n")
        textfile.close()

checkPointPath = "tamer.hdf5"
tamer          = Tamer2()
#tamer.load_weights(checkPointPath)

gameSym = ts.TetrisSym(20,10)

def GameStateEvaluation(game,events):
    # GameState gives you access to the entire Tetris class and includes the field and all controls
    
    #LOOP OVER INPUT EVENTS - INSERT YOUR OWN CONTROLS HERE
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                #SAVE WEIGHTS & DATA
                tamer.save_weights("model\\tamer" + str(game.gameid) + ".hdf5")
                tamer.save_data("data\\dataRun" + str(game.gameid) + ".csv")
            
            if event.key == pygame.K_l:
                #LOAD DATA & BATCH TRAIN
                tamer.load_data("data\\")
            
            if event.key == pygame.K_b:
                #BATCH DATA
                tamer.batch_backward()
                
    if game.playAI:
        # IF GAME FEEDBACK --> UPDATE MODEL (I.E. LEARN)
        if game.feedback != 0:
            tamer.backward(tamer.prev_state_state_feats,tamer.prev_action,game.feedback)
            game.feedback = 0
            
        #IF NEW FIGURE APPEARED, OR AI ENABLED, OR YOU DON'T KNOW WHAT TO DO NEXT... PLAN AN ACTION SEQUENCE (COA)
        if game.newFig == 1 or tamer.playAI == False or len(tamer.coa)==0:
            #UPDATE PREVIOUS STATE (FOR LEARNING)
            tamer.prev_state_state_feats = copy.deepcopy(tamer.state_state_feats)
            tamer.prev_action            = copy.deepcopy(tamer.action)
            
            #INDICATE AI IS NOW "ON"
            tamer.playAI = True            
            
            #FORWARD PROJECT OF PIECES
            gameSym.finalStates    = []
            gameSym.actionTree     = []
            #BOOKKEEPING VARIABLES
            gameSym.visitedStates  = numpy.zeros([10,20,4])
            gameSym.finalLocations = numpy.zeros([10,20,4])
            #GET THE STATE OF THE GAME & FIGURE
            field  = copy.deepcopy(game.field)
            figure = copy.deepcopy(game.figure)
            #FORWARD PROJECT ALL FUTURE, POSSIBLE POSITIONS FOR THE PIECE
            gameSym.forwardProject(field, figure, [])

            #COMPUTE STARTING STATE
            board = [[0 for x in range(10)] for y in range(20)]
            board += [[1 for x in range(10)]]
            for i in range(10):
                for j in range(20):
                    board[j][i] = game.field[j][i]

            state0_feat = gameSym.getFeatures(board)

            #COMPUTE DIFFERENCES BETWEEN FINAL STATES AND STARTING STATE
            state1_feats = []
            for piecePlacement in gameSym.finalStates:
                board = [[0 for x in range(10)] for y in range(20)]
                board += [[1 for x in range(10)]]
                for i in range(10):
                    for j in range(20):
                        board[j][i] = piecePlacement[j][i]
                state1_feats.append(gameSym.getFeatures(board))

            #GET STATE FEATURE VECTORS
            state_state_feats = []
            for state1_feat in state1_feats:
                state_state_feats.append(state1_feat - state0_feat)

            #GET BEST ACTION & ACTION SETS
            action, actionSet = tamer.forward(state_state_feats)

            actionTree = copy.deepcopy(gameSym.actionTree)

            tamer.state_state_feats = state_state_feats
            tamer.action            = action
            
            #SET COA
            tamer.coa = []
            if action < len(actionTree):
                tamer.coa = actionTree[action]
                
            tamer.actLoc = 0
            
            ## DONE PLANNING

        #IF AI IS PLAYING AND THERE IS A PLAN (COA) IN PLACE, EXECUTE NEXT ACTION
        if tamer.actLoc < len(tamer.coa):
            action_now   = tamer.coa[tamer.actLoc]
            tamer.actLoc += 1
            if action_now == 1:
                game.go_side(1)
            elif action_now == 2:
                game.go_side(-1)
            elif action_now == 3:
                game.rotate()
            else:
                game.go_down()
        else:
            game.go_down()        