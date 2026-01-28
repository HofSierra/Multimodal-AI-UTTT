# const values
WIDTH = 720
HEIGHT = 720
ROWS = 3
COLS = 3
SIZE = WIDTH // ROWS
LOCAL_SIZE = SIZE // ROWS
RADIUS = SIZE // 4
LOCAL_RADIUS = LOCAL_SIZE // 4

LINE_WIDTH = 15
GLOBAL_LINE_WIDTH = 20
LOCAL_LINE_WIDTH = 7
CROSS_WIDTH = 20
PADDING = 50

# colors
BG_COLOR = (230, 217, 200)
LINE_COLOR = (0, 0, 0)
WIN_LINE_COLOR = (3,122,118)
DENIED_BOARD_LINE_COLOR = (0, 0, 0, 60)
CROSS_COLOR = (205, 42, 91)
CIRCLE_COLOR = (8, 112, 202)
HOVER_COLOR = (0, 0, 0, 60)
ALLOWED_BOARD_COLOR = (182, 219, 192, 85)

# paths
IMAGES_FOLDER = "screens"
LOG_FILE_PATH = "logs/bot_moves.jsonl"
SYNTHETIC_LOG_FILE_PATH = "logs/bot_moves_synthetic.jsonl"
DATASET_FOLDER = "uttt_qwen_dataset"

# model
MODEL_NAME = "unsloth/Qwen3-VL-8B-Instruct-unsloth-bnb-4bit"

# model relevant paths
DATASET_TRAIN_PATH = "uttt_qwen_dataset/train.parquet"
DATASET_EVAL_PATH = "uttt_qwen_dataset/evaluate.parquet"
DATASET_TEST_PATH = "uttt_qwen_dataset/test.parquet"
OUTPUT_DIR_V2 = "adapter_uttt_qwen_8b_v2"