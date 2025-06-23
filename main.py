# main.py
import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import chromadb
from dotenv import load_dotenv

# --- Load Configuration and Data ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.Client()
app = FastAPI()

# Allow your future website to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all websites
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading AI knowledge base...")
collection = chroma_client.get_or_create_collection(name="n8n_workflows_web")

if collection.count() == 0:
    print("Database is empty. Populating...")
    with open('processed_workflows_v2.jsonl', 'r', encoding='utf-8') as f:
        all_data = [json.loads(line) for line in f]
    
    # We only need the name for searching
    documents = [item['name'] for item in all_data]
    metadatas = all_data
    ids = [str(i) for i in range(len(all_data))]
    
    for i in range(0, len(documents), 1000):
        collection.add(documents=documents[i:i+1000], metadatas=metadatas[i:i+1000], ids=ids[i:i+1000])
    print("Database population complete!")
else:
    print("Database already loaded.")

# --- API Logic ---
class Query(BaseModel):
    question: str

@app.post("/search")
def search_workflows(query: Query):
    print(f"Received search query: {query.question}")
    
    # Search the database
    results = collection.query(query_texts=[query.question], n_results=5)
    
    # Return the top 5 results as a clean list
    found_workflows = results['metadatas'][0]
    return {"workflows": found_workflows}

@app.get("/")
def read_root():
    return {"status": "AI search API is online"}