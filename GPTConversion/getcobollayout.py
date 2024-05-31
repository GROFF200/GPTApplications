import time
import openai
from openai import OpenAI

# Set your OpenAI API key here
openai.api_key = '<key here?'

client = openai.OpenAI(api_key="<key here>")


def get_gpt_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            log_to_file(f"Sending system prompt: {system_prompt}")
            log_to_file(f"Sending user prompt: {user_prompt}")
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",  # Or "gpt-4" depending on your subscription
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            # Correct way to access response based on object properties
            result = response.choices[0].message.content
            log_to_file(f"Received response: {result}")
            return result
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

def main():
    dependencies_description = ""
    main_subroutine_code = ""
    is_subroutine_section = False
    current_code = ""

    try:
        with open("cobolinfo.txt", "r") as file:
            lines = file.readlines()
            log_to_file("Starting to process file.")
            for line in lines:
                log_to_file(f"Read line: {line.strip()}")
                if "SUBROUTINE:" in line:
                    is_subroutine_section = True
                    continue

                if is_subroutine_section:
                    main_subroutine_code += line
                else:
                    if line.strip() == "------":
                        if current_code:
                            log_to_file(f"Processing code block: {current_code}")
                            system_prompt = "Generate a concise description of this COBOL dependency, detailing its functionality and fields."
                            user_prompt = f"Analyze the following COBOL dependency code: {current_code} Describe what it does, list all fields it interacts with, and any notable actions."
                            response = get_gpt_response(system_prompt, user_prompt)
                            if response is not None:
                                dependencies_description += response + " "
                                log_to_file(f"Processed dependency: {response}")
                            else:
                                log_to_file("Received no response for dependency, skipping.")
                            current_code = ""
                    else:
                        current_code += line

        # Process main subroutine
        if main_subroutine_code:
            log_to_file(f"Processing main subroutine code: {main_subroutine_code}")
            system_prompt = "Generate a detailed layout of the user interface for the given COBOL subroutine. Include all fields, their positions, and actions."
            user_prompt = f"Here is a COBOL subroutine along with descriptions of its dependencies. {dependencies_description} Analyze the subroutine: {main_subroutine_code} Generate a structured layout of the user interface that includes all fields, their screen positions, and interactions described."
            response = get_gpt_response(system_prompt, user_prompt)
            if response:
                log_to_file(f"Processed main subroutine with layout: {response}")
            else:
                log_to_file("Received no response for main subroutine, cannot proceed with layout generation.")

    except Exception as e:
        log_to_file(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
