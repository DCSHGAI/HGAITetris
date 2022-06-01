import subprocess
import re

# Read config file
config = open("Config.txt", "r")
line = config.readline()
games = int(re.search(r'\d+', line).group())

# Change this to control how many times the game is run
NumberOfTetrisGames = games

for Count in range(NumberOfTetrisGames):
    subprocess.Popen("Tetris.py " + str(Count) , shell=True)
