import sys
import pygame
import numpy as np

from config import *

#ref: https://www.youtube.com/watch?v=Bk9hlNZc6sE&t=343s
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Ultimate Tic Tac Toe')
screen.fill(BG_COLOR)

class Board:
    def __init__(self):
        self.squares = np.zeros((ROWS, COLS))
        self.empty_squares = self.squares
        self.marked_squares = 0

        #debug -> initial state
        print(self.squares)

    def mark_square(self, row, col, player):
        self.squares[row][col] = player
        self.marked_squares += 1

    def is_board_full(self):
        return self.marked_squares == 9

    def is_board_empty(self):
        return self.marked_squares == 0

    def if_empty_square(self, row, col):
        return self.squares[row][col] == 0

    def get_empty_squares(self):
        empty_squares = []
        for row in range(ROWS):
            for col in range(COLS):
                if self.if_empty_square(row, col):
                    empty_squares.append((row, col))

        return empty_squares

class Game:
    def __init__(self):
        self.board = Board()
        self.player = 1
        self.show_lines()

    def show_lines(self):

        #global board
        pygame.draw.line(screen, LINE_COLOR, (SIZE, 0),
                         (SIZE, HEIGHT), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (WIDTH-SIZE, 0),
                         (WIDTH-SIZE, HEIGHT), LINE_WIDTH)

        pygame.draw.line(screen, LINE_COLOR, (0, SIZE),
                         (WIDTH, SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (0, HEIGHT-SIZE),
                         (WIDTH, HEIGHT-SIZE), LINE_WIDTH)

        #logic is missing so commenting it out
        """#local boards
        for row in range(ROWS):
            for col in range(COLS):
                board_x_offset = col * SIZE
                board_y_offset = row * SIZE

                pygame.draw.line(screen, LINE_COLOR,
                                 (board_x_offset + LINE_SIZE, board_y_offset),
                                 (board_x_offset + LINE_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(screen, LINE_COLOR,
                                 (board_x_offset + 2*LINE_SIZE, board_y_offset),
                                 (board_x_offset + 2*LINE_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(screen, LINE_COLOR,
                                 (board_x_offset, board_y_offset + LINE_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + LINE_SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(screen, LINE_COLOR,
                                 (board_x_offset, board_y_offset + 2*LINE_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + 2*LINE_SIZE),
                                 LOCAL_LINE_WIDTH)"""

    def draw_fig(self, row, col):
        #X-shape
        if self.player == 1:
            #\-shape
            left_start_pos = (col * SIZE + 60, row * SIZE + 60)
            left_end_pos = (col * SIZE + SIZE - 60, row * SIZE + SIZE - 60)
            pygame.draw.line(screen, LINE_COLOR, left_start_pos, left_end_pos, SQUARE_SIZE)

            #/-shape
            right_start_pos = (col * SIZE + 60, row * SIZE + SIZE - 60)
            right_end_pos = (col * SIZE + SIZE - 60, row * SIZE + 60)
            pygame.draw.line(screen, LINE_COLOR, right_start_pos, right_end_pos, SQUARE_SIZE)
        #O-shape
        elif self.player == 2:
            center = (col*SIZE + SIZE//2, row*SIZE + SIZE//2)
            pygame.draw.circle(screen, LINE_COLOR, center, RADIUS, LINE_WIDTH)

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
                col = pos[0] // SIZE
                #y-axis
                row = pos[1] // SIZE

                if board.if_empty_square(row, col):
                    board.mark_square(row, col, game.player)
                    game.draw_fig(row,col)
                    game.switch_player()
                    print(board.squares)

        pygame.display.update()

main()