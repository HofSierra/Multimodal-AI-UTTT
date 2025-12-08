import random
import json, os
from config import *
from PIL import Image

ROTATION_ANGLES = [0, 90, 180, 270]

def rotate_coords(row, col, angle):
    if angle == 0:
        return row, col
    if angle == 90:
        return col, (2 - row)
    if angle == 180:
        return (2 - row), (2 - col)
    if angle == 270:
        return (2 - col), row

    raise ValueError ("Invalid angle.")


def rotate_and_save_image(original_path, new_path, angle):
    try:
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        img = Image.open(original_path)
        rotated_img = img.rotate(-angle, expand=True)

        rotated_img.save(new_path)
        print(f"  -> Generated image {new_path}")

    except FileNotFoundError:
        print(f"  -> WARNING: Original image not found at {original_path}. Skipping image generation.")
    except Exception as e:
        print(f"  -> ERROR rotating image {original_path}: {e}")

def rotate_log_entry(original_log, angle):
    if angle == 0:
        return original_log.copy()

    new_log = original_log.copy()

    # image rotation
    path = original_log["image path"]
    if angle == 0:
        new_image_path = path
    else:
        base, ext = os.path.splitext(path)
        if "_rotated_" in base:
            base = base.rsplit("_rotated_", 1)[0]
        new_image_path = f"{base}_rotated_{angle}{ext}"

        rotate_and_save_image(path, new_image_path, angle)
    new_log["image path"] = new_image_path

    # best move
    gr, gc, lr, lc = (
        original_log["best move"]["global_row"],
        original_log["best move"]["global_col"],
        original_log["best move"]["local_row"],
        original_log["best move"]["local_col"],
    )
    new_best_move_gr, new_best_move_gc, = rotate_coords(gr, gc, angle)
    new_best_move_lr, new_best_move_lc = rotate_coords(lr, lc, angle)

    new_log["best move"] = {
        "global_row": new_best_move_gr, "global_col": new_best_move_gc,
        "local_row": new_best_move_lr, "local_col": new_best_move_lc,
    }

    new_legal_moves = []
    for move in original_log["legal moves"]:
        new_legal_move_gr, new_legal_move_gc = rotate_coords(move["global_row"], move["global_col"], angle)
        new_legal_move_lr, new_legal_move_lc = rotate_coords(move["local_row"], move["local_col"], angle)

        new_legal_moves.append({
            "global_row": new_legal_move_gr, "global_col": new_legal_move_gc,
            "local_row": new_legal_move_lr, "local_col": new_legal_move_lc,
        })
    new_log["legal moves"] = new_legal_moves

    new_global_state = []
    for cell in original_log["global state"]:
        new_gr, new_gc = rotate_coords(cell["global_row"], cell["global_col"], angle)
        new_lr, new_lc = rotate_coords(cell["local_row"], cell["local_col"], angle)
        new_global_state.append({
            "global_row": new_gr, "global_col": new_gc,
            "local_row": new_lr, "local_col": new_lc,
            "player": cell["player"]
        })
    new_log["global state"] = new_global_state

    allowed_square = original_log["allowed squares"]
    new_allowed_square = None
    if allowed_square is not None:
        ar, ac = rotate_coords(allowed_square[0], allowed_square[1], angle)
        new_allowed_square = [ar, ac]

    new_log["allowed squares"] = new_allowed_square

    new_move = (new_best_move_gr, new_best_move_gc, new_best_move_lr, new_best_move_lc)
    legal_moves_count = len(original_log["legal moves"])
    player = original_log["player"]

    new_cot = gen_cot(
        move=new_move,
        player=player,
        legal_moves_count=legal_moves_count,
        allowed_square=new_allowed_square,
    )

    new_log["chain of thought"] = new_cot

    return new_log

def gen_cot(move, player, legal_moves_count, allowed_square):
    gr, gc, lr, lc = move
    player_str = "X" if player == 1 else "O"

    cot = f"Current player: {player_str}. "
    is_constrained = allowed_square is not None

    if is_constrained:
        ag_row, ag_col = allowed_square
        constraint_check = f"The UTTT constraint is active, requiring a move on global board ({ag_row},{ag_col}). The chosen move ({gr},{gc}) respects this constraint. "
    else:
        constraint_check = f"There is currently no UTTT constraint (Free Play). The selected global board ({gr},{gc}) is available for play. "

    cot += f"Move Legality Check: {constraint_check}The target cell ({lr},{lc}) within that board must be empty. This move has been verified as legal. Total legal moves available: {legal_moves_count}. "

    strategy = ""
    is_center = (lr == 1 and lc == 1)
    is_corner = (lr in (0, 2) and lc in (0, 2))
    is_local_diagonal = (lr == lc or lr + lc == 2)
    is_global_diagonal = (gr == gc or gr + gc == 2)

    if is_constrained and (gr, gc) == allowed_square and is_center:
        strategy += "This move secures the local center and, critically, directs the opponent to the exact same board, forcing them into a high-pressure defensive decision."
    elif is_center:
        strategy += "This move secures the central position of the local board, which is strategically the most valuable square for controlling future lines and maximizing win potential."
    elif is_corner:
        strategy += "This move secures a corner position in the local board, establishing key control points for a potential local win and strong setup."
    elif is_local_diagonal:
        strategy += "This move establishes a critical point along a local diagonal, immediately creating a win threat or setting up a powerful two-way attack within the sub-board."
    elif is_global_diagonal and random.random() < 0.4:
        strategy += "This move contributes to securing a win along a global diagonal (either main or anti-diagonal), which is a high-value strategy for overall game control and board dominance."
    else:
        strategy += "This is a key defensive move, blocking an immediate opponent win in the local board, or securing an important edge position to maintain parity."

    cot += f"Strategic Analysis: I am playing move ({gr},{gc}) ({lr},{lc}). {strategy} "
    cot += f"Final Move Coordinates: ({gr},{gc}) ({lr},{lc})."

    return cot

def process_log_rotation(original_log: list[dict]) -> dict:
    print("Processing Logs...")
    base_log = original_log

    rotated_logs = {
        0: [],
        90: [],
        180: [],
        270: []
    }

    for entry in base_log:
        for angle in ROTATION_ANGLES:
            rotated_entry = rotate_log_entry(entry, angle)
            rotated_logs[angle].append(rotated_entry)

    print("\n--- Processing Complete ---")
    return rotated_logs

def save_logs_to_jsonl(all_logs: dict):
    output_lines = []

    original_logs = all_logs.get(0, [])

    num_entries = len(original_logs)

    for i in range(num_entries):
        for angle in ROTATION_ANGLES:
            log_list = all_logs.get(angle, [])
            if i < len(log_list):
                entry = log_list[i]
                data = entry.copy()
                data['rotation_angle'] = angle
                output_lines.append(json.dumps(data) + '\n')

    try:
        os.makedirs(os.path.dirname(SYNTHETIC_LOG_FILE_PATH), exist_ok=True)
        with open(SYNTHETIC_LOG_FILE_PATH, 'w') as f:
            f.writelines(output_lines)
        print(f"\nSuccessfully wrote {len(output_lines)} lines to: {SYNTHETIC_LOG_FILE_PATH}")
    except Exception as e:
        print(f"\nWARNING: Could not write file to {SYNTHETIC_LOG_FILE_PATH}. Error: {e}")

    print(f"\nFile writing simulation complete. Total {len(output_lines)} lines prepared.")

if __name__ == "__main__":
    print(f"Attempting to read log entries from: {LOG_FILE_PATH}")
    original_log_file = []

    try:
        with open(LOG_FILE_PATH, 'r') as f:
            for line in f:
                original_log_file.append(json.loads(line))
    except Exception as e:
        print(f"WARNING: Actual file reading failed (Error: {e}). Using mock data for execution.")

    new_logs = process_log_rotation(original_log_file)
    save_logs_to_jsonl(new_logs)
