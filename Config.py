import json
from pathlib import Path

class Config:
    #const values
    width = 720
    height = 720
    rows = 3
    cols = 3
    size = width//rows
    lineWidth = 15
    lineSize = size//rows
    localLineWidth = 7

    #colors
    bgColor = (255, 255, 255)
    lineColor = (0, 0, 0)