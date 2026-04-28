import re
import string

def preprocess_text(text: str) -> str:
    """Preprocesses a single text document by lowercasing and removing punctuation."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Optional: basic tokenization by splitting to remove extra whitespace
    tokens = text.split()
    
    return ' '.join(tokens)
