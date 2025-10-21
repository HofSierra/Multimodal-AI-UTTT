#todo: dirty rects might need to be implemented to clear the local board and render the winner of a square

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
        #self.squares = np.zeros((ROWS, COLS))
        self.squares = np.zeros((ROWS, COLS, ROWS, COLS))
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

    """def mark_square(self, row, col, player):
        self.squares[row][col] = player
        self.marked_squares += 1"""

    def mark_square(self, global_row, global_col, local_row, local_col, player):
        self.squares[global_row][global_col][local_row][local_col] = player

    def is_local_square_empty(self, global_row, global_col, local_row, local_col):
        return self.squares[global_row][global_col][local_row][local_col] == 0

    def is_board_full(self):
        return self.marked_squares == 9

    def is_board_empty(self):
        return self.marked_squares == 0

    def is_empty_square(self, row, col):
        return self.squares[row][col] == 0

    def get_empty_squares(self):
        empty_squares = []
        for row in range(ROWS):
            for col in range(COLS):
                if self.is_empty_square(row, col):
                    empty_squares.append((row, col))

        return empty_squares

    def reset_board(self):
        self.squares = np.zeros((ROWS, COLS, ROWS, COLS))
        self.marked_squares = 0

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
        self.draw_local_win_fig(row, col)
        self.switch_player()

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

        #logic is still sort of missing so commenting it out
        #local boards
        local_lines_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for row in range(ROWS):
            for col in range(COLS):
                board_x_offset = col * SIZE
                board_y_offset = row * SIZE

                is_allowed = self.allowed_square is None or (row, col) == self.allowed_square
                draw_color = LINE_COLOR if is_allowed else DENIED_SQUARE_LINE_COLOR

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset + LINE_SIZE, board_y_offset),
                                 (board_x_offset + LINE_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset + 2*LINE_SIZE, board_y_offset),
                                 (board_x_offset + 2*LINE_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset, board_y_offset + LINE_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + LINE_SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset, board_y_offset + 2*LINE_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + 2*LINE_SIZE),
                                 LOCAL_LINE_WIDTH)

        screen.blit(local_lines_surface, (0, 0))

    def draw_win(self):
        if self.winner_line_coords is not None:
            initial_pos, end_pos = self.winner_line_coords
            pygame.draw.line(screen, LINE_COLOR, initial_pos, end_pos, CROSS_WIDTH)

    #need to clear the whole board for the hover ui so everything needs to be redrawn
    """def draw_all_again(self):
        for row in range(ROWS):
            for col in range(COLS):
                player = self.board.squares[row][col]
                if player != 0:
                    original_player = self.player
                    self.player = int(player)
                    self.draw_local_win_fig(row, col)
                    self.player = original_player"""

    def draw_all_again(self):
        for global_row in range(ROWS):
            for global_col in range(COLS):
                for local_row in range(ROWS):
                    for local_col in range(COLS):
                        player = self.board.squares[global_row][global_col][local_row][local_col]
                        if player != 0:
                            original_player = self.player
                            self.player = int(player)
                            self.draw_local_fig(global_row, global_col, local_row, local_col)
                            self.player = original_player

    def draw_local_win_fig(self, row, col):
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

    def draw_local_fig(self, global_row, global_col, local_row, local_col):
        local_center_x = global_col * SIZE + local_col * LINE_SIZE + LINE_SIZE // 2
        local_center_y = global_row * SIZE + local_row * LINE_SIZE + LINE_SIZE // 2
        padding = LINE_SIZE * 0.25

        # X-shape
        if self.player == 1:
            x1 = local_center_x - LINE_SIZE // 2 + padding
            x2 = local_center_x + LINE_SIZE // 2 - padding
            y1 = local_center_y - LINE_SIZE // 2 + padding
            y2 = local_center_y + LINE_SIZE // 2 - padding
            local_width = LOCAL_LINE_WIDTH + 2

            # \-shape
            pygame.draw.line(screen, CROSS_COLOR, (x1, y1), (x2, y2), local_width)
            # /-shape
            pygame.draw.line(screen, CROSS_COLOR, (x1, y2), (x2, y1), local_width)

        # O-shape
        elif self.player == 2:
            pygame.draw.circle(screen, CIRCLE_COLOR, (local_center_x, local_center_y),
                               LOCAL_RADIUS, LOCAL_LINE_WIDTH)

    def get_hovered_square(self, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        global_col = mouse_x // SIZE
        global_row = mouse_y // SIZE

        #stay within the defined parameters
        if not (0 <= global_row < ROWS and 0 <= global_col < COLS):
            return None

        return global_row, global_col

    def draw_allowed_square(self):
        if self.allowed_square is None:
            return

        global_row, global_col = self.allowed_square
        x = global_col * SIZE
        y = global_row * SIZE

        surface = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        surface.fill(ALLOWED_SQUARE_COLOR)
        screen.blit(surface, (x, y))

    def is_move_legal(self, global_row, global_col, local_row, local_col):
        if not self.board.is_local_square_empty(global_row, global_col, local_row, local_col):
            return False

        if self.allowed_square is None:
            return True
        else:
            allowed_global_row, allowed_global_col = self.allowed_square
            return (global_row, global_col) == (allowed_global_row, allowed_global_col)

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
        game.draw_allowed_square()
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
                    global_row, global_col = game.hover
                    mouse_x, mouse_y = event.pos
                    local_col = (mouse_x % SIZE) // LINE_SIZE
                    local_row = (mouse_y % SIZE) // LINE_SIZE

                    """if board.is_empty_square(row, col) and game.running:
                        game.play_move(row, col)
                        print(board.squares)

                        winner, line_coords = board.final_state()

                        if winner != 0:
                            game.winner = winner
                            game.winner_line_coords = line_coords
                            game.running = False"""

                    if game.is_move_legal(global_row, global_col, local_row, local_col):
                        board.mark_square(global_row, global_col, local_row, local_col, game.player)
                        game.allowed_square = (local_row, local_col)
                        game.switch_player()
                        print(board.squares)

        pygame.display.update()

main()