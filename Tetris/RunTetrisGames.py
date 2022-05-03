import subprocess

# Change this to control how many times the game is run
NumberOfTetrisGames = 5

for Count in range(NumberOfTetrisGames):
    subprocess.Popen("Tetris.py " + str(Count) , shell=True)
