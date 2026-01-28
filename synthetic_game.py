import json, os, re
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

def rotate_cot_text(text, angle):
    if angle == 0:
        return text

    def rotate_func(r, c, a):
        if a == 90: return c, 2 - r
        if a == 180: return 2 - r, 2 - c
        if a == 270: return 2 - c, r
        return r, c

    # 1. Rotate structured dictionary-like blocks in text
    def fix_block(match):
        # Extract digits: gr, gc, lr, lc
        d = [int(x) for x in re.findall(r'\d+', match.group(0))]
        ngr, ngc = rotate_func(d[0], d[1], angle)
        nlr, nlc = rotate_func(d[2], d[3], angle)
        return f"{{global_row: {ngr}, global_col: {ngc}, local_row: {nlr}, local_col: {ngc}}}"

    text = re.sub(r'\{global_row: \d+, global_col: \d+, local_row: \d+, local_col: \d+\}', fix_block, text)

    # 2. Rotate all free-text coordinate pairs (r, c)
    def fix_pair(match):
        r, c = int(match.group(1)), int(match.group(2))
        nr, nc = rotate_func(r, c, angle)
        return f"({nr}, {nc})"

    text = re.sub(r'\((\d)\s*,\s*(\d)\)', fix_pair, text)
    return text

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
    return new_log

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
