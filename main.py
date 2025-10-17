import sys
import pygame
from Config import Config

pygame.init()
screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
pygame.display.set_caption('Ultimate Tic Tac Toe')