import tkinter as tk
from tkinter import ttk
from ctransformers import AutoModelForCausalLM
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import datetime
import random
import threading
import time
import gc  # For memory management
import speech_recognition as sr

# Set up the Tkinter window
root = tk.Tk()
root.title("Mistral Chat Agent")
root.geometry("800x500")
root.configure(bg="#F5E8C7")  # Default: Sandy beige background

# Directory to store chat history files
CHAT_DIR = "chat_history"
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# List of funny thinking messages
THINKING_MESSAGES = [
    "Diving into the cosmic soup of knowledge...",
    "Consulting the galaxy’s oldest librarian...",
    "Untangling the web of infinite thoughts...",
    "Asking the universe for a quick hint...",
    "Shuffling through the stardust of ideas..."
]

# Load the Mistral 7B model
model = AutoModelForCausalLM.from_pretrained(
    "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    model_type="mistral",
    gpu_layers=0,
    context_length=2048
)

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Model settings
CONTEXT_LENGTH = 2048
DEFAULT_WORD_COUNT = 150  # Default story length in words

# Variables for UI toggles
word_count_var = tk.StringVar(value=str(DEFAULT_WORD_COUNT))
dark_mode_var = tk.BooleanVar(value=False)
auto_scroll_var = tk.BooleanVar(value=True)
search_var = tk.StringVar()

# Dictionary to store the open state of date nodes
date_node_states = {}

# Color schemes for light and dark modes
LIGHT_COLORS = {
    "window_bg": "#F5E8C7",  # Sandy beige
    "text_bg": "#B3DCE8",    # Light ocean blue
    "text_fg": "#2A6070",    # Deep teal
    "button_bg": "white",
    "button_fg": "black"
}

DARK_COLORS = {
    "window_bg": "#2E2E2E",  # Dark gray
    "text_bg": "#4A4A4A",    # Slightly lighter gray
    "text_fg": "#E0E0E0",    # Light gray
    "button_bg": "#808080",  # Lighter gray for better contrast
    "button_fg": "#000000"   # Black for readability
}

# Current color scheme (default to light)
current_colors = LIGHT_COLORS.copy()

# Log model loading for debugging
print(f"Loaded model: Mistral 7B, Context length: {model.context_length}")

# Function to estimate token count (simplified approximation)
def estimate_token_count(text):
    return len(text) // 4 + 1

# Function to count words in a text
def count_words(text):
    words = [word for word in text.split() if word]
    return len(words)

# Function to count lines in a text
def count_lines(text):
    return len([line for line in text.splitlines() if line.strip()])

# Function to truncate text to a specific word count, preserving sonnet structure if applicable
def truncate_to_word_count(text, word_limit, is_sonnet=False):
    words = text.split()
    if len(words) <= word_limit:
        return text
    if is_sonnet:
        lines = text.splitlines()
        current_words = 0
        truncated_lines = []
        for i, line in enumerate(lines):
            line_words = len(line.split())
            # Allow the last line to complete, even if it exceeds the limit slightly
            if i == len(lines) - 1 and current_words < word_limit:
                truncated_lines.append(line)
                break
            if current_words + line_words > word_limit:
                remaining_words = word_limit - current_words
                truncated_line = " ".join(line.split()[:remaining_words])
                if truncated_line:
                    truncated_lines.append(truncated_line + "...")
                break
            truncated_lines.append(line)
            current_words += line_words
        return "\n".join(truncated_lines)
    else:
        truncated = " ".join(words[:word_limit])
        last_period = truncated.rfind(".")
        last_exclamation = truncated.rfind("!")
        last_question = truncated.rfind("?")
        last_boundary = max(last_period, last_exclamation, last_question)
        if last_boundary != -1 and last_boundary > len(truncated) // 2:
            truncated = truncated[:last_boundary + 1]
        else:
            truncated += "..."
        return truncated

# Function to toggle dark mode
def toggle_dark_mode():
    global current_colors
    if dark_mode_var.get():
        current_colors = DARK_COLORS.copy()
    else:
        current_colors = LIGHT_COLORS.copy()
    
    root.configure(bg=current_colors["window_bg"])
    main_frame.configure(bg=current_colors["window_bg"])
    side_panel.configure(bg=current_colors["window_bg"])
    chat_frame.configure(bg=current_colors["window_bg"])
    prompt_frame.configure(bg=current_colors["window_bg"])
    control_frame.configure(bg=current_colors["window_bg"])
    button_frame.configure(bg=current_colors["window_bg"])
    
    chat_display.configure(bg=current_colors["text_bg"], fg=current_colors["text_fg"])
    prompt_entry.configure(bg=current_colors["text_bg"], fg=current_colors["text_fg"], highlightbackground=current_colors["text_fg"], highlightcolor=current_colors["text_fg"])
    prompt_label.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    chat_list_label.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    disclaimer_label.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    word_count_label.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    search_label.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    word_count_display.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    
    new_chat_button.configure(bg=current_colors["button_bg"], fg=current_colors["button_fg"])
    clear_chat_button.configure(bg=current_colors["button_bg"], fg=current_colors["button_fg"])
    submit_button.configure(bg=current_colors["button_bg"], fg=current_colors["button_fg"])
    speak_button.configure(bg=current_colors["button_bg"], fg=current_colors["button_fg"])
    dark_mode_toggle.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])
    auto_scroll_toggle.configure(bg=current_colors["window_bg"], fg=current_colors["text_fg"])

# Function to analyze sentiment and determine mood
def get_sentiment_mood(text):
    sentiment = analyzer.polarity_scores(text)
    compound_score = sentiment['compound']
    if compound_score < -0.05:
        return "sad and comforting"
    elif compound_score > 0.05:
        return "joyful and uplifting"
    return None

# Function to get list of chat files
def get_chat_files():
    return sorted([f for f in os.listdir(CHAT_DIR) if f.endswith(".txt")], reverse=True)

# Function to parse timestamp from filename and extract date
def parse_chat_timestamp(filename):
    timestamp_str = filename.replace("chat_", "").replace(".txt", "")
    try:
        dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return dt, dt.strftime("%b %d, %Y %I:%M %p"), dt.strftime("%b %d, %Y")
    except ValueError:
        return None, filename, filename

# Function to extract the first prompt from a chat file (for preview)
def get_prompt_preview(filename):
    try:
        with open(os.path.join(CHAT_DIR, filename), "r") as file:
            content = file.read()
            for line in content.splitlines():
                if line.startswith("[") and "] You: " in line:
                    prompt_start = line.find("] You: ") + 7
                    prompt = line[prompt_start:].strip()
                    if len(prompt) > 30:
                        prompt = prompt[:27] + "..."
                    return prompt
        return "No prompt found"
    except Exception:
        return "Error reading file"

# Function to save current chat to a file
def save_current_chat():
    chat_content = chat_display.get("1.0", tk.END).strip()
    if chat_content:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(CHAT_DIR, f"chat_{timestamp}.txt"), "w") as file:
            file.write(chat_content)

# Function to load a chat from a file
def load_chat(event=None):
    selected = chat_tree.selection()
    if not selected:
        return
    item = selected[0]
    parent = chat_tree.parent(item)
    if not parent:
        return
    filename = chat_tree.item(item, "tags")[0]
    with open(os.path.join(CHAT_DIR, filename), "r") as file:
        chat_display.delete("1.0", tk.END)
        chat_display.insert(tk.END, file.read())
    if auto_scroll_var.get():
        chat_display.see(tk.END)

# Function to toggle date node (expand/collapse)
def toggle_date(event):
    region = chat_tree.identify_region(event.x, event.y)
    if region != "tree":
        return
    selected = chat_tree.selection()
    if not selected:
        return
    item = selected[0]
    if chat_tree.parent(item):
        return
    if chat_tree.item(item, "open"):
        chat_tree.item(item, open=False)
        date_node_states[item] = False
    else:
        chat_tree.item(item, open=True)
        date_node_states[item] = True

# Function to clear the chat display and prompt without saving
def clear_chat():
    chat_display.delete("1.0", tk.END)
    prompt_entry.delete("1.0", tk.END)

# Function to update chat history list with search filtering
def update_chat_list(*args):
    global date_node_states
    current_open_states = {}
    for item in chat_tree.get_children():
        current_open_states[chat_tree.item(item, "text")] = chat_tree.item(item, "open")
    
    for item in chat_tree.get_children():
        chat_tree.delete(item)
    
    search_term = search_var.get().lower()
    chats_by_date = {}
    for chat_file in get_chat_files():
        dt, full_timestamp, date_str = parse_chat_timestamp(chat_file)
        if dt is None:
            continue
        prompt_preview = get_prompt_preview(chat_file).lower()
        if search_term and search_term not in prompt_preview:
            continue
        if date_str not in chats_by_date:
            chats_by_date[date_str] = []
        chats_by_date[date_str].append((chat_file, prompt_preview))
    
    for date_str in sorted(chats_by_date.keys(), reverse=True):
        date_node = chat_tree.insert("", "end", text=date_str, open=current_open_states.get(date_str, False))
        for chat_file, prompt_preview in sorted(chats_by_date[date_str], key=lambda x: x[0], reverse=True):
            child_node = chat_tree.insert(date_node, "end", text=prompt_preview, tags=(chat_file,))
            chat_tree.selection_remove(child_node)
    
    date_node_states = {chat_tree.item(item, "text"): chat_tree.item(item, "open") for item in chat_tree.get_children()}

# Function to start a new chat
def new_chat():
    save_current_chat()
    chat_display.delete("1.0", tk.END)
    prompt_entry.delete("1.0", tk.END)
    update_chat_list()

# Function to handle voice input
def voice_input():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            speak_button.config(text="Listening...", state="disabled")
            root.update()
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            prompt_entry.delete("1.0", tk.END)
            prompt_entry.insert(tk.END, text)
    except sr.UnknownValueError:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Sorry, I couldn't understand the audio.\n\n")
    except sr.RequestError as e:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Error with speech recognition: {str(e)}\n\n")
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Error during voice input: {str(e)}\n\n")
    finally:
        speak_button.config(text="Speak", state="normal")
        if auto_scroll_var.get():
            chat_display.see(tk.END)
        root.update()

# Function to generate a response in a separate thread
def generate_response(event=None):
    prompt = prompt_entry.get("1.0", tk.END).strip()
    if not prompt:
        return
    try:
        word_limit = int(word_count_var.get())
        if word_limit < 50 or word_limit > 500:
            raise ValueError
    except ValueError:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Please enter a valid word count (50-500).\n\n")
        if auto_scroll_var.get():
            chat_display.see(tk.END)
        return
    is_sonnet = "sonnet" in prompt.lower()
    if is_sonnet:
        max_new_tokens = int(word_limit * 1.2) + 30
    else:
        max_new_tokens = int(word_limit * 1.33) + 50
    if is_sonnet:
        topic = prompt.lower().replace("write me a sonnet", "").replace("sonnet", "").strip()
        if not topic:
            topic = prompt
        base_prompt = f"Write a 14-line sonnet with an ABAB CDCD EFEF GG rhyme scheme, approximately {word_limit} words, describing {topic}"
    else:
        base_prompt = f"Write a {word_limit}-word story about {prompt}"
    mood = get_sentiment_mood(prompt)
    if mood:
        full_prompt = f"Write a {mood} {base_prompt}"
    else:
        full_prompt = base_prompt
    prompt_tokens = estimate_token_count(full_prompt)
    print(f"Prompt token estimate: {prompt_tokens}")
    available_tokens = CONTEXT_LENGTH - prompt_tokens
    if available_tokens <= 0:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Error: Prompt is too long for the model's context length ({CONTEXT_LENGTH} tokens).\n\n")
        prompt_entry.delete("1.0", tk.END)
        if auto_scroll_var.get():
            chat_display.see(tk.END)
        return
    adjusted_max_tokens = min(max_new_tokens, available_tokens)
    print(f"Adjusted max_new_tokens: {adjusted_max_tokens}")
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    chat_display.insert(tk.END, f"[{current_time}] You: {prompt}\n\n")
    thinking_message = random.choice(THINKING_MESSAGES)
    chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: {thinking_message}\n")
    if auto_scroll_var.get():
        chat_display.see(tk.END)
    root.update()
    submit_button.config(state="disabled")
    prompt_entry.config(state="disabled")
    speak_button.config(state="disabled")
    clear_chat_button.config(state="disabled")
    progress_bar.start()
    progress_frame.pack(pady=5)
    root.update()
    response_container = {"response": None, "error": None}
    start_time = time.time()
    def inference_thread():
        try:
            response = model(full_prompt, stream=False, max_new_tokens=adjusted_max_tokens, temperature=0.8, top_p=0.9, stop=None)
            if is_sonnet:
                attempts = 0
                while not (13 <= count_lines(response) <= 15) and attempts < 2:
                    response = model(full_prompt, stream=False, max_new_tokens=adjusted_max_tokens, temperature=0.8, top_p=0.9, stop=None)
                    attempts += 1
                if not (13 <= count_lines(response) <= 15):
                    response = "Mistral 7B: Sorry, I couldn't generate a proper sonnet (13-15 lines) after several attempts."
            response = truncate_to_word_count(response, word_limit, is_sonnet=is_sonnet)
            response_container["response"] = response
            response_tokens = estimate_token_count(response)
            response_words = count_words(response)
            print(f"Response token estimate: {response_tokens}")
            print(f"Response word count: {response_words}")
            print(f"Response length (characters): {len(response)}")
            gc.collect()
        except Exception as e:
            print(f"Error during inference: {str(e)}")
            response_container["error"] = f"Model inference failed: {str(e)}"
    thread = threading.Thread(target=inference_thread, daemon=True)
    thread.start()
    timeout = 180
    thread.join(timeout)
    elapsed_time = time.time() - start_time
    print(f"Inference took {elapsed_time:.2f} seconds")
    progress_bar.stop()
    progress_frame.pack_forget()
    if response_container["response"] is not None:
        print("Response received, displaying in chat window")
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.delete("end-2l", "end-1l")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: {response_container['response']}\n\n")
        word_count = count_words(response_container['response'])
        word_count_display.config(text=f"Word Count: {word_count}")
    elif response_container["error"]:
        print("Error occurred, displaying error in chat window")
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.delete("end-2l", "end-1l")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Error: {response_container['error']}\n\n")
    else:
        print("No response or error, displaying timeout message")
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        chat_display.delete("end-2l", "end-1l")
        chat_display.insert(tk.END, f"[{current_time}] Mistral 7B: Error: Inference timed out after {timeout} seconds.\n\n")
    if auto_scroll_var.get():
        chat_display.see(tk.END)
    root.update()
    submit_button.config(state="normal")
    prompt_entry.config(state="normal")
    speak_button.config(state="normal")
    clear_chat_button.config(state="normal")

# Create main frame for layout
main_frame = tk.Frame(root, bg=current_colors["window_bg"])
main_frame.pack(fill=tk.BOTH, expand=True)

# Create side panel for chat history
side_panel = tk.Frame(main_frame, width=200, bg=current_colors["window_bg"])
side_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

# Search bar for chat history
search_frame = tk.Frame(side_panel, bg=current_colors["window_bg"])
search_frame.pack(fill=tk.X, pady=(5, 0))

search_label = tk.Label(search_frame, text="Search Chats:", bg=current_colors["window_bg"], fg=current_colors["text_fg"])
search_label.pack(side=tk.LEFT, padx=5)

search_entry = tk.Entry(search_frame, textvariable=search_var)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
search_var.trace("w", update_chat_list)

chat_list_label = tk.Label(side_panel, text="Previous Chats:", bg=current_colors["window_bg"], fg=current_colors["text_fg"])
chat_list_label.pack(pady=(5, 5))

chat_tree = ttk.Treeview(
    side_panel,
    height=20,
    show="tree"
)
chat_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
chat_tree.bind("<Double-1>", load_chat)
chat_tree.bind("<Button-1>", toggle_date)

update_chat_list()

# Create main chat area
chat_frame = tk.Frame(main_frame, bg=current_colors["window_bg"])
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

# Create UI elements for chat
chat_display = tk.Text(
    chat_frame,
    height=20,
    wrap=tk.WORD,
    bg=current_colors["text_bg"],
    fg=current_colors["text_fg"],
    font=("Arial", 10)
)
chat_display.pack(padx=0, pady=(10, 5), fill=tk.BOTH, expand=True)
chat_display.delete("1.0", tk.END)

# Progress bar for inference
progress_frame = tk.Frame(chat_frame, bg=current_colors["window_bg"])
progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=200)
progress_bar.pack()

# Word count display
word_count_display = tk.Label(chat_frame, text="Word Count: 0", bg=current_colors["window_bg"], fg=current_colors["text_fg"])
word_count_display.pack(anchor="w", pady=(5, 0))

# Auto-scroll toggle
auto_scroll_toggle = tk.Checkbutton(
    chat_frame,
    text="Auto-Scroll",
    variable=auto_scroll_var,
    bg=current_colors["window_bg"],
    fg=current_colors["text_fg"]
)
auto_scroll_toggle.pack(anchor="w", pady=(0, 5))

# Create frame for prompt entry
prompt_frame = tk.Frame(chat_frame, bg=current_colors["window_bg"])
prompt_frame.pack(fill=tk.X, pady=(0, 5))

prompt_label = tk.Label(prompt_frame, text="Enter your prompt:", bg=current_colors["window_bg"], fg=current_colors["text_fg"])
prompt_label.pack(anchor="w")

prompt_entry = tk.Text(
    prompt_frame,
    height=3,
    bg=current_colors["text_bg"],
    fg=current_colors["text_fg"],
    relief="solid",
    borderwidth=1,
    highlightbackground=current_colors["text_fg"],
    highlightcolor=current_colors["text_fg"],
    highlightthickness=1
)
prompt_entry.pack(fill=tk.X)

# Create frame for buttons and controls
control_frame = tk.Frame(chat_frame, bg=current_colors["window_bg"])
control_frame.pack(fill=tk.X)

# Create frame for New Chat, Clear Chat, Submit, Speak buttons, and word count selector
button_frame = tk.Frame(control_frame, bg=current_colors["window_bg"])
button_frame.pack(side=tk.LEFT, pady=5)

new_chat_button = tk.Button(
    button_frame,
    text="New Chat",
    command=new_chat,
    fg=current_colors["button_fg"],
    bg=current_colors["button_bg"],
    font=("Arial", 11, "bold")
)
new_chat_button.pack(side=tk.LEFT, padx=5)

clear_chat_button = tk.Button(
    button_frame,
    text="Clear Chat",
    command=clear_chat,
    fg=current_colors["button_fg"],
    bg=current_colors["button_bg"],
    font=("Arial", 11, "bold")
)
clear_chat_button.pack(side=tk.LEFT, padx=5)

submit_button = tk.Button(
    button_frame,
    text="Submit",
    command=generate_response,
    fg=current_colors["button_fg"],
    bg=current_colors["button_bg"],
    font=("Arial", 11, "bold")
)
submit_button.pack(side=tk.LEFT, padx=5)

speak_button = tk.Button(
    button_frame,
    text="Speak",
    command=voice_input,
    fg=current_colors["button_fg"],
    bg=current_colors["button_bg"],
    font=("Arial", 11, "bold")
)
speak_button.pack(side=tk.LEFT, padx=5)

word_count_label = tk.Label(button_frame, text="Word Count:", bg=current_colors["window_bg"], fg=current_colors["text_fg"])
word_count_label.pack(side=tk.LEFT, padx=5)

word_count_menu = ttk.Combobox(
    button_frame,
    textvariable=word_count_var,
    values=["100", "150", "200", "300"],
    width=5,
    state="readonly"
)
word_count_menu.pack(side=tk.LEFT, padx=5)

# Dark mode toggle
dark_mode_toggle = tk.Checkbutton(
    control_frame,
    text="Dark Mode",
    variable=dark_mode_var,
    command=toggle_dark_mode,
    bg=current_colors["window_bg"],
    fg=current_colors["text_fg"]
)
dark_mode_toggle.pack(side=tk.RIGHT, padx=10)

# Add shortened disclaimer at the bottom
disclaimer_label = tk.Label(
    chat_frame,
    text="Offline Mistral 7B agent here! I might hallucinate—don’t ride my waves blindly, surfer!",
    font=("Arial", 9, "bold"),
    fg=current_colors["text_fg"],
    bg=current_colors["window_bg"]
)
disclaimer_label.pack(side=tk.BOTTOM, pady=5)

# Bind the Return key to the generate_response function
prompt_entry.bind("<Return>", generate_response)

# Bind window close event to save chat history
root.protocol("WM_DELETE_WINDOW", lambda: [save_current_chat(), root.destroy()])

# Start the Tkinter event loop
root.mainloop()