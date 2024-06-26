import os
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import ChatPromptTemplate
from gpt4all import GPT4All
from pathlib import Path

# Initialize GPT4All model
model_path = Path.home() / '.cache' / 'gpt4all'
model_name = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
llama3_model = GPT4All(model_name, model_path=model_path)

# Function to log messages to a file
def log_to_file(message, filename="support.log"):
    with open(filename, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# Initialize the vector database
embedding_function = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
vector_db = Chroma(persist_directory='vector_db/', embedding_function=embedding_function)

# Function to search the vector database
def search_vector_db(query):
    results = vector_db.similarity_search(query, k=5)  # Retrieve top 5 similar documents
    return results

# Function to interact with llama3 model
def get_llama3_response(system_prompt, user_prompt):
    max_tokens = 2048
    total_prompt = system_prompt + user_prompt
    
    # Truncate the total prompt to fit within the token limit
    if len(total_prompt) > max_tokens:
        total_prompt = total_prompt[:max_tokens]
    
    with llama3_model.chat_session(system_prompt=system_prompt):
        response = llama3_model.generate(total_prompt, max_tokens=2048, temp=0.7, n_batch=4)
    return response

# Function to summarize a document using llama3
def summarize_document(document_content, query):
    system_prompt = f"Summarize the following support related content as conscisely as possible. Compress the data as much as you can without losing the relevant details. Only keep the details relevant for this question: {query}"
    user_prompt = document_content
    log_to_file("Summarizing the following document: "+user_prompt)
    summary = get_llama3_response(system_prompt, user_prompt)
    log_to_file("Retrieved following summary: "+summary)
    return summary

# Function to handle user query
def handle_user_query(query):
    print("Searching support database...")
    log_to_file("Searching support database...")
    results = search_vector_db(query)
    if not results:
        return "No relevant information found in the support database."

    # Summarize each document to fit within context length
    summaries = []
    for i, res in enumerate(results):
        print(f"Summarizing data item {i+1}...")
        log_to_file(f"Summarizing data item {i+1}...")
        summary = summarize_document(res.page_content, query)
        summaries.append(summary)
        log_to_file(f"Result {i+1} - Summary: {summary}")

     
    # Prepare system and user prompts
    system_prompt = "You are trying to assist the user with providing support for the company contained in the database. Do your best to answer the User query as accurately and as helpfully as possible."
    user_prompt = f"User query: {query}\n\nRelevant summaries:\n" + "\n".join(summaries)

    #print(f"Analyzing support data: {user_prompt}")
    log_to_file("Analyzing support data: {user_prompt}")

    # Get response from llama3
    response = get_llama3_response(system_prompt, user_prompt)
    return response

def main():
    print("I am your support assistant. Please enter your problem description:")
    while True:
        user_query = input(">> ")
        if user_query.lower() == "exit()":
            break
        log_to_file(f"User query: {user_query}")

        response = handle_user_query(user_query)
        print(f"***Support Response: {response}")
        log_to_file(f"Support Response: {response}")

if __name__ == "__main__":
    main()
