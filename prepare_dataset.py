# prepare_dataset.py
import pandas as pd
from datasets import Dataset, Image
import json

finetuning_data = []

# Questions we will train the model on
question_variations = [
    "Where is the active board?",
    "Which board is highlighted in green?",
    "What are the (row, col) coordinates of the board I must play on?",
    "Identify the allowed board.",
    "Which local board is currently active?"
]

with open("vqa_perception_dataset.jsonl", "r") as f:
    for line in f:
        log = json.loads(line)

        image_path = log["image_path"]
        # Format the answer as a simple string
        answer = str(log["active_board_coords"])  # e.g., "(1, 2)" or "None"

        # Create a (question, answer) pair for each variation
        for q in question_variations:
            finetuning_data.append({
                "image_path": image_path,
                "question": q,
                "answer": answer
            })

# Create a Pandas DataFrame
df = pd.DataFrame(finetuning_data)

# Convert to Hugging Face Dataset
dataset = Dataset.from_pandas(df)
# Cast the image_path column to the Image type
dataset = dataset.map(lambda x: {"image": x["image_path"]}, remove_columns=["image_path"])
dataset = dataset.cast_column("image", Image())

# Save as Parquet file
dataset.to_parquet("finetune_active_board.parquet")
print(f"Finetuning dataset created with {len(dataset)} examples!")