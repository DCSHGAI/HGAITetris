import subprocess
import re
import platform

def StartGames():
    # Read config file
    config = open("Config.txt", "r")
    lines = config.readlines()
    games = int(re.search(r'\d+', lines[1]).group())

    # Change this to control how many times the game is run
    NumberOfTetrisGames = games

    for Count in range(NumberOfTetrisGames):
        if  platform.system() == "Windows":
            subprocess.Popen(".\Tetris.cpython-39.pyc " + str(Count) , shell=True)
        else:
            subprocess.Popen("#!/usr/bin/env python Tetris.cpython-39.pyc " + str(Count) , shell=True)