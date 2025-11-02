#Ultimate Version
import math
import numpy as np
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

# Evaluate the current game state
def evaluate(game, player):

    opponent = 1 if player == 2 else 2
    winner = game.get_winner()

    if winner == player:
        return 1000
    elif winner == opponent:
        return -1000

    score = 0
    # Local Board Evaluation

    for row in range(ROWS):
        for col in range(COLS):
            board = game.board.squares[row][col]
            if check_win(board) == player:
                score += 100
            elif check_win(board) == opponent:
                score -= 100
            else:
                score += evaluate_local_board(board, player)

    return score

# Evaluate a Local Board
def evaluate_local_board(board, player):
    opponent = 1 if player == 2 else 2
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
    for line in lines:
        values = [board[r][c] for r, c in line]
        if opponent not in values:
            score += 1
        if values.count(player) == 2 and 0 in values:
            score += 5
    return score

def minimax(game, depth, alpha, beta, maximizing_player, player):
    opponent = 1 if player == 2 else 2

    if depth == 0 or game.is_game_over():
        return evaluate(game, player), None

    legal_moves = game.get_legal_moves()
    if not legal_moves:
        return evaluate(game, player), None

    best_move = None

    if maximizing_player:
        value = -math.inf
        for move in legal_moves:
            new_game = game.copy()
            new_game.board.mark_square(move[0], move[1], move[2], move[3], player)
            g_row, g_col, l_row, l_col = move
            new_game.board.global_squares[g_row, g_col] = check_win(new_game.board.squares[g_row, g_col])
            if new_game.board.global_squares[l_row, l_col] != 0:
                new_game.allowed_square = None
            else:
                new_game.allowed_square = (l_row, l_col)

            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, False, player)
            if eval_score > value:
                value, best_move = eval_score, move
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best_move

    else:
        value = math.inf
        for move in legal_moves:
            new_game = game.copy()
            new_game.board.mark_square(move[0], move[1], move[2], move[3], opponent)
            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, True, player)
            if eval_score < value:
                value, best_move = eval_score, move
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

def get_bot_move(game, player, depth=3):
    _, move = minimax(game, depth, -math.inf, math.inf, True, player)
    return move