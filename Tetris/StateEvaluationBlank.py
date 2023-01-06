# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 10:31:58 2022

@author: sgordon
"""

## USE THIS CODE IN PLACE OF StateEvaluation if desired

#import pygame
import random
tamer = None

def GameStateEvaluation(game,events):
    
    if game.playAI:
        action_now = random.randint(0,4)
        if action_now == 1:
            game.go_side(1)
        elif action_now == 2:
            game.go_side(-1)
        elif action_now == 3:
            game.rotate()
        else:
            game.go_down() 