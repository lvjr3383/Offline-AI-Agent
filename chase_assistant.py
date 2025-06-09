import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import re
import threading
import queue
import logging
import time
import random
import psutil

logging.basicConfig(filename='chase_assistant.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

faq_pairs = []
model_queue = queue.Queue()
response_queue = queue.Queue()

def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        return f"Warning: High CPU usage detected ({cpu_percent}%). For best performance, please close other applications before starting the chat.\n\n"
    return ""

def initialize_models():
    global faq_pairs
    try:
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
    text = re.sub(r'[/\-]', ' ', text)  # Replace slashes and hyphens with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    return text

def query_faq(question):
    question = normalize_text(question)
    best_match = None
    best_score = 0
    for faq_question, faq_answer in faq_pairs:
        faq_question_clean = normalize_text(faq_question.split('. ', 1)[-1])
        question_words = set(question.split())
        faq_words = set(faq_question_clean.split())
        common_words = len(question_words & faq_words)
        score = common_words / max(len(question_words), len(faq_words))
        logging.debug(f"Comparing '{question}' with '{faq_question_clean}': Score = {score}")
        if score > best_score:
            best_score = score
            best_match = faq_answer
    return best_match, best_score

def generate_summary(question, rating):
    closing_phrases = ["Have a great day!", "See you next time!", "Take care!"]
    closing_phrase = random.choice(closing_phrases)
    summary = f"Thanks for chatting! I helped with your query about '{question}', and you rated the experience {rating}. {closing_phrase}"
    return summary

def generate_case_number():
    return f"CASE-{random.randint(100000, 999999)}"

def get_random_agent_name():
    agents = ["Jeff", "Andrea", "Sarah", "Michael", "Emily"]
    return random.choice(agents)

def process_query(app, user_input):
    try:
        app.chat_display.config(state='normal')
        app.chat_display.insert(tk.END, "ChaseBot: Thinking...\n")
        app.chat_display.config(state='disabled')
        app.chat_display.see(tk.END)

        critical_keywords = ['fraud', 'fraudulent', 'stolen', 'hacked', 'unauthorized']
        escalation_keywords = ['speak to someone', 'talk to support', 'need help', 'escalate']
        is_critical = any(keyword in user_input.lower() for keyword in critical_keywords)
        is_escalation = any(keyword in user_input.lower() for keyword in escalation_keywords)

        retrieved_answer, score = query_faq(user_input)
        logging.debug(f"Retrieved answer for '{user_input}': {retrieved_answer}, Score: {score}")
        confidence_threshold = 0.5

        if score >= confidence_threshold and retrieved_answer:
            response = retrieved_answer
            response = f"{response}\n\nIs your question answered? (Yes/No)"
            app.current_state = "help_check"
            response_queue.put((response, "answered"))
            return

        if is_critical or is_escalation:
            response = "I see this might need human assistance. Is this urgent or not urgent?"
            app.current_state = "urgency_check"
        else:
            response = "Apologies, can’t help with that and would recommend human involvement."
            response = f"{response}\n\nIs your question answered? (Yes/No)"
            app.current_state = "help_check"
        response_queue.put((response, "answered"))
    except Exception as e:
        logging.error(f"Error in process_query: {str(e)}")
        response_queue.put(("Error occurred while processing your request.", "answered"))

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
        self.current_question = None
        self.state = "initial"
        self.current_state = None
        self.needs_human = False
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
        if self.state not in ["asking", "help_check", "more_questions", "urgency_check", "rating"]:
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

        if self.state == "asking":
            self.current_question = user_input
            threading.Thread(target=process_query, args=(self, user_input), daemon=True).start()
            self.response_start_time = time.time()
            self.check_response()

        elif self.state == "help_check":
            if user_input.lower() in ['yes', 'y']:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "ChaseBot: Do you have any more questions I can answer? (Yes/No)\n\n")
                self.chat_display.config(state='disabled')
                self.state = "more_questions"
            else:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "ChaseBot: It looks like human involvement is necessary. Is this urgent or not urgent?\n\n")
                self.chat_display.config(state='disabled')
                self.state = "urgency_check"
            self.chat_display.see(tk.END)

        elif self.state == "more_questions":
            if user_input.lower() in ['yes', 'y']:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "ChaseBot: Great! Please go ahead with your next question.\n\n")
                self.chat_display.config(state='disabled')
                self.state = "asking"
            else:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "ChaseBot: How did I do? Positive, Neutral, or Negative?\n\n")
                self.chat_display.config(state='disabled')
                self.state = "rating"
            self.chat_display.see(tk.END)

        elif self.state == "urgency_check":
            non_urgent = re.search(r'not\s+urgent|non\s?-?\s?urgent', user_input.lower())
            urgent = 'urgent' in user_input.lower() and not non_urgent
            if non_urgent:
                case_number = generate_case_number()
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, f"ChaseBot: I've created a case for you—{case_number}. A human agent will follow up within 1-2 business days.\n\n")
                self.chat_display.insert(tk.END, "ChaseBot: How did I do? Positive, Neutral, or Negative?\n\n")
                self.chat_display.config(state='disabled')
                self.state = "rating"
            elif urgent:
                agent_name = get_random_agent_name()
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, f"ChaseBot: Since this is urgent, I’ll connect you to a human agent. You are now with {agent_name}. They'll assist you shortly!\n\n")
                self.chat_display.insert(tk.END, "ChaseBot: How did I do? Positive, Neutral, or Negative?\n\n")
                self.chat_display.config(state='disabled')
                self.state = "rating"
            else:
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "ChaseBot: I didn’t catch that. Please let me know if it’s urgent or not urgent.\n\n")
                self.chat_display.config(state='disabled')
                self.state = "urgency_check"
            self.chat_display.see(tk.END)

        elif self.state == "rating":
            rating = user_input.capitalize()
            if rating not in ['Positive', 'Negative', 'Neutral']:
                rating = "Not provided"
            summary = generate_summary(self.current_question, rating)
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"ChaseBot: {summary}\n\n")
            self.chat_display.config(state='disabled')
            self.state = "ended"
            self.input_field.config(state='disabled')
            self.send_button.config(state='disabled')
            self.chat_display.see(tk.END)
            self.root.after(15000, self.exit_app)

    def check_response(self):
        try:
            response, action = response_queue.get_nowait()
            self.chat_display.config(state='normal')
            self.chat_display.delete("end-2l", tk.END)
            self.chat_display.insert(tk.END, f"ChaseBot: {response}\n\n")
            self.chat_display.config(state='disabled')
            self.state = self.current_state
            self.chat_display.see(tk.END)
        except queue.Empty:
            if time.time() - self.response_start_time > 120:
                self.chat_display.config(state='normal')
                self.chat_display.delete("end-2l", tk.END)
                self.chat_display.insert(tk.END, "ChaseBot: I’m struggling to respond—let’s get a human to help!\n\nChaseBot: Is this urgent or not urgent?\n\n")
                self.chat_display.config(state='disabled')
                self.state = "urgency_check"
                self.chat_display.see(tk.END)
                return
            self.root.after(100, self.check_response)

    def exit_app(self):
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()