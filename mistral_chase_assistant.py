import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from ctransformers import AutoModelForCausalLM
import re
import threading
import queue
import logging
import time
import random
import psutil

logging.basicConfig(filename='chase_assistant.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

llm = None
faq_pairs = []
model_queue = queue.Queue()
response_queue = queue.Queue()

def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        return f"Warning: High CPU usage detected ({cpu_percent}%). For best performance, please close other applications before starting the chat.\n\n"
    return ""

def initialize_models():
    global llm, faq_pairs
    try:
        mistral_model_path = os.path.expanduser("~/Documents/mistral_chat_agent/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        if not os.path.exists(mistral_model_path):
            raise FileNotFoundError(f"Mistral model file not found at {mistral_model_path}")
        llm = AutoModelForCausalLM.from_pretrained(mistral_model_path, model_type="mistral", context_length=128)
        logging.info("Loaded Mistral 7B model")

        faq_path = "./Chase_FAQ/Chase Banking FAQ.txt"
        if os.path.exists(faq_path):
            with open(faq_path, "r", encoding="utf-8") as f:
                faq_text = f.read()
            faq_pairs.extend(parse_faq(faq_text))
            logging.info(f"Loaded and parsed FAQ: {len(faq_pairs)} question-answer pairs")
            logging.debug(f"FAQ pairs: {faq_pairs}")
        else:
            raise FileNotFoundError(f"FAQ file not found at {faq_path}")

        model_queue.put(("success", None))
    except Exception as e:
        logging.error(f"Error loading models: {str(e)}")
        model_queue.put(("error", str(e)))

def parse_faq(text):
    entries = re.split(r'(?=\d+\.\s)', text)[1:]
    faq_pairs = []
    for entry in entries:
        entry = entry.strip()
        if entry:
            match = re.match(r'(\d+\.\s+[^?]+\?)\s+(.+)', entry, re.DOTALL)
            if match:
                question = match.group(1).strip()
                answer = match.group(2).strip()
                faq_pairs.append((question, answer))
    return faq_pairs

def normalize_text(text):
    text = text.lower().strip('?')
    text = re.sub(r'[/\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def query_faq(question):
    question = normalize_text(question)
    best_match = None
    best_score = 0
    best_question = None
    for faq_question, faq_answer in faq_pairs:
        faq_question_clean = normalize_text(faq_question.split('. ', 1)[-1])
        question_words = set(question.split())
        faq_words = set(faq_question_clean.split())
        common_words = len(question_words & faq_words)
        score = common_words / max(len(question_words), len(faq_words))
        logging.debug(f"Comparing '{question}' with '{faq_question_clean}': Intersection = {question_words & faq_words}, Score = {score}")
        if score > best_score:
            best_score = score
            best_match = faq_answer
            best_question = faq_question_clean
    logging.debug(f"Best FAQ match for '{question}': '{best_question}' with score {best_score}")
    return best_match, best_score

def generate_mistral_response(question, faq_answer=None):
    try:
        if faq_answer:
            prompt = f"Rephrase this answer in a friendly, conversational tone (max 50 words) and end with 'Thank you!': '{faq_answer}'"
            response = llm(prompt, max_new_tokens=50, temperature=0.3, top_p=0.9, timeout=7)
            logging.debug(f"Mistral 7B response: {response}")
            if response and not re.search(r"subject:|hello \[customer\]|space|moon|teleport", response.lower()):
                return response
            return f"{faq_answer} Thank you!"
        else:
            action = random.choice(["case", "agent"])
            if action == "case":
                case_number = f"CASE-{random.randint(100000, 999999)}"
                prompt = f"Generate a friendly message (max 50 words) saying human intervention is needed for '{question}', create a case '{case_number}', and end with 'Thank you!'"
            else:
                agent_name = random.choice(["Jeff", "Andrea", "Sarah", "Michael", "Emily"])
                prompt = f"Generate a friendly message (max 50 words) saying human intervention is needed for '{question}', route to agent '{agent_name}', and end with 'Thank you!'"
            response = llm(prompt, max_new_tokens=50, temperature=0.3, top_p=0.9, timeout=7)
            logging.debug(f"Mistral 7B response: {response}")
            if response and not re.search(r"subject:|hello \[customer\]|space|moon|teleport", response.lower()):
                return response
    except Exception as e:
        logging.error(f"Mistral 7B error: {str(e)}")
    if not faq_answer:
        return "I’m sorry, I can’t assist with that. Thank you!"
    return f"{faq_answer} Thank you!"

def process_query(app, user_input):
    try:
        app.chat_display.config(state='normal')
        app.chat_display.insert(tk.END, "ChaseBot: Thinking...\n")
        app.chat_display.config(state='disabled')
        app.chat_display.see(tk.END)

        retrieved_answer, score = query_faq(user_input)
        logging.debug(f"Retrieved answer for '{user_input}': {retrieved_answer}, Score: {score}")
        confidence_threshold = 0.4  # Lowered from 0.5 to 0.4

        if score >= confidence_threshold and retrieved_answer:
            response = generate_mistral_response(user_input, retrieved_answer)
        else:
            response = generate_mistral_response(user_input)

        response_queue.put((response, "answered"))
    except Exception as e:
        logging.error(f"Error in process_query: {str(e)}")
        response_queue.put(("I’m sorry, I can’t assist with that. Thank you!", "answered"))

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chase Banking Assistant")
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.chat_display.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.chat_display.config(state='disabled')
        self.start_button = ttk.Button(root, text="Start Chat", command=self.start_chat)
        self.start_button.grid(row=1, column=0, columnspan=2, pady=5)
        self.input_field = ttk.Entry(root, width=50, state='disabled')
        self.input_field.grid(row=2, column=0, padx=10, pady=5)
        self.send_button = ttk.Button(root, text="Send", command=self.send_message, state='disabled')
        self.send_button.grid(row=2, column=1, padx=10, pady=5)
        self.exit_button = ttk.Button(root, text="Exit", command=self.exit_app, state='disabled')
        self.exit_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.state = "initial"
        self.start_button.config(state='disabled')
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "Get ready! ChaseBot is powering up to assist you with all your banking needs…\n")
        self.chat_display.config(state='disabled')
        threading.Thread(target=initialize_models, daemon=True).start()
        self.load_start_time = time.time()
        self.check_models_loaded()

    def check_models_loaded(self):
        try:
            result = model_queue.get_nowait()
            if result[0] == "error":
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, f"Error: Unable to load the assistant. Please try again later. (Details: {result[1]})\n\n")
                self.chat_display.config(state='disabled')
                self.exit_button.config(state='normal')
                return
            resource_warning = check_system_resources()
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, resource_warning + "ChaseBot: Is ready! Click 'Start Chat' to begin.\n\n")
            self.chat_display.config(state='disabled')
            self.start_button.config(state='normal')
            self.exit_button.config(state='normal')
        except queue.Empty:
            if time.time() - self.load_start_time > 30:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "Error: Loading timed out. Please try again later.\n\n")
                self.chat_display.config(state='disabled')
                self.exit_button.config(state='normal')
                return
            self.root.after(100, self.check_models_loaded)

    def start_chat(self):
        self.state = "asking"
        self.start_button.config(state='disabled')
        self.input_field.config(state='normal')
        self.send_button.config(state='normal')
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "ChaseBot: Hi, I’m ChaseBot, your banking assistant! I can help with account questions, deposits, and more.\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def send_message(self, event=None):
        if self.state != "asking":
            return
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"You: {user_input}\n\n")
        self.chat_display.config(state='disabled')
        self.input_field.delete(0, tk.END)
        self.chat_display.see(tk.END)

        if user_input.lower() in ['exit', 'quit']:
            self.exit_app()
            return

        threading.Thread(target=process_query, args=(self, user_input), daemon=True).start()
        self.response_start_time = time.time()
        self.check_response()

    def check_response(self):
        try:
            response, action = response_queue.get_nowait()
            self.chat_display.config(state='normal')
            self.chat_display.delete("end-2l", tk.END)
            self.chat_display.insert(tk.END, f"ChaseBot: {response}\n\n")
            self.chat_display.config(state='disabled')
            self.state = "ended"
            self.input_field.config(state='disabled')
            self.send_button.config(state='disabled')
            self.chat_display.see(tk.END)
            self.root.after(25000, self.exit_app)
        except queue.Empty:
            if time.time() - self.response_start_time > 120:
                self.chat_display.config(state='normal')
                self.chat_display.delete("end-2l", tk.END)
                self.chat_display.insert(tk.END, "ChaseBot: I’m sorry, I can’t assist with that. Thank you!\n\n")
                self.chat_display.config(state='disabled')
                self.state = "ended"
                self.input_field.config(state='disabled')
                self.send_button.config(state='disabled')
                self.chat_display.see(tk.END)
                self.root.after(25000, self.exit_app)
                return
            self.root.after(100, self.check_response)

    def exit_app(self):
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()