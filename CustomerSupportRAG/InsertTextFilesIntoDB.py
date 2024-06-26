import os
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

def clean_text(text):
    """Clean the text by removing extra spaces and new lines."""
    return text.strip().replace("\n", " ").replace("\r", "")

def log_message(message):
    """Simple logger that appends messages to a log file."""
    with open('process_log.txt', 'a') as log_file:
        log_file.write(message + '\n')

def process_text_file(file_path, model):
    """Process each chunk from the text file, generate embeddings, and store them in the vector database."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    chunks = content.split('======###')
    cleaned_chunks = [clean_text(chunk) for chunk in chunks if chunk.strip()]

    # Initialize the embedding function
    embedding_function = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    # Create a list of documents
    documents = [
        Document(
            page_content=chunk,
            metadata={}
        )
        for chunk in cleaned_chunks
    ]

    # Load existing vector store or create new if doesn't exist
    vector_db = Chroma(persist_directory='vector_db/', embedding_function=embedding_function)

    # Add documents to the vector store
    vector_db.add_documents(documents)
    log_message("All data from the text file has been processed and added to the vector database.")

def main():
    model = SentenceTransformer('all-MiniLM-L6-v2')

    file_path = 'text-files/company_info.txt'
    log_message(f"Processing file: {file_path}")
    process_text_file(file_path, model)

if __name__ == "__main__":
    main()
