import subprocess
import re
import platform

# Read config file
config = open("Config.txt", "r")
line = config.readline()
games = int(re.search(r'\d+', line).group())

# Change this to control how many times the game is run
NumberOfTetrisGames = games

for Count in range(NumberOfTetrisGames):
    if  platform.system() == "Windows":
        subprocess.Popen(".\Tetris.py " + str(Count) , shell=True)
    else:
        subprocess.Popen("#!/usr/bin/env python Tetris.py " + str(Count) , shell=True)