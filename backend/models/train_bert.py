import os
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from transformers import Trainer, TrainingArguments
from datasets import load_dataset
import pandas as pd

# Handle path resolution
base_dir = os.path.dirname(os.path.dirname(__file__))
data_file = os.path.join(base_dir, "data", "scam_dataset_large.json")
model_output_dir = os.path.join(base_dir, "models", "scam_model")

# Use a lightweight model for CPU inference and testing
model_name = "distilbert-base-uncased"
tokenizer = DistilBertTokenizer.from_pretrained(model_name)

def extract_content(example):
    """
    Format WhatsApp-style conversational histories into a single context block.
    For single messages, just pass it through.
    """
    if example.get("type") == "conversation":
        # Join previous messages using the [SEP] token so BERT knows they are sequential
        msgs = [msg["text"] for msg in example["conversation"]]
        context = " [SEP] ".join(msgs)
        # The label of the entire conversation is dictated by the final intent message
        label = example["conversation"][-1]["label"]
        return {"processed_text": context, "label": label}
    else:
        return {"processed_text": example["text"], "label": example["label"]}

def tokenize(batch):
    return tokenizer(batch["processed_text"], padding="max_length", truncation=True, max_length=128)

def main():
    print("=" * 50)
    print("Loading Dataset for PRO LEVEL Transformer Training")
    print("=" * 50)
    
    # Load raw JSON
    dataset = load_dataset("json", data_files=data_file)
    
    # Process the conversational arrays vs single messages
    print("Flattening conversations into BERT context strings...")
    dataset = dataset.map(extract_content, remove_columns=["conversation", "type", "text"])
    
    # Split train/test
    dataset = dataset["train"].train_test_split(test_size=0.2)
    
    # Tokenize
    print("Tokenizing (this might take a minute)...")
    dataset = dataset.map(tokenize, batched=True)
    
    model = DistilBertForSequenceClassification.from_pretrained(
        model_name,
        num_labels=3 # 0: Safe, 1: Suspicious, 2: Scam
    )
    
    # If training on CPU locally, use VERY small batch size
    args = TrainingArguments(
        output_dir=model_output_dir,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        num_train_epochs=1, # Reduced to 1 for quick CPU local test
        weight_decay=0.01,
        save_strategy="epoch",
        logging_dir='./logs',
        logging_steps=10
    )
    
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"]
    )
    
    print("\nStarting Training on CPU...")
    trainer.train()
    
    # Save the final pristine model
    print(f"\nSaving final model to: {model_output_dir}")
    trainer.save_model(model_output_dir)
    tokenizer.save_pretrained(model_output_dir)
    print("Training Complete!")

if __name__ == "__main__":
    main()
