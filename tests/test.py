import sys
import os
import os.path as path

# hack to import non-installed package
root = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(root)
from src.sanidrive import SaniDrive

# modify working directory for consistent relative paths
os.chdir(root)

# modify sys.argv to simulate passing of arguments from shell
sys.argv = ['SaniDrive.py', '--file', 'data/credenziali.json', 
            #'--visible',
            '--log', 'tests/logs.txt',
            '--driver', 'driver/chromedriver.exe']

# test code
SaniDrive.main()