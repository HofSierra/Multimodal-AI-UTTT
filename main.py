import sys, os
import pygame
import numpy as np
import copy
import time, json
import random

from TTT_bot import UltimateTTTBot, RandomTTTBot
from config import *

#ref: https://www.youtube.com/watch?v=Bk9hlNZc6sE
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Ultimate Tic Tac Toe')
screen.fill(BG_COLOR)
SCREENSHOT_COUNT = 1

# method to check if local/global board (3x3) has been won by any player
def check_win(grid):

    for i in range(3):

        # Check each row
        if grid[i, 0] == grid[i, 1] == grid[i, 2] != 0:
            return grid[i, 0]

        # Check each column
        if grid[0, i] == grid[1, i] == grid[2, i] != 0:
            return grid[0, i]

    # Check both diagonals
    if (grid[0, 0] == grid[1, 1] == grid[2, 2] != 0) or (grid[2, 0] == grid[1, 1] == grid[0, 2] != 0):
        return grid[1, 1]

    # Draw
    if np.all(grid != 0):
        return -1

    # Ongoing
    return 0

def get_hovered_square(mouse_pos):
    mouse_x, mouse_y = mouse_pos
    global_col = mouse_x // SIZE
    global_row = mouse_y // SIZE

    #stay within the defined parameters
    if not (0 <= global_row < ROWS and 0 <= global_col < COLS):
        return None

    return global_row, global_col

def set_game_mode(key, are_bots_enabled):
    if key == pygame.K_0:
        are_bots_enabled[1] = True
        are_bots_enabled[2] = True
        mode_name = "Bot vs Bot"

    elif key == pygame.K_1:
        are_bots_enabled[1] = False # Human
        are_bots_enabled[2] = True
        mode_name = "Human vs Bot"

    elif key == pygame.K_2:
        are_bots_enabled[1] = True
        are_bots_enabled[2] = False # Human
        mode_name = "Bot vs Human"

    elif key == pygame.K_3:
        are_bots_enabled[1] = False
        are_bots_enabled[2] = False
        mode_name = "Human vs Human"
    else:
        return

    # game.reset()
    print(f"\nNew Mode: {mode_name}")
    return True

def bot_play(game, board, bots, is_bot_turn, current_player):
    if game.running and is_bot_turn:
        current_bot = bots[current_player]
        game_copy = game.copy()
        bot_move = current_bot.get_bot_move(game_copy)
        if isinstance(current_bot, UltimateTTTBot):
             take_screenshots(screen, game, current_player, bot_move)
        board.mark_square(bot_move[0], bot_move[1], bot_move[2], bot_move[3], game.player)
        global_row, global_col = bot_move[0], bot_move[1]
        local_row, local_col = bot_move[2], bot_move[3]
        board.global_squares[global_row, global_col] = check_win(board.squares[global_row, global_col])

        # win check
        global_winner, line_coords = board.final_global_state()
        if global_winner != 0:
            game.winner = global_winner
            game.winner_line_coords = line_coords
            game.running = False

        # free play
        next_g_row, next_g_col = local_row, local_col
        if board.global_squares[next_g_row, next_g_col] != 0:
            game.allowed_square = None
        else:
            game.allowed_square = (next_g_row, next_g_col)

        game.switch_player()
        print(board.global_squares)

def human_play(game, board, are_bots_enabled, event):
    if game.running and not are_bots_enabled[game.player] and game.hover is not None:
        global_row, global_col = game.hover
        mouse_x, mouse_y = event.pos
        local_col = (mouse_x % SIZE) // LOCAL_SIZE
        local_row = (mouse_y % SIZE) // LOCAL_SIZE

        if game.is_move_legal(global_row, global_col, local_row, local_col) and game.running:
            board.mark_square(global_row, global_col, local_row, local_col, game.player)
            board.global_squares[global_row, global_col] = check_win(board.squares[global_row, global_col])

            # win check
            global_winner, line_coords = board.final_global_state()
            if global_winner != 0:
                game.winner = global_winner
                game.winner_line_coords = line_coords
                game.running = False

            # free play
            next_g_row, next_g_col = local_row, local_col
            if board.global_squares[next_g_row, next_g_col] != 0:
                game.allowed_square = None
            else:
                game.allowed_square = (next_g_row, next_g_col)

            game.switch_player()
            print(board.global_squares)

def game_shortcuts(event, game, are_bots_enabled):
    if event.type == pygame.KEYDOWN:
        set_game_mode(event.key, are_bots_enabled)
        if event.key == pygame.K_r:
            print("Reset game")
            game.reset()
        if event.key == pygame.K_q:
            print("Quit pygame")
            pygame.quit()
            sys.exit()

def take_screenshots(screen, game, player, bot_move):
    global SCREENSHOT_COUNT
    filename = os.path.join(IMAGES_FOLDER, f"image_{SCREENSHOT_COUNT}.png")
    pygame.image.save(screen, filename)
    log_bot_move(game, player, filename, bot_move)
    print(f"Screenshot saved to {filename}")
    SCREENSHOT_COUNT += 1
    return time.time(), SCREENSHOT_COUNT

def log_bot_move(game, player, filename, bot_move):
    g_row, g_col, l_row, l_col = bot_move

    legal_moves = game.get_legal_moves()
    annotated_legal_moves = []

    global_state_log = []
    for gr in range(ROWS):
        for gc in range(COLS):
            for lr in range(ROWS):
                for lc in range(COLS):
                    l_player = game.board.squares[gr][gc][lr][lc]
                    global_state = {
                        "global_row": gr,
                        "global_col": gc,
                        "local_row": lr,
                        "local_col": lc,
                        "player": int(l_player),
                    }
                    global_state_log.append(global_state)

    for move in legal_moves:
        gr, gc, lr, lc = move
        annotated_move = {
            "global_row": gr,
            "global_col": gc,
            "local_row": lr,
            "local_col": lc,
        }
        annotated_legal_moves.append(annotated_move)

    log = {
        "player": player,
        "image path": filename,
        "legal moves": annotated_legal_moves,
        "allowed squares": game.allowed_square,
        "global state": global_state_log,
        "best move": {
            "global_row": g_row,
            "global_col": g_col,
            "local_row": l_row,
            "local_col": l_col
        },
        "chain of thought": "",
    }

    try:
        with open(LOG_FILE_PATH, "a") as f:
            json.dump(log, f)
            f.write("\n")
        print(f"Log for Player_{player} saved to {LOG_FILE_PATH} with move: {bot_move}")
    except Exception as e:
        print(e)

class Board:
    def __init__(self):
        self.squares = np.zeros((ROWS, COLS, ROWS, COLS))
        self.global_squares = np.zeros((ROWS, COLS))
        self.empty_squares = self.squares

    def final_global_state(self):
        # vertical wins
        for col in range(COLS):
            if self.global_squares[0][col] == self.global_squares[1][col] == self.global_squares[2][col] != 0:
                winner = self.global_squares[0][col]
                x = col * SIZE + SIZE // 2
                initial_pos = (x, 20)
                end_pos = (x, HEIGHT - 20)
                line_coords = (initial_pos, end_pos)
                return winner, line_coords

        # horizontal wins
        for row in range(ROWS):
            if self.global_squares[row][0] == self.global_squares[row][1] == self.global_squares[row][2] != 0:
                winner = self.global_squares[row][0]
                y = row * SIZE + SIZE // 2
                initial_pos = (20, y)
                end_pos = (WIDTH - 20, y)
                line_coords = (initial_pos, end_pos)
                return winner, line_coords

        # diagonal wins
        if self.global_squares[0][0] == self.global_squares[1][1] == self.global_squares[2][2] != 0:
            winner = self.global_squares[1][1]
            initial_pos = (20, 20)
            end_pos = (WIDTH - 20, HEIGHT - 20)
            line_coords = (initial_pos, end_pos)
            return winner, line_coords
        if self.global_squares[2][0] == self.global_squares[1][1] == self.global_squares[0][2] != 0:
            winner = self.global_squares[1][1]
            initial_pos = (20, HEIGHT - 20)
            end_pos = (WIDTH - 20, 20)
            line_coords = (initial_pos, end_pos)
            return winner, line_coords

        return 0, None

    def mark_square(self, global_row, global_col, local_row, local_col, player):
        self.squares[global_row][global_col][local_row][local_col] = player

    def is_local_square_empty(self, global_row, global_col, local_row, local_col):
        return self.squares[global_row][global_col][local_row][local_col] == 0

    def reset(self):
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

        #local boards
        local_lines_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for row in range(ROWS):
            for col in range(COLS):
                local_winner = self.board.global_squares[row][col]
                if local_winner != -1 and local_winner != 0:
                     continue

                board_x_offset = col * SIZE
                board_y_offset = row * SIZE

                is_allowed = self.allowed_square is None or (row, col) == self.allowed_square
                draw_color = LINE_COLOR if is_allowed else DENIED_BOARD_LINE_COLOR

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset + LOCAL_SIZE, board_y_offset),
                                 (board_x_offset + LOCAL_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset + 2 * LOCAL_SIZE, board_y_offset),
                                 (board_x_offset + 2 * LOCAL_SIZE, board_y_offset + SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset, board_y_offset + LOCAL_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + LOCAL_SIZE),
                                 LOCAL_LINE_WIDTH)

                pygame.draw.line(local_lines_surface, draw_color,
                                 (board_x_offset, board_y_offset + 2 * LOCAL_SIZE),
                                 (board_x_offset + SIZE, board_y_offset + 2 * LOCAL_SIZE),
                                 LOCAL_LINE_WIDTH)

        screen.blit(local_lines_surface, (0, 0))

    def draw_win(self):
        if self.winner_line_coords is not None:
            initial_pos, end_pos = self.winner_line_coords
            pygame.draw.line(screen, WIN_LINE_COLOR, initial_pos, end_pos, CROSS_WIDTH)

    #need to clear the whole board for the hover ui so everything needs to be redrawn
    def draw_all_again(self):
        for global_row in range(ROWS):
            for global_col in range(COLS):
                local_winner = self.board.global_squares[global_row, global_col]
                if local_winner == -1 or local_winner == 0:
                    for local_row in range(ROWS):
                        for local_col in range(COLS):
                            player = self.board.squares[global_row][global_col][local_row][local_col]
                            if player != 0:
                                original_player = self.player
                                self.player = int(player)
                                self.draw_local_fig(global_row, global_col, local_row, local_col)
                                self.player = original_player
                if local_winner in [1, 2]:
                    original_player = self.player
                    self.player = int(local_winner)
                    self.draw_global_fig(global_row, global_col)
                    self.player = original_player

    # function to draw X or O on global board, when a local board has been won
    def draw_global_fig(self, row, col):
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

    # function to draw X or O on local boards
    def draw_local_fig(self, global_row, global_col, local_row, local_col):
        local_center_x = global_col * SIZE + local_col * LOCAL_SIZE + LOCAL_SIZE // 2
        local_center_y = global_row * SIZE + local_row * LOCAL_SIZE + LOCAL_SIZE // 2
        padding = LOCAL_SIZE * 0.25

        # X-shape
        if self.player == 1:
            x1 = local_center_x - LOCAL_SIZE // 2 + padding
            x2 = local_center_x + LOCAL_SIZE // 2 - padding
            y1 = local_center_y - LOCAL_SIZE // 2 + padding
            y2 = local_center_y + LOCAL_SIZE // 2 - padding
            local_width = LOCAL_LINE_WIDTH + 2

            # \-shape
            pygame.draw.line(screen, CROSS_COLOR, (x1, y1), (x2, y2), local_width)
            # /-shape
            pygame.draw.line(screen, CROSS_COLOR, (x1, y2), (x2, y1), local_width)

        # O-shape
        elif self.player == 2:
            pygame.draw.circle(screen, CIRCLE_COLOR, (local_center_x, local_center_y),
                               LOCAL_RADIUS, LOCAL_LINE_WIDTH)

    def draw_allowed_square(self):
        if self.allowed_square is None:
            return

        global_row, global_col = self.allowed_square
        x = global_col * SIZE
        y = global_row * SIZE

        surface = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        surface.fill(ALLOWED_BOARD_COLOR)
        if self.running:
            screen.blit(surface, (x, y))

    def copy(self):
        return copy.deepcopy(self)

    def is_move_legal(self, global_row, global_col, local_row, local_col):
        if not self.board.is_local_square_empty(global_row, global_col, local_row, local_col):
            return False

        if self.allowed_square is None:
            if self.board.global_squares[global_row, global_col]!=0:
                return False
            return True
        else:
            allowed_global_row, allowed_global_col = self.allowed_square
            return (global_row, global_col) == (allowed_global_row, allowed_global_col)

    def get_legal_moves(self) -> list[tuple[int, int, int, int]]:
        legal_moves = []
        if self.allowed_square is not None:
            # Play in a specific local board
            g_row, g_col = self.allowed_square
            for row in range(ROWS):
                for col in range(COLS):
                    if self.is_move_legal(g_row, g_col, row, col):
                        legal_moves.append((g_row, g_col, row, col))
        else:
            # Play anywhere
            for g_row in range(ROWS):
                for g_col in range(COLS):
                    for row in range(ROWS):
                        for col in range(COLS):
                            if self.is_move_legal(g_row, g_col, row, col):
                                legal_moves.append((g_row, g_col, row, col))

        return legal_moves

    def is_game_over(self):
        if check_win(self.board.global_squares) == 1 or check_win(self.board.global_squares) == 2:
            return True
        return False

    def get_winner(self):
        return check_win(self.board.global_squares)

    def get_board(self):
        return self.board.global_squares

    """
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
    """

    def switch_player(self):
        self.player = self.player % 2 + 1

    def reset(self):
        self.board.reset()
        self.player = 1
        self.hover = None
        self.allowed_square = None
        self.running = True
        self.winner = 0
        self.winner_line_coords = None

def main():
    game = Game()
    board = game.board
    player_1 = RandomTTTBot(1) # X
    player_2 = UltimateTTTBot(2) # O
    bots = {1: player_1, 2: player_2}
    are_bots_enabled = {1: False, 2: False}

    while True:
        screen.fill(BG_COLOR)
        game.draw_allowed_square()
        game.show_lines()
        game.draw_all_again()
        game.draw_win()

        current_player = game.player
        is_bot_turn = are_bots_enabled[current_player]

        # bot logic needs to run every frame and not wait for input
        bot_play(game, board, bots, is_bot_turn, current_player)

        if not game.running:
            screen.fill(BG_COLOR)
            game.draw_allowed_square()
            game.show_lines()
            game.draw_all_again()
            game.draw_win()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                pos = event.pos
                game.hover = get_hovered_square(pos)

            game_shortcuts(event, game, are_bots_enabled)

            if event.type == pygame.MOUSEBUTTONDOWN:
                human_play(game, board, are_bots_enabled, event)

        pygame.display.update()

        if not game.running and are_bots_enabled[1] and are_bots_enabled[2]:
            print("Game Over")
            end_time = time.time() + 10
            while time.time() < end_time:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        game_shortcuts(event, game, are_bots_enabled)
            if bots[1] == player_1 and bots[2] == player_2:
                bots[1] = player_2
                bots[2] = player_1
                print("Switch bots")
            else:
                bots[1] = player_1
                bots[2] = player_2
                print("Switch bots")
            game.reset()
            print("Resetting game")

main()