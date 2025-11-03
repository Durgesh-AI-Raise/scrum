# src/text_preprocessing.py

import re
# from nltk.corpus import stopwords
# from nltk.stem import PorterStemmer
# from nltk.tokenize import word_tokenize # Placeholder for future use

# Initialize NLTK components (download if not present)
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')

# stop_words = set(stopwords.words('english'))
# ps = PorterStemmer()

def clean_text(text):
    """
    Performs basic cleaning on text:
    - Converts to lowercase
    - Removes punctuation and special characters
    - Removes extra whitespace
    """
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove mentions and hashtags
    text = re.sub(r'@\w+|#\w+', '', text)
    # Remove punctuation and numbers
    text = re.sub(r'[^a-z\s]', '', text) # Keep only letters and spaces
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_text(text):
    """
    Tokenizes cleaned text into a list of words.
    """
    # For this sprint, a simple split is sufficient.
    # In future, NLTK's word_tokenize can be used.
    return text.split()

def preprocess_review_text(review_text):
    """
    Orchestrates the text pre-processing steps.
    """
    if not isinstance(review_text, str) or not review_text.strip():
        return [] # Return empty list for invalid or empty input

    cleaned_text = clean_text(review_text)
    tokens = tokenize_text(cleaned_text)

    # Future: apply stemming/lemmatization and stop word removal
    # tokens = [ps.stem(word) for word in tokens if word not in stop_words]

    return tokens

if __name__ == '__main__':
    sample_text_1 = "This is an AMAZING product! I absolutely LOVE it. #bestbuy @amazon greatdeal https://example.com"
    sample_text_2 = "Worst. Product. Ever!!! So disappointing. 123"
    sample_text_3 = "   Hello world.  "
    sample_text_4 = ""
    sample_text_5 = 123 # Non-string input

    print(f"Original 1: {sample_text_1}")
    print(f"Processed 1: {preprocess_review_text(sample_text_1)}")
    print(f"Original 2: {sample_text_2}")
    print(f"Processed 2: {preprocess_review_text(sample_text_2)}")
    print(f"Original 3: {sample_text_3}")
    print(f"Processed 3: {preprocess_review_text(sample_text_3)}")
    print(f"Original 4: '{sample_text_4}'")
    print(f"Processed 4: {preprocess_review_text(sample_text_4)}")
    print(f"Original 5: {sample_text_5}")
    print(f"Processed 5: {preprocess_review_text(sample_text_5)}")
