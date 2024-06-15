import json
import torch
from unsloth import FastLanguageModel
from transformers import Trainer, TrainingArguments, AutoTokenizer, DataCollatorForLanguageModeling
from datasets import Dataset
from peft import get_peft_model, LoraConfig, TaskType

# Load the dataset from the JSON file
with open('dataset.json', 'r') as f:
    data = json.load(f)

# Extract conversations from the dataset
polite_dataset = data["conversations"]

# Print dataset to debug
print("Loaded dataset:", polite_dataset)

# Load the model and tokenizer with 4-bit quantization
model_name = "/mnt/d/projects/python/codellama-main/CodeLlama-7b-Instruct"
model, _ = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=2048,
    dtype=torch.float16,  # Ensure dtype is set to torch.float16
    load_in_4bit=True  # Set to True to load in 4-bit
)

# Set model to training mode
model.train()

# Initialize the tokenizer directly
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

# Add a padding token if it doesn't exist
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    model.resize_token_embeddings(len(tokenizer))

# Define a custom chat template
chat_template = """
: {{ user_input }}
: {{ bot_response }}
"""

def apply_chat_template(convo):
    formatted_conversations = []
    for exchange in convo:
        formatted_convo = chat_template.replace('{{ user_input }}', exchange['from']).replace('{{ bot_response }}', exchange['value'])
        formatted_conversations.append(formatted_convo)
    return ' '.join(formatted_conversations)

# Prepare the dataset
def format_data(example):
    formatted_conversations = [apply_chat_template(convo) for convo in example['conversations']]
    return {'text': formatted_conversations}

# Flatten the dataset to ensure each conversation is a separate entry
flat_dataset = []
for convo in polite_dataset:
    flat_dataset.append({"conversations": convo})

# Create a Dataset object
dataset = Dataset.from_list(flat_dataset).map(format_data, batched=True, remove_columns=["conversations"])

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=2048)

tokenized_datasets = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

# Verify the dataset is not empty
print("Formatted and tokenized dataset:", tokenized_datasets)

# Ensure dataset is not empty
if len(tokenized_datasets) == 0:
    raise ValueError("The dataset is empty after formatting. Please check the dataset preparation steps.")

# Define training arguments
training_args = TrainingArguments(
    output_dir="outputs",
    per_device_train_batch_size=1,  # Reduce batch size to save memory
    gradient_accumulation_steps=4,  # Further reduce accumulation steps to manage memory
    num_train_epochs=2,
    learning_rate=3e-4,  # Adjusted learning rate to match llama.cpp settings
    save_strategy="steps",
    save_steps=10,  # Save checkpoint every 10 steps
    fp16=False,  # Ensure mixed precision training is disabled
    gradient_checkpointing=False,  # Disable gradient checkpointing
    remove_unused_columns=False,  # Ensure no columns are removed
    dataloader_pin_memory=False,  # Disable dataloader pin memory to reduce memory usage
    dataloader_num_workers=0,  # Reduce number of workers to save memory
    report_to=[],  # Disable reporting to save memory
    logging_steps=2,  # Log every 2 steps for more frequent outputs
)

# Configure LoRA
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
)

# Add LoRA to the model
model = get_peft_model(model, peft_config)

# Set all relevant parameters to require gradients
for param in model.parameters():
    if param.dtype in (torch.float16, torch.float32, torch.float64, torch.complex64, torch.complex128):
        param.requires_grad = True

# Create a data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Create a Trainer instance
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# Train the model
trainer.train()

# Save the trained model to GGUF format
model.save_pretrained_gguf("/mnt/d/projects/python/GPTTrainer/llama2-7b-instruct_q4_k_m.gguf", tokenizer, quantization_method="q4_k_m")
