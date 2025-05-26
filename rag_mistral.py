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
model = SentenceTransformer('all-MiniLM-L6-v2')

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

def store_document_in_chroma(doc, collection_name="salesforce_asa_docs"):
    collection = chroma_client.get_or_create_collection(name=collection_name)
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
    return collection

def query_documents(question, collection, top_k=5):
    question_embedding = get_hf_embedding(question)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    return results["documents"][0]

def generate_answer_with_mistral(question, retrieved_docs):
    context = " ".join(retrieved_docs)
    prompt = f"Hey there! You asked: '{question}' Here's what I found in the Salesforce ASA FAQ:\n\n{context}\n\nBased on this, let me answer in a friendly way: "
    response = llm(prompt, max_new_tokens=500, temperature=0.7, top_p=0.9)
    return response

# Load and process the document
doc_path = "./test_data/Salesforce ASA FAQ.txt"
doc = load_document(doc_path)
doc["text"] = clean_text(doc["text"])
collection = store_document_in_chroma(doc)
print(f"Loaded and processed document: {doc['id']}")

# Main loop for querying
while True:
    question = input("Ask a question (or type 'exit' to quit): ")
    if question.lower() in ['exit', 'quit']:
        break
    retrieved_docs = query_documents(question, collection)
    answer = generate_answer_with_mistral(question, retrieved_docs)
    print(f"Question: {question}")
    print(f"Answer: {answer}")