# This application reads from cobolinfo.txt, using a delimiter to split the entries.  Note that this file has to built either manually or with another tool.
# Each section of the file contains cobol code.  This is sent to llama 3 for analysis, then two GPT requests are made to further refine the analysis before it is saved to a file.
# Langchain is used to handle the flow for the GPT responses
import time
from gpt4all import GPT4All
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Set your OpenAI API key here
openai_api_key = '<api key>'

# Initialize GPT4All model
model_path = Path.home() / '.cache' / 'gpt4all'
model_name = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
llama3_model = GPT4All(model_name, model_path=model_path)

# Function to log messages to a file
def log_to_file(message, filename="cobolconversion.log"):
    with open(filename, "a") as log_file:
        log_file.write(message + "\n")

# Define prompt templates for LangChain
gpt4_correction_template = ChatPromptTemplate.from_messages([
    ("system", "You are reviewing an analysis of COBOL code. Ensure the response is accurate, correct any errors, and improve the explanation as necessary."),
    ("human", "Original COBOL code:\n{cobol_code}\n\nInitial analysis:\n{llama3_response}")
])

gpt4_completeness_template = ChatPromptTemplate.from_messages([
    ("system", "You are evaluating the completeness of an analysis of COBOL code. Confirm whether all relevant details are included."),
    ("human", "Original COBOL code:\n{cobol_code}\n\nCorrected analysis:\n{gpt4_response}")
])

gpt4_final_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert COBOL analyst. Provide a comprehensive, self-contained, and well-structured analysis of the following COBOL code."),
    ("human", "Original COBOL code:\n{cobol_code}\n\nDetailed analysis:\n{gpt4_response}")
])

# Initialize LangChain LLMs with API key
gpt4_llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4")

# Function to interact with GPT4All model using LangChain
def get_llama3_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            log_to_file(f"Sending system prompt: {system_prompt}")
            log_to_file(f"Sending user prompt: {user_prompt}")
            print("Sending user prompt: " + user_prompt + "\n")
            with llama3_model.chat_session(system_prompt=system_prompt):
                response = llama3_model.generate(user_prompt, max_tokens=16384, temp=0.7, n_batch=4)
            print("Received response: " + response + "\n")
            log_to_file(f"Received response: {response}")
            return response
        except Exception as e:
            log_to_file(f"An error occurred on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                log_to_file(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_to_file("Max retries reached, moving to next task.")
    return None

# Function to process COBOL code chunk and write results
def analyze_and_write_results(cobol_code_chunk):
    # Step 1: Initial analysis with llama3_model
    system_prompt = "When you examine COBOL code, be sure to provide a response that indicates the order of operations, what UI elements interact with users and in what way, and detail which fields are involved and any lookups or modifications are associated with the fields."
    user_prompt = f"Please analyze the following code and give a detailed explanation of how it works. This needs to be done in enough detail that a non-COBOL developer can follow the logic: {cobol_code_chunk}"
    llama3_response = get_llama3_response(system_prompt, user_prompt)
    log_to_file(f"Llama3 Response: {llama3_response}")

    # Step 2: Correction and improvement with GPT-4 using LangChain
    gpt4_correction_prompt = gpt4_correction_template.format(cobol_code=cobol_code_chunk, llama3_response=llama3_response)
    try:
        gpt4_correction_response = gpt4_llm.invoke(gpt4_correction_prompt)
        gpt4_correction_response_content = gpt4_correction_response.content
        log_to_file(f"GPT-4 Correction Response: {gpt4_correction_response_content}")
    except Exception as e:
        log_to_file(f"Error during GPT-4 correction step: {e}")
        return

    # Step 3: Completeness check with GPT-4 using LangChain
    gpt4_completeness_prompt = gpt4_completeness_template.format(cobol_code=cobol_code_chunk, gpt4_response=gpt4_correction_response_content)
    try:
        gpt4_completeness_response = gpt4_llm.invoke(gpt4_completeness_prompt)
        gpt4_completeness_response_content = gpt4_completeness_response.content
        log_to_file(f"GPT-4 Completeness Response: {gpt4_completeness_response_content}")
    except Exception as e:
        log_to_file(f"Error during GPT-4 completeness step: {e}")
        return

    # Final decision based on completeness check
    final_response = gpt4_correction_response_content
    if "incomplete" in gpt4_completeness_response_content.lower():
        try:
            gpt4_final_prompt = gpt4_final_template.format(cobol_code=cobol_code_chunk, gpt4_response=gpt4_correction_response_content)
            final_response = gpt4_llm.invoke(gpt4_final_prompt).content
            log_to_file(f"Final GPT-4 Detailed Response: {final_response}")
        except Exception as e:
            log_to_file(f"Error during final GPT-4 detail step: {e}")
            return

    # Write the final analysis to a text file
    with open("cobol_analysis.txt", "a") as output_file:
        output_file.write(f"Original COBOL code:\n{cobol_code_chunk}\n\nFinal analysis:\n{final_response}\n")
        output_file.write("=" * 80 + "\n")

def main():
    try:
        with open("cobolinfo.txt", "r") as file:
            lines = file.readlines()
            log_to_file("Starting to process file.")
            current_code = ""

            for line in lines:
                log_to_file(f"Read line: {line.strip()}")
                if line.strip() == "###------###":
                    if current_code:  # Ensure current_code is not empty before processing
                        log_to_file(f"Processing code block: {current_code}")
                        analyze_and_write_results(current_code)
                        current_code = ""  # Reset for next block
                else:
                    current_code += line

            # Ensure the last block is processed if there's no trailing "------"
            if current_code:
                log_to_file(f"Processing final code block: {current_code}")
                analyze_and_write_results(current_code)

    except Exception as e:
        log_to_file(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
