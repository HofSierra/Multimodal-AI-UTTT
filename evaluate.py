import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from transformers import AutoProcessor
from PIL import Image as PILImage
import json
import re

# CONFIGURATION

#MODEL_NAME = "unsloth/Qwen3-VL-8B-Thinking-unsloth-bnb-4bit"
MODEL_NAME = "unsloth/Qwen3-VL-8B-Instruct-unsloth-bnb-4bit"
DATASET_TEST_PATH = "uttt_qwen_dataset/test.parquet"
MAX_SEQ_LENGTH = 2048
DTYPE = None

# LOAD MODEL

def load_vlm_model():
    print(f"Loading Model: {MODEL_NAME}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = MODEL_NAME,
        max_seq_length = MAX_SEQ_LENGTH,
        dtype = DTYPE,
        load_in_4bit = True,
        trust_remote_code = True
    )

    processor = AutoProcessor.from_pretrained(MODEL_NAME, trust_remote_code=True)

    model.config.use_cache = False

    print("Model and Tokenizer loaded successfully")
    return model, tokenizer, processor

# EVALUATION FUNCTION

def evaluate_baseline(model, tokenizer, processor, test_data_path):
    """
    baseline evaluation on evaluation set, to test model's ability.
    """

    try:
        test_data = load_dataset("parquet", data_files={"test": test_data_path}, split="test")
    except Exception as e:
        print(f"Error loading test dataset: {e}")
        return 0,0,0

    # small sample to avoid long initial run time
    sample_size = min(len(test_data),1000)
    print(f"\nStarting baseline evaluation on {sample_size} samples")

    correct_moves = 0
    correct_allowed_squares = 0
    legal_move_count = 0
    invalid_model_move = 0
    total_similarity_score = 0
    total_moves = 0

    for i in range(sample_size):
        sample = test_data[i]

        # --- Input Prep ---

        # Extract text prompt
        user_content = next(item for item in sample["messages"] if item["role"] == "user")["content"]
        user_prompt_text = next(item["text"] for item in user_content if item["type"] == "text")

        # Extract ground truth move
        assistant_response = next(item for item in sample["messages"] if item["role"] == "assistant")["content"][0]["text"]
        ground_truth_move = parse_move_from_text(assistant_response)
        if ground_truth_move is None:
            print(f"Skipping sample {i}: Could not parse ground truth JSON.")
            continue

        ground_truth_allowed_square = parse_square_from_text(assistant_response)
        if ground_truth_allowed_square is None:
            ground_truth_allowed_square = {
                "global_row": -1,
                "global_col": -1
            }


        legal_moves = sample["legal_moves"]

        image = sample["image"].convert("RGB")

        simplified_prompt = (
                "\n\nAnswer in two sentences. Be Brief." +
                "\n\nOne Sentence will be the allowed board in the format: {\"global_row\": r, \"global_col\": c}"+
                "\n\nThe second sentence will be the bext available move to play in the format: {\"global_row\": r, \"global_col\": c, \"local_row\": r, \"local_col\": c}." +
                "<|image|>" +
                user_prompt_text
            # "\n\nOutput only the coordinates of the green square as a JSON object: {\"global_row\": r, \"global_col\": c}"
            # "{\"global_row\": r, \"global_col\": c, \"local_row\": r, \"local_col\": c}."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image,
                    },
                    {"type": "text", "text": simplified_prompt},
                ],
            }
        ]

        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(model.device)


        # --- Model Inference ---
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=256, use_cache=True)
        # Decode Output
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=False)
        # remove input prompt to get just the response
        response_text = response_text.split("<|im_start|>assistant\n")[-1].strip()

        # --- Parse Model's Move Attempt ---
        model_move = parse_move_from_text(response_text)

        model_allowed_square = parse_allowed_square_from_text(response_text)

        total_moves += 1
        is_correct_move = compare_moves(model_move, ground_truth_move)
        is_correct_allowed_square = compare_sqs(model_allowed_square, ground_truth_allowed_square)
        is_legal = is_move_legal(model_move, legal_moves)
        is_model_move_invalid = model_move_invalid(model_move)
        similarity_score = move_similarity(model_move, ground_truth_move)

        total_similarity_score += similarity_score

        if is_correct_move:
            correct_moves += 1

        if is_correct_allowed_square:
            correct_allowed_squares += 1

        if is_legal:
            legal_move_count += 1

        if is_model_move_invalid:
            invalid_model_move += 1

        if i<5 or is_correct_move or not is_correct_move:
            print(f"\nSample {i+1}")
            print(f"Ground Truth Best Move: {ground_truth_move}")
            if ground_truth_allowed_square["global_row"] == -1:
                print(f"Ground Truth Allowed Square: Any Board")
            print("-" * 100)
            print(f"Model Move: {model_move}")
            print(f"Model Allowed Square: {model_allowed_square}")
            print(f"Move Result: {'CORRECT MOVE' if is_correct_move else 'INCORRECT MOVE'}")
            print(f"Allowed Sqaure Result: {'CORRECT Sqaure' if is_correct_allowed_square else 'INCORRECT Square'}")
            print(f"Move Similarity Score: {similarity_score}")
            print(f"Move Allowed?: {'Legal Move' if is_legal else 'Illegal Move'}")
            print(f"{'Invalid Model Move' if is_model_move_invalid else ''}")

    move_accuracy = (correct_moves / total_moves) * 100 if total_moves > 0 else 0
    square_accuracy = (correct_allowed_squares / total_moves) * 100 if total_moves > 0 else 0
    legal_move_accuracy = (legal_move_count/total_moves) * 100 if total_moves > 0 else 0
    avg_similarity_score = total_similarity_score / total_moves
    invalid_moves = invalid_model_move
    return move_accuracy, square_accuracy, legal_move_accuracy, total_moves, invalid_moves, avg_similarity_score

# Helper functions

def parse_move_from_text(text):
    # extract JSON dictionary from VLM output

    match = re.search(r'\{\s*"global_row":\s*\d+,\s*"global_col":\s*\d+,\s*"local_row":\s*\d+,\s*"local_col":\s*\d+\s*}', text)
    if match:
        try:
            move_str = match.group(0).replace('"', '\"')
            return json.loads(move_str)
        except json.JSONDecodeError:
            pass

    return None

def parse_square_from_text(text):
    match = re.search(r'Allowed Square:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]', text)
    none_match = re.search(r'Allowed Sqaure:\s*None', text)
    if none_match:
        return {
            "global_row": -1,
            "global_col": -1
        }
    if match:
        try:
            return {
                "global_row": int(match.group(1)),
                "global_col": int(match.group(2))
            }
        except Exception:
            pass
    return None

def parse_allowed_square_from_text(text):
    match = re.search(r'\{\s*"global_row":\s*(\d+),\s*"global_col":\s*(\d+)\s*\}', text)
    if match:
        try:
            move_str = f'{{"global_row": {match.group(1)}, "global_col": {match.group(2)}}}'
            return json.loads(move_str)
        except json.JSONDecodeError:
            pass
    return None

def compare_moves(model_move, ground_truth_move):
    # compare model move against ground truth
    if model_move is None:
        return False

    keys = ["global_row", "global_col", "local_row", "local_col"]

    try:
        return all(model_move.get(k) == ground_truth_move.get(k) for k in keys)
    except Exception:
        return False

def compare_sqs(model_square, ground_truth_square):
    # compare model move against ground truth
    if model_square is None:
        return False
    if ground_truth_square.get("global_row") == -1:
        return True

    keys = ["global_row", "global_col"]

    try:
        return all(model_square.get(k) == ground_truth_square.get(k) for k in keys)
    except Exception:
        return False

def is_move_legal(model_move, legal_moves):
    if model_move is None:
        return False
    for m in legal_moves:
        if (
                model_move["global_row"] == m["global_row"] and
                model_move["global_col"] == m["global_col"] and
                model_move["local_row"] == m["local_row"] and
                model_move["local_col"] == m["local_col"]
        ):
            return True
    return False

def model_move_invalid(model_move):
    if model_move is None:
        return True
    required_keys = ['global_row', 'global_col', 'local_row', 'local_col']
    if not all(key in model_move for key in required_keys):
        return True
    coordinates = [
        model_move.get('global_row'),
        model_move.get('global_col'),
        model_move.get('local_row'),
        model_move.get('local_col'),
    ]

    for coord in coordinates:
        if not isinstance(coord, int) or coord not in {0, 1, 2}:
            return True

    return False

def move_similarity(model_move, ground_truth_move):
    score = 0
    if model_move is None:
        return 0.0

    keys = ["global_row", "global_col", "local_row", "local_col"]
    if not all(key in model_move for key in keys):
        return 0.0

    if model_move["global_row"] == ground_truth_move["global_row"]:
        score += 1
    if model_move["global_col"] == ground_truth_move["global_col"]:
        score += 1
    if model_move["local_row"] == ground_truth_move["local_row"]:
        score += 1
    if model_move["local_col"] == ground_truth_move["local_col"]:
        score += 1
    return score / 4.0

# Main Execution

if __name__ == "__main__":
    model, tokenizer, processor = load_vlm_model()
    move_accuracy, square_accuracy, legal_move_accuracy, total_samples, invalid_moves, avg_similarity_score = evaluate_baseline(model, tokenizer, processor, DATASET_TEST_PATH)

    print("\n" + "="*100)
    print("BASELINE EVALUATION RESULTS")
    print(f"Total samples: {total_samples}")
    print(f"Baseline Move Accuracy: {move_accuracy:.2f}%")
    print(f"Baseline Allowed Square Accuracy: {square_accuracy:.2f}%")
    print(f"Average Move Similarity Score: {avg_similarity_score}")
    print(f"Baseline Legal Move Accuracy: {legal_move_accuracy:.2f}%")
    print(f"Invalid Moves by Model (Hallucination/Out-of-bounds): {invalid_moves} moves")
    print("\n" + "="*100)
