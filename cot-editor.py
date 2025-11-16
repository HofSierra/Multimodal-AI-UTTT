import streamlit as st
import json
import os
from pathlib import Path

# Configuration
LOG_FILE = "logs/bot_moves.jsonl"
SCREENS_FOLDER = "screens"

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'data' not in st.session_state:
    st.session_state.data = []
if 'modified' not in st.session_state:
    st.session_state.modified = False


def load_data():
    """Load data from JSONL file."""
    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
    return data


def save_data(data):
    """Save data back to JSONL file."""
    with open(LOG_FILE, 'w') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')


def format_board_state(global_state):
    """Format the board state into a readable grid."""
    board = [[0 for _ in range(9)] for _ in range(9)]

    for cell in global_state:
        gr, gc = cell["global_row"], cell["global_col"]
        lr, lc = cell["local_row"], cell["local_col"]
        player = cell["player"]
        row = gr * 3 + lr
        col = gc * 3 + lc
        board[row][col] = player

    return board


# Load data
if not st.session_state.data:
    st.session_state.data = load_data()

# Title
st.title("🎮 Ultimate Tic-Tac-Toe Chain of Thought Editor")

# Check if data exists
if not st.session_state.data:
    st.error(f"No data found in {LOG_FILE}")
    st.stop()

# Sidebar navigation
st.sidebar.header("Navigation")
total_entries = len(st.session_state.data)
st.sidebar.write(f"Total entries: {total_entries}")

# Entry selector
st.session_state.current_index = st.sidebar.number_input(
    "Go to entry:",
    min_value=0,
    max_value=total_entries - 1,
    value=st.session_state.current_index
)

# Navigation buttons
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("⬅️ Prev"):
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.rerun()

if col2.button("➡️ Next"):
    if st.session_state.current_index < total_entries - 1:
        st.session_state.current_index += 1
        st.rerun()

if col3.button("💾 Save"):
    save_data(st.session_state.data)
    st.sidebar.success("Saved!")
    st.session_state.modified = False

# Filter options
st.sidebar.header("Filters")
show_empty_only = st.sidebar.checkbox("Show only empty chain of thought")
show_player = st.sidebar.selectbox("Filter by player", ["All", "Player 1", "Player 2"])

# Apply filters
filtered_indices = []
for i, entry in enumerate(st.session_state.data):
    if show_empty_only and entry.get("chain of thought", "").strip():
        continue
    if show_player == "Player 1" and entry["player"] != 1:
        continue
    if show_player == "Player 2" and entry["player"] != 2:
        continue
    filtered_indices.append(i)

if filtered_indices:
    st.sidebar.write(f"Filtered: {len(filtered_indices)} entries")
    if st.sidebar.button("Jump to next filtered"):
        for idx in filtered_indices:
            if idx > st.session_state.current_index:
                st.session_state.current_index = idx
                st.rerun()
                break

# Current entry
current_entry = st.session_state.data[st.session_state.current_index]

# Display progress
st.progress((st.session_state.current_index + 1) / total_entries)
st.subheader(f"Entry {st.session_state.current_index + 1} of {total_entries}")

# Two columns layout
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📸 Game Board")

    # Display image
    image_path = current_entry.get("image path", "")
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.error(f"Image not found: {image_path}")

    # Game info
    st.write(f"**Player:** {current_entry['player']} ({'X' if current_entry['player'] == 1 else 'O'})")

    # Best move
    best_move = current_entry["best move"]
    st.write(
        f"**Best Move:** Global({best_move['global_row']}, {best_move['global_col']}) Local({best_move['local_row']}, {best_move['local_col']})")

    # Allowed squares
    allowed = current_entry.get("allowed squares")
    if allowed:
        st.write(f"**Allowed Square:** ({allowed[0]}, {allowed[1]})")
    else:
        st.write("**Allowed Square:** Any")

    # Legal moves
    with st.expander("Legal Moves"):
        for i, move in enumerate(current_entry["legal moves"]):
            st.write(
                f"{i + 1}. Global({move['global_row']}, {move['global_col']}) Local({move['local_row']}, {move['local_col']})")

with col_right:
    st.subheader("🧠 Chain of Thought")

    # Text area for chain of thought
    chain_of_thought = st.text_area(
        "Enter reasoning for this move:",
        value=current_entry.get("chain of thought", ""),
        height=300,
        placeholder="Explain the strategic reasoning behind this move...\n\nExample:\n- Analyze the current board state\n- Identify threats and opportunities\n- Explain why this move is optimal\n- Consider future implications"
    )

    # Update button
    if st.button("✅ Update Chain of Thought", type="primary"):
        st.session_state.data[st.session_state.current_index]["chain of thought"] = chain_of_thought
        st.session_state.modified = True
        st.success("Updated! Don't forget to save.")

    # Show if modified
    if st.session_state.modified:
        st.warning("⚠️ Unsaved changes! Click 'Save' in the sidebar.")

    # Board state visualization
    with st.expander("📊 Board State (9x9 Grid)"):
        board = format_board_state(current_entry["global state"])

        # Display as text grid
        board_text = ""
        for i, row in enumerate(board):
            if i > 0 and i % 3 == 0:
                board_text += "---+---+---\n"
            row_str = ""
            for j, cell in enumerate(row):
                if j > 0 and j % 3 == 0:
                    row_str += "|"
                symbol = "." if cell == 0 else ("X" if cell == 1 else "O")
                row_str += symbol
            board_text += row_str + "\n"

        st.code(board_text)

# Statistics in sidebar
st.sidebar.header("📊 Statistics")
total_with_cot = sum(1 for entry in st.session_state.data if entry.get("chain of thought", "").strip())
st.sidebar.write(f"Completed: {total_with_cot}/{total_entries}")
st.sidebar.write(f"Remaining: {total_entries - total_with_cot}")
st.sidebar.progress(total_with_cot / total_entries if total_entries > 0 else 0)

# Keyboard shortcuts info
with st.sidebar.expander("⌨️ Keyboard Shortcuts"):
    st.write("""
    - **Tab**: Navigate between fields
    - **Ctrl/Cmd + Enter**: Submit form
    - Use navigation buttons for prev/next
    """)