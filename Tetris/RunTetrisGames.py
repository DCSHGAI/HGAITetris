import subprocess

# Change this to control how many times the game is run
NumberOfTetrisGames = 1

for Count in range(NumberOfTetrisGames):
    subprocess.Popen("Tetris.py", shell=True)

# TODO: Create game state to feed to AI function so custom moves can be implemented


