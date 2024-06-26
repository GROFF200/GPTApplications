import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

def clean_text(text):
    """Clean the email text by removing extra spaces and new lines."""
    return text.strip().replace("\n", " ").replace("\r", "")

def log_message(message):
    """Simple logger that appends messages to a log file."""
    with open('process_log.txt', 'a') as log_file:
        log_file.write(message + '\n')

def process_emails(csv_path, model):
    """Process each email from the CSV, generate embeddings, and store them in the vector database."""
    emails_df = pd.read_csv(csv_path)
    emails_df['Body'] = emails_df['Body'].apply(clean_text)
    
    # Initialize the embedding function
    embedding_function = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    # Embeddings are computed here
    embeddings = model.encode(emails_df['Body'].tolist(), convert_to_tensor=True)
    
    # Create a list of documents with the correct key 'page_content'
    documents = [
        Document(
            page_content=row['Body'],
            metadata={
                'Subject': row['Subject'],
                'From': row['From: (Name)'],
                'To': row['To: (Name)']
            }
        )
        for index, row in emails_df.iterrows()
    ]

    # Create vector store
    vector_db = Chroma.from_documents(documents=documents, embedding=embedding_function, persist_directory='vector_db/')
    log_message("All data has been processed and the vector database is created.")

def main():
    model = SentenceTransformer('all-MiniLM-L6-v2')

    csv_directory = 'csv'
    print(f"Looking for CSV files in: {os.path.abspath(csv_directory)}")  # Shows the absolute path
    try:
        files = os.listdir(csv_directory)
        print(f"Found files: {files}")  # Lists found files
    except Exception as e:
        print(f"Error accessing directory {csv_directory}: {e}")
        return

    for filename in files:
        if filename.lower().endswith('.csv'):
            csv_path = os.path.join(csv_directory, filename)
            log_message(f"Processing file: {filename}")
            process_emails(csv_path, model)

if __name__ == "__main__":
    main()

