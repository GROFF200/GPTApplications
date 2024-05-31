import time
from gpt4all import GPT4All
from pathlib import Path

model_path = Path.home() / '.cache' / 'gpt4all'
model_name = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'

# Initialize the GPT4All model
model = GPT4All(model_name, model_path=model_path)

def get_gpt_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            log_to_file(f"Sending system prompt: {system_prompt}")
            log_to_file(f"Sending user prompt: {user_prompt}")
            print("Sending user prompt: "+user_prompt+"\n")
            with model.chat_session(system_prompt=system_prompt):
                response = model.generate(user_prompt, max_tokens=16384, temp=0.7, n_batch=4)
            print("Received response: "+response+"\n")
            log_to_file(f"Received response: {response}")
            #log_json_response(response)  # Call to log response to separate file
            return response
        except Exception as e:
            log_to_file(f"An error occurred on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                log_to_file(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_to_file("Max retries reached, moving to next task.")
    return None

def log_to_file(message):
    with open("cobolconversion.log", "a") as log_file:
        log_file.write(message + "\n")

def log_json_response(response):
    """ Log the JSON LLM response to a separate file. """
    with open("cobol_layout_json.log", "a") as log_file:
        log_file.write(response + "\n------\n")

def main():
    try:
        with open("cobolinfo.txt", "r") as file:
            lines = file.readlines()
            log_to_file("Starting to process file.")
            current_code = ""
            is_subroutine_section = False

            for line in lines:
                log_to_file(f"Read line: {line.strip()}")
                if "SUBROUTINE:" in line:
                    is_subroutine_section = True
                    continue

                if line.strip() == "------":
                    if current_code:  # Ensure current_code is not empty before processing
                        log_to_file(f"Processing code block: {current_code}")
                        system_prompt = "When you examine COBOL code, be sure to provide a response that indicates the order of operations, what UI elements interact with users and in what way, and detail which fields are involved and any lookups or modifications are associated with the fields."

                        user_prompt = f"Please analyze the following code and give a detailed explanation of how it works.  This needs to be done in enough detail that a non-COBOL developer can follow the logic: {current_code}"
                        get_gpt_response(system_prompt, user_prompt)
                    current_code = ""
                elif is_subroutine_section:
                    current_code += line
                else:
                    current_code += line

    except Exception as e:
        log_to_file(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
