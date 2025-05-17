# Mistral Chat Agent

A Python-based chat agent using the Mistral 7B model for creative storytelling, featuring a Tkinter UI, voice input, and chat history.

## Features
- Generate stories with sentiment-based tones (e.g., joyful, sad).
- Tkinter UI with dark mode, auto-scroll, and a searchable chat history sidebar.
- Voice input support using speech recognition.
- Runs offline for privacy and zero cost.

## Requirements
- Python 3.x
- Libraries: `tkinter`, `ctransformers`, `vaderSentiment`, `speech_recognition`
- Mistral 7B model file: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`

## Setup
1. Install dependencies: `pip install ctransformers vaderSentiment speechrecognition`
2. Place the Mistral model file in the project directory.
3. Run the script: `python mistral_chat_ui.py`

## Usage
- Enter a prompt (or use voice input) and select a word limit (100, 150, 200, 300).
- The AI generates a story, displayed in the chat window.
- Browse past chats in the sidebar.
