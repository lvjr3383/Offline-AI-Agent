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

# lvjr3383/Offline-AI-Agent

## Folders and files

| Name  | Name | Last commit message         | Last commit date |
|-------|------|-----------------------------|------------------|
|       |      |                             |                  |

# Offline AI Agents

A collection of Python-based AI agents, including a Mistral 7B-based chat agent for creative storytelling and a rules-based banking assistant, both with Tkinter UI.

## Features

- **Mistral Chat Agent**:
  - Generate stories with sentiment-based tones (e.g., joyful, sad).
  - Tkinter UI with dark mode, auto-scroll, and searchable chat history sidebar.
  - Voice input support using speech recognition.
  - Runs offline for privacy and zero cost.
- **Rules-Based Chase Assistant**:
  - Handles Chase FAQ questions with precision using a local FAQ file.
  - Tkinter UI with chat display, input field, and escalation options.
  - Runs offline with threading for performance.

## Requirements

- Python 3.x
- Libraries:
  - `tkinter` (built-in)
  - `ctransformers` (for Mistral)
  - `vaderSentiment` (for Mistral sentiment)
  - `speech_recognition` (for Mistral voice input)
- Mistral 7B model file: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (for Mistral agent)

## Setup

1. Install dependencies:
   - `pip install ctransformers vaderSentiment speechrecognition`
2. Place the Mistral model file in the project directory (for Mistral agent).
3. Run the script:
   - `python mistral_chat_ui.py` (for Mistral agent)
   - `python chase_assistant.py` (for rules-based assistant)

## Usage

- **Mistral Chat Agent**: Enter a prompt (or use voice input), select a word limit (100, 150, 200, 300), and view the story in the chat window. Browse past chats in the sidebar.
- **Rules-Based Chase Assistant**: Start a chat, ask FAQ questions, and escalate if needed. Close after 25 seconds if no input.

## About

A collection of offline AI agents for creative storytelling and banking assistance, built with Tkinter UI.

## Releases

No releases published

## Packages

No packages published

# lvjr3383/Offline-AI-Agent

## Folders and files

| Name  | Name | Last commit message         | Last commit date |
|-------|------|-----------------------------|------------------|
|       |      |                             |                  |

# Offline AI Agents

A collection of Python-based AI agents, including a Mistral 7B-based chat agent for creative storytelling and a rules-based banking assistant, both with Tkinter UI.

## Features

- **Mistral Chat Agent**:
  - Generate stories with sentiment-based tones (e.g., joyful, sad).
  - Tkinter UI with dark mode, auto-scroll, and searchable chat history sidebar.
  - Voice input support using speech recognition.
  - Runs offline for privacy and zero cost.
- **Rules-Based Chase Assistant**:
  - Handles Chase FAQ questions with precision using a local FAQ file.
  - Tkinter UI with chat display, input field, and escalation options.
  - Runs offline with threading for performance.

## Requirements

- Python 3.x
- Libraries:
  - `tkinter` (built-in)
  - `ctransformers` (for Mistral)
  - `vaderSentiment` (for Mistral sentiment)
  - `speech_recognition` (for Mistral voice input)
- Mistral 7B model file: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (for Mistral agent)

## Setup

1. Install dependencies:
   - `pip install ctransformers vaderSentiment speechrecognition`
2. Place the Mistral model file in the project directory (for Mistral agent).
3. Run the script:
   - `python mistral_chat_ui.py` (for Mistral agent)
   - `python chase_assistant.py` (for rules-based assistant)

## Usage

- **Mistral Chat Agent**: Enter a prompt (or use voice input), select a word limit (100, 150, 200, 300), and view the story in the chat window. Browse past chats in the sidebar.
- **Rules-Based Chase Assistant**: Start a chat, ask FAQ questions, and escalate if needed. Close after 25 seconds if no input.

## About

A collection of offline AI agents for creative storytelling and banking assistance, built with Tkinter UI.

## Releases

No releases published

## Packages

No packages published