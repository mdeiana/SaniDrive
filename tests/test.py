# hack to import non-installed package
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import src.SaniDrive.SaniDrive as SaniDrive

# Test code goes here I fucking guess
SaniDrive.main()