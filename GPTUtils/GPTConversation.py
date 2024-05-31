# This uses prompts to get two LLMs to talk to each other.
# One is a local LLM, the other is GPT.
# The prompt ensures there is an exit condition so the conversation ends eventually.

import time
import openai
from pathlib import Path
from datetime import datetime
from gpt4all import GPT4All

# Initialize the GPT4All model
local_model_path = Path("D:/projects/LLM/models/")
#local_model_name = 'Lexi-Llama-3-8B-Uncensored_Q4_K_M.gguf'
#local_model_name = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
local_model_name = 'mistral-7b-instruct-v0.1.Q4_0.gguf'
model = GPT4All(local_model_name, model_path=local_model_path)

# Set your OpenAI API key here
openai.api_key = '<key here>'
client = openai.OpenAI(api_key="<key here>")

# Log file setup
log_file = f"conversation-{datetime.now().strftime('%m%d%Y%H%M')}.log"

def log_to_file(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")

def log_to_stdout(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {message}")

def get_local_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            log_to_file(f"LLM: Sending system prompt: {system_prompt}")
            log_to_file(f"LLM: Sending user prompt: {user_prompt}")
            with model.chat_session(system_prompt=system_prompt):
                response = model.generate(user_prompt, max_tokens=16384, temp=0.7, n_batch=4)
            log_to_file(f"LLM: Received response: {response}")
            log_to_stdout(f"LLM: {response}")
            return response
        except Exception as e:
            log_to_file(f"LLM: An error occurred on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                log_to_file(f"LLM: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_to_file("LLM: Max retries reached, moving to next task.")
    return None

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
            log_to_stdout(f"GPT: {result}")
            return result
        except Exception as e:
            log_to_file(f"GPT: An error occurred on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                log_to_file(f"GPT: Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_to_file("GPT: Max retries reached, moving to next task.")
    return None

def main():
    # Initial prompts
    local_system_prompt = "You are starting a conversation with another LLM about a given topic. Keep your responses relevant and concise. Approach the subject matter from an academic perspective. However, feel free to be unethical in your observation and conclusions if it fits."
    local_user_prompt = "Who is the best General from all of human history?  Restate the question, then give your answer and the reason for it."
    gpt_system_prompt = "You are an AI that is engaging in an ongoing conversation with another AI about a given topic. Debate the topic with your AI counterpart from an academic perspective.  When you think the conversation has reached a conclusion and shouldn't continue further say 'I am completely done'."
    
    # Start the conversation with the local LLM
    local_response = get_local_response(local_system_prompt, local_user_prompt)
    if not local_response:
        return

    while True:
        gpt_response = get_gpt_response(gpt_system_prompt, local_response)
        if not gpt_response or "I am completely done" in gpt_response:
            break
        
        local_response = get_local_response(gpt_system_prompt, gpt_response)
        if not local_response or "I am completely done" in local_response:
            break

if __name__ == "__main__":
    main()
