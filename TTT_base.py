import sys
import pygame
import numpy as np

from config import *

#ref: https://www.youtube.com/watch?v=Bk9hlNZc6sE
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
screen.fill(BG_COLOR)

class Board:
    def __init__(self):
        self.squares = np.zeros((ROWS, COLS))
        self.empty_squares = self.squares
        self.marked_squares = 0

        #debug -> initial state
        print(self.squares)

    def final_state(self):
        #vertical wins
        for col in range(COLS):
            if self.squares[0][col] == self.squares[1][col] == self.squares[2][col] != 0:
                winner = self.squares[0][col]
                x = col * SIZE + SIZE // 2
                initial_pos = (x, 20)
                end_pos = (x, HEIGHT - 20)
                line_coords = (initial_pos, end_pos)
                return winner, line_coords

        #horizontal wins
        for row in range(ROWS):
            if self.squares[row][0] == self.squares[row][1] == self.squares[row][2] != 0:
                winner = self.squares[row][0]
                y = row * SIZE + SIZE // 2
                initial_pos = (20, y)
                end_pos = (WIDTH - 20, y)
                line_coords = (initial_pos, end_pos)
                #pygame.draw.line(screen, LINE_COLOR, initial_pos, end_pos, LINE_WIDTH)
                return winner, line_coords

        #diagonal wins
        if self.squares[0][0] == self.squares[1][1] == self.squares[2][2] != 0:
            winner = self.squares[1][1]
            initial_pos = (20, 20)
            end_pos = (WIDTH - 20, HEIGHT - 20)
            line_coords = (initial_pos, end_pos)
            return winner, line_coords
        if self.squares[2][0] == self.squares[1][1] == self.squares[0][2] != 0:
            winner = self.squares[1][1]
            initial_pos = (20, HEIGHT - 20)
            end_pos = (WIDTH - 20, 20)
            line_coords = (initial_pos, end_pos)
            return winner, line_coords

        return 0, None

    def mark_square(self, row, col, player):
        self.squares[row][col] = player
        self.marked_squares += 1

    def is_board_full(self):
        return self.marked_squares == 9

    def is_board_empty(self):
        return self.marked_squares == 0

    def is_empty_square(self, row, col):
        return self.squares[row][col] == 0

    def reset_board(self):
        self.__init__()

class Game:
    def __init__(self):
        self.board = Board()
        self.player = 1
        self.hover = None
        self.allowed_square = None
        self.running = True
        self.winner = 0
        self.winner_line_coords = None
        self.show_lines()

    def play_move(self, row, col):
        self.board.mark_square(row, col, self.player)
        self.draw_fig(row, col)
        self.switch_player()

    @staticmethod
    def show_lines():

        #board
        pygame.draw.line(screen, LINE_COLOR, (SIZE, 0),
                         (SIZE, HEIGHT), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (WIDTH-SIZE, 0),
                         (WIDTH-SIZE, HEIGHT), LINE_WIDTH)

        pygame.draw.line(screen, LINE_COLOR, (0, SIZE),
                         (WIDTH, SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (0, HEIGHT-SIZE),
                         (WIDTH, HEIGHT-SIZE), LINE_WIDTH)

    def draw_win(self):
        if self.winner_line_coords is not None:
            initial_pos, end_pos = self.winner_line_coords
            pygame.draw.line(screen, LINE_COLOR, initial_pos, end_pos, CROSS_WIDTH)

    #need to clear the whole board for the hover ui so everything needs to be redrawn
    def draw_all_again(self):
        for row in range(ROWS):
            for col in range(COLS):
                player = self.board.squares[row][col]
                if player != 0:
                    original_player = self.player
                    self.player = int(player)
                    self.draw_fig(row, col)
                    self.player = original_player

    def draw_fig(self, row, col):
        #X-shape
        if self.player == 1:
            #\-shape
            left_start_pos = (col * SIZE + 60, row * SIZE + 60)
            left_end_pos = (col * SIZE + SIZE - 60, row * SIZE + SIZE - 60)
            pygame.draw.line(screen, CROSS_COLOR, left_start_pos, left_end_pos, CROSS_WIDTH)

            #/-shape
            right_start_pos = (col * SIZE + 60, row * SIZE + SIZE - 60)
            right_end_pos = (col * SIZE + SIZE - 60, row * SIZE + 60)
            pygame.draw.line(screen, CROSS_COLOR, right_start_pos, right_end_pos, CROSS_WIDTH)
        #O-shape
        elif self.player == 2:
            center = (col*SIZE + SIZE//2, row*SIZE + SIZE//2)
            pygame.draw.circle(screen, CIRCLE_COLOR, center, RADIUS, LINE_WIDTH)

    @staticmethod
    def get_hovered_square(mouse_pos):
        mouse_x, mouse_y = mouse_pos
        global_col = mouse_x // SIZE
        global_row = mouse_y // SIZE

        #stay within the defined parameters
        if not (0 <= global_row < ROWS and 0 <= global_col < COLS):
            return None

        return global_row, global_col

    def draw_hover(self):
        if self.hover is None:
            return

        global_row, global_col = self.hover

        hover_dim = SIZE

        x = (global_col * SIZE)
        y = (global_row * SIZE)

        surface = pygame.Surface((hover_dim, hover_dim), pygame.SRCALPHA)
        surface.fill(HOVER_COLOR)

        screen.blit(surface, (x, y))

    def switch_player(self):
        self.player = self.player % 2 + 1

    def reset_game(self):
        self.board.reset_board()
        self.player = 1
        self.hover = None
        self.allowed_square = None
        self.running = True
        self.winner = 0
        self.winner_line_coords = None

def main():
    game = Game()
    board = game.board

    while True:
        screen.fill(BG_COLOR)
        game.draw_hover()
        game.show_lines()
        game.draw_all_again()
        game.draw_win()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                pos = event.pos
                game.hover = game.get_hovered_square(pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_game()
                    print("Reset game")

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.hover is not None:
                    row, col = game.hover

                    if board.is_empty_square(row, col) and game.running:
                        game.play_move(row, col)
                        print(board.squares)

                        winner, line_coords = board.final_state()

                        if winner != 0:
                            game.winner = winner
                            game.winner_line_coords = line_coords
                            game.running = False

        pygame.display.update()

main()