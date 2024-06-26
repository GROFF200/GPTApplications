import os
import openai
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer

# Set your OpenAI API key here
openai.api_key = '<enter your api key here>'
client = openai.OpenAI(api_key="<enter your api key here>")

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

# Function to interact with OpenAI GPT model
def get_gpt_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            log_to_file(f"GPT: Sending system prompt: {system_prompt}")
            log_to_file(f"GPT: Sending user prompt: {user_prompt}")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            result = response.choices[0].message.content
            log_to_file(f"GPT: Received response: {result}")
            return result
        except Exception as e:
            log_to_file(f"GPT: An error occurred on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                log_to_file(f"GPT: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_to_file("GPT: Max retries reached, moving to next task.")
    return None

# Function to summarize a document using llama3
def summarize_document(document_content, query):
    system_prompt = f"Summarize the following support related content as conscisely as possible. Compress the data as much as you can without losing the relevant details. Only keep the details relevant for this question: {query}"
    user_prompt = document_content
    log_to_file("Summarizing the following document: "+user_prompt)
    summary = get_gpt_response(system_prompt, user_prompt)
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
        print(f"Summarizing data item {i + 1}...")
        log_to_file(f"Summarizing data item {i + 1}...")
        summary = summarize_document(res.page_content, query)
        summaries.append(summary)
        log_to_file(f"Result {i + 1} - Summary: {summary}")

    # Prepare system and user prompts
    system_prompt = "You are trying to assist the user with providing support for a company that has the specified info. Provide the best possible feedback based on the data that is provided for you to analyze."
    user_prompt = f"User query: {query}\n\nRelevant summaries:\n" + "\n".join(summaries)

    print("Analyzing support data...")
    log_to_file("Analyzing support data...")

    # Get response from GPT-4
    response = get_gpt_response(system_prompt, user_prompt)
    return response

def main():
    print("I am your support assistant. Please enter your problem description:")
    while True:
        user_query = input(">> ")
        if user_query.lower() == "exit()":
            break
        log_to_file(f"User query: {user_query}")

        response = handle_user_query(user_query)
        print(f"Support Response: {response}")
        log_to_file(f"Support Response: {response}")

if __name__ == "__main__":
    main()
