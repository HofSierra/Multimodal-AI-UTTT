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
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""


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


def format_board_compact(global_state):
    """Format board state into compact text representation."""
    board = format_board_state(global_state)
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
    return board_text


def generate_prompt(current_entry):
    """Generate optimized prompt for Gemini - concise strategic analysis only."""
    # Format board state
    board_text = format_board_compact(current_entry["global state"])

    # Get player info
    player = current_entry['player']
    player_symbol = 'X' if player == 1 else 'O'

    # Get best move
    best_move = current_entry["best move"]
    gr, gc = best_move['global_row'], best_move['global_col']
    lr, lc = best_move['local_row'], best_move['local_col']

    # Get allowed squares
    allowed = current_entry.get("allowed squares")
    allowed_str = f"({allowed[0]}, {allowed[1]})" if allowed else "Any"

    # Optimized prompt - prevents board redrawing and enforces word limit
    prompt = f"""Ultimate Tic-Tac-Toe Strategic Analysis

Board State:
{board_text}

Player: {player} ({player_symbol})
Best Move: Global({gr}, {gc}) Local({lr}, {lc})
Allowed Square: {allowed_str}

STRICT REQUIREMENTS:
- Write EXACTLY 50-80 words
- Do NOT redraw or describe the board state
- Explain WHY this move at Global({gr},{gc}) Local({lr},{lc}) is optimal
- State OFFENSIVE strategy: What does it achieve?
- State DEFENSIVE strategy: What does it prevent/block?
- Use coordinates in your explanation
- Be direct and concise

Strategic Analysis:"""

    return prompt


def get_gemini_suggestion(prompt, api_key):
    """Get suggestion from Gemini API."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


# Load data
if not st.session_state.data:
    st.session_state.data = load_data()

# Title
st.title("🎮 Ultimate Tic-Tac-Toe Chain of Thought Editor with Gemini")

# Sidebar - API Key
st.sidebar.header("🔑 Gemini API Configuration")
st.session_state.api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=st.session_state.api_key,
    type="password",
    help="Enter your Google Gemini API key"
)

if st.session_state.api_key:
    st.sidebar.success("✅ API Key configured")
else:
    st.sidebar.warning("⚠️ Please enter your API key")

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
        st.warning("Image not found")

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

    # Chain of Thought section
    st.divider()

    col_gen, col_auto = st.columns([3, 1])

    with col_gen:
        if st.button("🤖 Generate with Gemini", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Please enter your Gemini API Key in the sidebar")
            else:
                with st.spinner("Generating chain of thought..."):
                    prompt = generate_prompt(current_entry)
                    suggestion = get_gemini_suggestion(prompt, st.session_state.api_key)
                    st.session_state.data[st.session_state.current_index]["chain of thought"] = suggestion
                    st.session_state.modified = True
                    st.rerun()

    with col_auto:
        if st.button("⚡ Auto-fill Empty", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Please enter API Key")
            else:
                empty_indices = [i for i, e in enumerate(st.session_state.data)
                                 if not e.get("chain of thought", "").strip()]

                if not empty_indices:
                    st.info("All entries have chain of thought!")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, i in enumerate(empty_indices):
                        status_text.text(f"Processing {idx + 1}/{len(empty_indices)}...")
                        prompt = generate_prompt(st.session_state.data[i])
                        suggestion = get_gemini_suggestion(prompt, st.session_state.api_key)
                        st.session_state.data[i]["chain of thought"] = suggestion
                        progress_bar.progress((idx + 1) / len(empty_indices))

                    st.session_state.modified = True
                    status_text.text("Done!")
                    st.success(f"Generated {len(empty_indices)} chain of thoughts!")
                    st.rerun()

    # Edit chain of thought
    current_cot = current_entry.get("chain of thought", "")
    new_cot = st.text_area(
        "Edit Chain of Thought",
        value=current_cot,
        height=150,
        help="Edit or review the generated chain of thought"
    )

    if new_cot != current_cot:
        st.session_state.data[st.session_state.current_index]["chain of thought"] = new_cot
        st.session_state.modified = True
        st.info("Modified (remember to save)")

    # Show prompt preview
    with st.expander("🔍 View Gemini Prompt"):
        st.code(generate_prompt(current_entry), language=None)

    # Show if modified
    if st.session_state.modified:
        st.warning("⚠️ Unsaved changes! Click 'Save' in the sidebar.")

    # Board state visualization
    with st.expander("📊 Board State (9x9 Grid)"):
        st.code(format_board_compact(current_entry["global state"]))

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