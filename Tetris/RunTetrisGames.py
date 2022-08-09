import subprocess
import re
import time
import platform


def StartGames():
    # Read config file
    config = open("Config.txt", "r")
    lines = config.readlines()
    games = int(re.search(r'\d+', lines[1]).group())

    # Change this to control how many times the game is run
    NumberOfTetrisGames = 8

    for Count in range(NumberOfTetrisGames):
        if  platform.system() == "Windows":
            print("The program has detected that you are running Windows and will run the appropriate command to spool up Tetris games.")
            time.sleep(1)
            subprocess.Popen(".\Tetris.py " + str(Count) , shell=True)
        else:
            print("The program has detected that you are running Linux or Mac and will run the appropriate command to spool up Tetris games.")
            time.sleep(1)
            subprocess.Popen("#!/usr/bin/env python Tetris.cpython-39.pyc " + str(Count) , shell=True)

#StartGames()