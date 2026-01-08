#Ultimate Version
import math
import numpy as np
from PIL import Image
import random, time, requests, io, base64, pygame
from config import *

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

class RandomTTTBot:
    def __init__(self, player):
        self.player = player

    def get_bot_move (self, game):
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return None
        return random.choice(legal_moves)

class VLMBot:
    def __init__(self, screen, player):
        self.player = player
        self.screen = screen
        self.api_url = "https://vernetta-superspiritual-sorrily.ngrok-free.dev/predict_move"

    def get_bot_move(self, game):

        image_data = pygame.image.tostring(self.screen, "RGB")
        img = Image.frombytes("RGB", self.screen.get_size(), image_data)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        game_state_list = []
        for gr in range(ROWS):
            for gc in range(COLS):
                for lr in range(ROWS):
                    for lc in range(COLS):
                        game_state_list.append({
                            "global_row": gr, "global_col": gc,
                            "local_row": lr, "local_col": lc,
                            "player": int(game.board.squares[gr][gc][lr][lc]),
                        })

        payload = {
            "image_base64": img_str,
            "player_turn": "X" if self.player == 1 else "O",
            "global_state": game_state_list,
            "allowed_square": game.allowed_square
        }

        try:
            print(f"--- Sending API Request for Player {self.player} ---")
            response = requests.post(self.api_url, json=payload, timeout=20)
            if response.status_code == 200:
                move = response.json()
                # Verify coordinates are present
                if all(k in move for k in ["global_row", "global_col", "local_row", "local_col"]):
                    return (move["global_row"], move["global_col"], move["local_row"], move["local_col"])
            else:
                print(f"API Error: Status {response.status_code}")
        except Exception as e:
            print(f"VLM API CONNECTION ERROR: {e}")

        return None

class UltimateTTTBot:
    def __init__(self, player, max_time = 2.0):
        self.player = player
        self.opponent = 1 if player == 2 else 2
        self.max_time = max_time

    def get_bot_move(self, game):
        start_time = time.time()
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return None
        best_move = legal_moves[0]
        current_depth = 1

        while True:
            if time.time() - start_time > self.max_time * 0.95:
                break
            try:
                if current_depth > 1:
                    # order to improve search time by ignoring moves that aren't better than the current best
                    ordered_moves = [best_move] + [move for move in legal_moves if move != best_move]
                else:
                    ordered_moves = legal_moves

                _, current_best_move = self.minimax(game, current_depth, -math.inf, math.inf, True, ordered_moves)
                if current_best_move:
                    best_move = current_best_move
                current_depth += 1
            except Exception as e:
                print(e)
                break
        return best_move

    def minimax(self, game, depth, alpha, beta, maximizing_player, moves = None):
        is_minimax_ordered = moves is not None
        legal_moves = moves if is_minimax_ordered else game.get_legal_moves()

        if depth == 0 or game.is_game_over() or not legal_moves:
            return self.evaluate(game), None

        best_move = None
        current_player = self.player if maximizing_player else self.opponent
        next_player = not maximizing_player

        if maximizing_player:
            value = -math.inf
        else:
            value = math.inf

        for move in legal_moves:
            new_game = game.copy()
            new_game.board.mark_square(move[0], move[1], move[2], move[3], current_player)
            g_row, g_col, l_row, l_col = move
            new_game.board.global_squares[g_row, g_col] = check_win(new_game.board.squares[g_row, g_col])
            if new_game.board.global_squares[l_row, l_col] != 0:
                new_game.allowed_square = None
            else:
                new_game.allowed_square = (l_row, l_col)

            # need to switch player so that the function does not mistake the next move as its own
            new_game.switch_player()

            eval_score, _ = self.minimax(new_game, depth - 1, alpha, beta, next_player)

            if maximizing_player:
                if eval_score > value:
                    value, best_move = eval_score, move
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            else:
                if eval_score < value:
                    value, best_move = eval_score, move
                beta = min(beta, value)
                if beta <= alpha:
                    break
        return value, best_move

    # Evaluate the current game state
    def evaluate(self, game):
        winner = game.get_winner()

        if winner == self.player:
            return 10000000
        elif winner == self.opponent:
            return -10000000

        score = 0

        # Global Board Evaluation
        global_board = game.board.global_squares
        score += self.evaluate_global_board(global_board)

        # Punish for giving opponent free play
        if game.allowed_square is None: score -= 500

        # Local Board Evaluation
        for row in range(ROWS):
            for col in range(COLS):
                board = game.board.squares[row][col]
                if check_win(board) == self.player:
                    score += 2000
                    if row == 1 and col == 1: score += 2000
                elif check_win(board) == self.opponent:
                    score -= 2000
                else:
                    score += self.evaluate_local_board(board)
        return score

    # General Evaluation
    def evaluate_lines(self, board):
        lines = [
            [(0,0), (0,1), (0,2)],
            [(1,0), (1,1), (1,2)],
            [(2,0), (2,1), (2,2)],
            [(0,0), (1,0), (2,0)],
            [(0,1), (1,1), (2,1)],
            [(0,2), (1,2), (2,2)],
            [(0,0), (1,1), (2,2)],
            [(0,2), (1,1), (2,0)],
        ]

        score = 0

        center_square = board[1][1]
        if center_square == self.player: score += 0.35
        elif center_square == self.opponent: score -= 0.35

        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for row, col in corners:
            corner = board[row][col]
            if corner == self.player: score += 0.30
            elif corner == self.opponent: score -= 0.30

        for line in lines:
            values = [board[r][c] for r, c in line]
            if values.count(self.player) == 2 and 0 in values:
                score += 20
            elif values.count(self.opponent) == 2 and 0 in values:
                score -= 20
            elif values.count(self.player) == 1 and values.count(0) == 2:
                score += 1
            elif values.count(self.opponent) == 1 and values.count(0) == 2:
                score -= 1
        return score

    def evaluate_global_board(self, board):
        return self.evaluate_lines(board) * 10000

    def evaluate_local_board(self, board):
        return self.evaluate_lines(board) * 5