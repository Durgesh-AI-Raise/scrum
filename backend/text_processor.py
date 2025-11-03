import re
import string

def clean_text(text: str) -> str:
    """
    Performs basic text cleaning:
    - Removes HTML tags
    - Converts to lowercase
    - Removes punctuation
    - Removes extra whitespaces
    """
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    # Remove extra whitespaces and strip
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_text(text: str) -> list[str]:
    """
    Splits text into words using simple whitespace tokenization.
    """
    return text.split()

if __name__ == '__main__':
    test_text = "<h3>Hello, World!</h3> This is a *test* with 123 numbers!!! spam-text"
    cleaned = clean_text(test_text)
    tokens = tokenize_text(cleaned)
    print(f"Original: {test_text}")
    print(f"Cleaned: {cleaned}")
    print(f"Tokens: {tokens}")
