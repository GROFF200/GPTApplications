from gpt4all import GPT4All

# Initialize the model
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Start a chat session with the model
with model.chat_session():
    # Ask the model a question
    response = model.generate(prompt="What are the current trends in the stock market?", temp=0.7)
    # Print the response
    print(response)
