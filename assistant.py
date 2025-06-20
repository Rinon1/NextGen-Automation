## --- This is the full, corrected content for assistant.py ---

import os
import json
from openai import OpenAI
import chromadb
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OpenAI API key not found. Please set it in a .env file.")

client = OpenAI()
chroma_client = chromadb.Client()

DATA_FILE = 'processed_workflows_v2.jsonl'
COLLECTION_NAME = 'n8n_workflows'
EMBEDDING_MODEL = "text-embedding-3-small"


def create_and_load_database():
    print("Initializing vector database...")
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    if collection.count() > 0:
        print(f"Database '{COLLECTION_NAME}' is already loaded with {collection.count()} items. Skipping population.")
        return collection

    print(f"Database is empty. Populating from '{DATA_FILE}'... (This might take a moment)")
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        workflow_data = [json.loads(line) for line in f]

    documents = []
    metadatas = []
    ids = []

    for i, item in enumerate(workflow_data):
        # ## --- FIX IS HERE --- ##
        # We must convert the 'nodes' list into a single string for ChromaDB.
        if 'nodes' in item and isinstance(item['nodes'], list):
            item['nodes'] = ", ".join(item['nodes'])
        # ## ----------------- ##

        content = f"Workflow Name: {item['name']}\nDescription: {item['description']}\nNodes: {item['nodes']}"
        documents.append(content)
        metadatas.append(item)
        ids.append(str(i))

    batch_size = 1000
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        print(f"Creating embeddings for batch {i//batch_size + 1}...")
        response = client.embeddings.create(input=batch_docs, model=EMBEDDING_MODEL)
        embeddings = [embedding.embedding for embedding in response.data]
        
        print("Adding batch to the database...")
        collection.add(
            embeddings=embeddings,
            documents=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

    print(f"Database population complete! Total items: {collection.count()}")
    return collection


def query_assistant(question: str, collection):
    print("\nFinding relevant workflows...")
    results = collection.query(
        query_texts=[question],
        n_results=5
    )
    relevant_workflows = results['metadatas'][0]
    
    context = "Here are the most relevant workflows found in the library:\n\n"
    for i, wf in enumerate(relevant_workflows):
        context += f"--- Workflow {i+1} ---\n"
        context += f"Name: {wf['name']}\n"
        context += f"File: {os.path.basename(wf['source_file'])}\n"
        context += f"Description: {wf['description']}\n\n"
    
    system_prompt = "You are 'AutomationFlow AI', a helpful assistant that helps users find the perfect n8n automation workflow from a private library. Be friendly, concise, and helpful. Base your answer STRICTLY on the context provided."
    user_prompt = f"""{context}Based on the workflows provided above, please answer my question: '{question}'"""

    print("Generating an answer with GPT-4o...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


# --- Main execution block ---
if __name__ == "__main__":
    db_collection = create_and_load_database()
    
    print("\n--- AutomationFlow AI Assistant is Ready! ---")
    print("Ask me anything about the workflows (or type 'exit' to quit).")
    
    while True:
        user_question = input("\n> ")
        if user_question.lower() == 'exit':
            break
        
        answer = query_assistant(user_question, db_collection)
        print(f"\nAssistant: {answer}")