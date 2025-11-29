import json
import os
from datasets import Dataset, Features, Image, Value, Sequence, Split
import pandas as pd
from sklearn.model_selection import train_test_split
from PIL import Image as PILImage

# ---------------------------------------------------------
# CONFIGURATION (Updated based on your screenshot)
# ---------------------------------------------------------
# Path relative to where you run the script (project root)
INPUT_JSON_FILE = 'logs/bot_moves.jsonl'

# Base folder. Since JSON has "screens/image_1.png", we use current dir '.'
IMAGE_BASE_FOLDER = '.'

OUTPUT_DIR = 'uttt_qwen_dataset'


# ---------------------------------------------------------
# HELPER: ASCII BOARD RENDERER
# ---------------------------------------------------------
def render_ascii_board(global_state_list):
    """
    Renders 9 separate 3x3 grids with explicit 0-1-2 axis labels.
    Critical for small datasets to ground the coordinates visually.
    """
    symbols = {0: '.', 1: 'X', 2: 'O'}

    # Map (g_row, g_col, l_row, l_col) -> symbol
    state_map = {}
    for cell in global_state_list:
        key = (cell['global_row'], cell['global_col'], cell['local_row'], cell['local_col'])
        state_map[key] = symbols.get(cell['player'], '?')

    board_sections = []

    # Iterate through Global Boards
    for g_r in range(3):
        for g_c in range(3):
            # Header with Global Coordinates
            section = [f"=== Global Board [Row {g_r}, Col {g_c}] ==="]

            # Column Axis Header (indent to match cell spacing)
            section.append("    0 1 2")
            section.append("   -------")

            # Render rows with Row Axis Label
            for l_r in range(3):
                row_cells = []
                for l_c in range(3):
                    val = state_map.get((g_r, g_c, l_r, l_c), '.')
                    row_cells.append(val)
                # Format: "0 | . X O"
                section.append(f"{l_r} | " + " ".join(row_cells))

            board_sections.append("\n".join(section))

    return "\n\n".join(board_sections)


def format_legal_moves(moves_list):
    """
    Compacts the legal moves list into a clear 'Global -> Local' format.
    """
    formatted = []
    for move in moves_list:
        m_str = (f"- Global[{move['global_row']}, {move['global_col']}] -> "
                 f"Local[{move['local_row']}, {move['local_col']}]")
        formatted.append(m_str)
    return "\n".join(formatted)


# ---------------------------------------------------------
# PROMPT FORMATTING
# ---------------------------------------------------------
def format_user_prompt(data):
    """
    Constructs a highly structured prompt to maximize training efficiency on small data.
    """
    global_state_ascii = render_ascii_board(data.get("global state", []))
    legal_moves_str = format_legal_moves(data.get("legal moves", []))
    allowed_squares = data.get("allowed squares", [])
    player = str(data.get("player", "Unknown"))

    # Format allowed squares clearly
    # If it's a list like [1, 2], it usually means Global Board Indices if flattened?
    # Or strict coordinates? We treat it as context.
    allowed_context = f"{allowed_squares}"

    # text_prompt = (
    #     f"You are an expert Ultimate Tic Tac Toe player. "
    #     f"Analyze the board state provided in the image and the ASCII text below.\n\n"
    #     f"--- COORDINATE SYSTEM (CRITICAL) ---\n"
    #     f"1. ALL coordinates are 0-indexed (0, 1, 2).\n"
    #     f"2. Hierarchy: Global Board [Row, Col] > Local Square [Row, Col].\n"
    #     f"3. Valid Moves: You must play in the 'Active Global Board' determined by the previous move.\n\n"
    #     f"--- CURRENT TURN ---\n"
    #     f"Player: {player} (X=Player 1, O=Player 2)\n"
    #     f"Active Global Targets: {allowed_context}\n\n"
    #     f"--- BOARD STATE (ASCII) ---\n"
    #     f"{global_state_ascii}\n\n"
    #     f"--- LEGAL MOVES LIST ---\n"
    #     f"{legal_moves_str}\n\n"
    #     f"--- TASK ---\n"
    #     f"1. Identify the Active Global Board from the list above.\n"
    #     f"2. Select the BEST move to win that local board or send the opponent to a disadvantageous global board.\n"
    #     f"3. Output a Chain of Thought followed by the Best Move in JSON."
    # )

    text_prompt = (
        f"Analyze the board state provided in the image.\n\n"
        f"--- COORDINATE SYSTEM (CRITICAL) ---\n"
        f"ALL coordinates are 0-indexed (0, 1, 2).\n"
        f"For Example, the middle left would be (1,0), middle middle would be (1,1) and middle right would be (1,2)"
        f"--- CURRENT TURN ---\n"
        f"Player: {player} (X=Player 1, O=Player 2)\n"
        f"--- TASK ---\n"
        f"Find out which is the active global board currently. It is highlighted in green, and if no highlighted board, then player can play anywhere."
    )
    return text_prompt


def format_assistant_response(data):
    chain_of_thought = data.get("chain of thought", "")
    best_move_json = json.dumps(data.get("best move", {}))
    allowed_square_json = json.dumps(data.get("allowed squares", {}))
    return f"<think>{chain_of_thought}</think>\nBest Move:{best_move_json}\nAllowed Square:{allowed_square_json}"


# ---------------------------------------------------------
# DATA GENERATOR
# ---------------------------------------------------------
def gen_data():
    if not os.path.exists(INPUT_JSON_FILE):
        print(f"Error: Input file '{INPUT_JSON_FILE}' not found.")
        print("Please ensure you are running this script from the 'ultimate-tic-tac-toe' folder.")
        return

    print(f"Processing {INPUT_JSON_FILE}...")

    with open(INPUT_JSON_FILE, 'r') as f:
        for line_num, line in enumerate(f):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON at line {line_num}")
                continue

            img_rel_path = entry.get("image path")
            # os.path.join('.', 'screens/image_1.png') works if running from root
            full_img_path = os.path.join(IMAGE_BASE_FOLDER, img_rel_path)

            if not os.path.exists(full_img_path):
                print(f"Warning: Image not found at {full_img_path}. Skipping.")
                continue

            try:
                img_obj = PILImage.open(full_img_path).convert("RGB")
            except Exception as e:
                print(f"Error loading image {full_img_path}: {e}")
                continue

            messages = [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are an expert Ultimate Tic-Tac-Toe player. Analyze the board and the current game constraints. You MUST provide your strategic reasoning in <think> tags followed by the final move as a JSON object."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": format_user_prompt(entry)}
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": format_assistant_response(entry)}
                    ]
                }
            ]
            yield {
                "image": img_obj,
                "messages": messages,
                "legal_moves": entry.get("legal moves", []),
            }


# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
def main():
    features = Features({
        "image": Image(),
        "messages": [{
            "role": Value("string"),
            "content": [{
                "type": Value("string"),
                "text": Value("string"),
            }],
        }],

        "legal_moves": [{
            "global_row": Value("int32"),
            "global_col": Value("int32"),
            "local_row": Value("int32"),
            "local_col": Value("int32"),
        }],
    })

    ds = Dataset.from_generator(gen_data, features=features)

    if len(ds) == 0:
        print("No data loaded.")
        return

    print(f"Loaded {len(ds)} samples.")

    # 90% Train, 5% Test, 5% Val
    train_testvalid = ds.train_test_split(test_size=0.2, seed=42)
    test_eval = train_testvalid['test'].train_test_split(test_size=0.5, seed=42)

    final_dataset = {
        'train': train_testvalid['train'],
        'test': test_eval['train'],
        'evaluate': test_eval['test']
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for split_name, dataset in final_dataset.items():
        file_name = f"{OUTPUT_DIR}/{split_name}.parquet"
        print(f"Saving {split_name} split to {file_name}...")
        dataset.to_parquet(file_name)

    print("\nSuccess! Dataset created in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()