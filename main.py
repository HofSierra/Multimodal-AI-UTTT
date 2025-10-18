import sys
import pygame
import numpy as np

from Config import Config

#ref: https://www.youtube.com/watch?v=Bk9hlNZc6sE&t=343s
pygame.init()
screen = pygame.display.set_mode((Config.width, Config.height))
pygame.display.set_caption('Ultimate Tic Tac Toe')
screen.fill(Config.bgColor)

class Board:
    def __init__(self):
        self.squares = np.zeros((Config.rows, Config.cols))

        #debug -> initial state
        print(self.squares)

    def mark_square(self, row, col, player):
        self.squares[row][col] = player

    def if_empty_square(self, row, col):
        return self.squares[row][col] == 0

class Game:
    def __init__(self):
        self.board = Board()
        self.player = 1
        self.show_lines()

    def show_lines(self):

        #global board
        pygame.draw.line(screen, Config.lineColor, (Config.size, 0),
                         (Config.size, Config.height), Config.lineWidth)
        pygame.draw.line(screen, Config.lineColor, (Config.width-Config.size, 0),
                         (Config.width-Config.size, Config.height), Config.lineWidth)

        pygame.draw.line(screen, Config.lineColor, (0, Config.size),
                         (Config.width, Config.size), Config.lineWidth)
        pygame.draw.line(screen, Config.lineColor, (0, Config.height-Config.size),
                         (Config.width, Config.height-Config.size), Config.lineWidth)

        #local boards
        for row in range(Config.rows):
            for col in range(Config.cols):
                board_x_offset = col * Config.size
                board_y_offset = row * Config.size

                pygame.draw.line(screen, Config.lineColor,
                                 (board_x_offset + Config.lineSize, board_y_offset),
                                 (board_x_offset + Config.lineSize, board_y_offset + Config.size),
                                 Config.localLineWidth)

                pygame.draw.line(screen, Config.lineColor,
                                 (board_x_offset + 2*Config.lineSize, board_y_offset),
                                 (board_x_offset + 2*Config.lineSize, board_y_offset + Config.size),
                                 Config.localLineWidth)

                pygame.draw.line(screen, Config.lineColor,
                                 (board_x_offset, board_y_offset + Config.lineSize),
                                 (board_x_offset + Config.size, board_y_offset + Config.lineSize),
                                 Config.localLineWidth)

                pygame.draw.line(screen, Config.lineColor,
                                 (board_x_offset, board_y_offset + 2*Config.lineSize),
                                 (board_x_offset + Config.size, board_y_offset + 2*Config.lineSize),
                                 Config.localLineWidth)


    def switch_player(self):
        self.player = self.player % 2 + 1

def main():
    game = Game()
    board = game.board

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                #x-axis
                col = pos[0] // Config.size
                #y-axis
                row = pos[1] // Config.size

                if board.if_empty_square(row, col):
                    board.mark_square(row, col, game.player)
                    game.switch_player()
                    print(board.squares)

        pygame.display.update()

main()