#Used to test responsiveness of local API server if one is running
#This usually works with properly configured GPT4All and llamacpp servers
import requests
import json

def send_request_to_server(system_prompt, user_prompt):
    server_url = "http://127.0.0.1:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "Llama 3 Instruct",  # or the appropriate model name you are using
        "max_tokens": 16438,  # Adjust the max tokens as necessary
        "temperature": 0.7,  # Optional, adjust as needed
        "top_p": 0.9,       # Optional, adjust as needed
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    response = requests.post(server_url, headers=headers, json=payload)
    response_json = response.json()  # parse the JSON response
    print("response text:", response.text)
    if 'choices' in response_json and response_json['choices']:
        # Get the content from the first choice in the response
        return response_json['choices'][0]['message']['content']
    else:
        return "No response or invalid response format"

# Define your prompts here
system_prompt = "This is a test application. You need to give a valid response, but not a lenghty one."
user_prompt = "I am testing a service that asks you questions.  Is it working?"
# Send the request and print the response
print("Sending request to API server...");
response = send_request_to_server(system_prompt, user_prompt)
print("Response from the API server:")
print(response)
