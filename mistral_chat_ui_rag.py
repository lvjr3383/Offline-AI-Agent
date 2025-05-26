import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import chromadb
from sentence_transformers import SentenceTransformer
import re
from ctransformers import AutoModelForCausalLM

# Initialize Mistral 7B with ctransformers (CPU-only)
mistral_model_path = os.path.expanduser("~/Documents/mistral_chat_agent/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
llm = AutoModelForCausalLM.from_pretrained(mistral_model_path, model_type="mistral", context_length=2048)

# Initialize Chroma client and embedding model
chroma_client = chromadb.Client()
model = SentenceTransformer('all-mpnet-base-v2')
collection = chroma_client.get_or_create_collection(name="salesforce_asa_docs")

# Load and process the document (same as rag_mistral.py)
def load_document(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return {"id": os.path.basename(file_path), "text": text}

def clean_text(text):
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^(Q:|A:)', '', text, flags=re.MULTILINE)
    return text.strip()

def split_text(text, max_length=100):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += " " + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def get_hf_embedding(text):
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def store_document_in_chroma(doc):
    doc_id = doc["id"]
    text = doc["text"]
    chunks = split_text(text)
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        embedding = get_hf_embedding(chunk)
        collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"source": doc_id}]
        )

# Query documents (same as rag_mistral.py)
def query_documents(question, top_k=5):
    question_embedding = get_hf_embedding(question)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    return results["documents"][0]

# Generate answer with Mistral using retrieved documents
def generate_answer_with_mistral(question, retrieved_docs):
    context = " ".join(retrieved_docs)
    prompt = f"Answer based only on the provided context. Do not add information beyond the context. Question: '{question}' Context:\n\n{context}\n\nAnswer in a friendly way: "
    response = llm(prompt, max_new_tokens=500, temperature=0.7, top_p=0.9)
    return response

# Load multiple documents at startup
doc_paths = [
    "./test_data/Salesforce ASA FAQ.txt",
    "./test_data/Salesforce Data Cloud Sandbox FAQ.txt"
]

for doc_path in doc_paths:
    if os.path.exists(doc_path):
        doc = load_document(doc_path)
        doc["text"] = clean_text(doc["text"])
        store_document_in_chroma(doc)
        print(f"Loaded and processed document: {doc['id']}")
    else:
        print(f"Document not found: {doc_path}")

# Tkinter UI
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mistral Chat Agent")
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.chat_display.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.chat_display.config(state='disabled')
        
        # Input field
        self.input_field = ttk.Entry(root, width=50)
        self.input_field.grid(row=1, column=0, padx=10, pady=5)
        self.input_field.bind("<Return>", self.send_message)
        
        # Send button
        self.send_button = ttk.Button(root, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=10, pady=5)
        
        # Exit button
        self.exit_button = ttk.Button(root, text="Exit", command=self.exit_app)
        self.exit_button.grid(row=2, column=0, columnspan=2, pady=5)

    def send_message(self, event=None):
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        
        # Display user message
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_display.config(state='disabled')
        self.input_field.delete(0, tk.END)
        
        # Check for exit condition
        if user_input.lower() in ['exit', 'quit']:
            self.exit_app()
            return
        
        # Get RAG response
        retrieved_docs = query_documents(user_input)
        response = generate_answer_with_mistral(user_input, retrieved_docs)
        
        # Display response
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"Agent: {response}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def exit_app(self):
        self.root.quit()

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()