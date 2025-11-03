
import json
import os
from datetime import datetime, timedelta
import re
from collections import Counter

# Mock NLTK for sentiment and keyword extraction
# In a real scenario, you'd install and import nltk
# from nltk.sentiment import SentimentIntensityAnalyzer
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize

def _mock_sentiment_analyzer(text: str) -> str:
    """A mock sentiment analyzer for demonstration purposes."""
    text_lower = text.lower()
    if "amazing" in text_lower or "love" in text_lower or "perfectly" in text_lower or "recommend" in text_lower:
        return "positive"
    elif "bad" in text_lower or "hate" in text_lower or "disappointed" in text_lower:
        return "negative"
    else:
        return "neutral"

def _mock_keyword_extractor(text: str) -> list:
    """A mock keyword extractor for demonstration purposes."""
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = set(["this", "is", "a", "an", "the", "i", "it", "to", "and", "for", "with", "my", "me", "you", "not", "of", "product", "review", "in"])
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    # Return top 3 most frequent keywords
    return [word for word, count in Counter(keywords).most_common(3)]

def _get_user_account_details(user_id: str):
    """Simulate fetching user account details."""
    # In a real system, this would query a user service/database
    if user_id == "USER001":
        return {"account_creation_date": (datetime.now() - timedelta(days=60)).isoformat()} # Older user
    elif user_id == "USER002":
        return {"account_creation_date": (datetime.now() - timedelta(days=10)).isoformat()} # Newer user (potential suspicious)
    elif user_id == "USER003":
        return {"account_creation_date": (datetime.now() - timedelta(days=8)).isoformat()} # Newer user (potential suspicious)
    else:
        return {"account_creation_date": (datetime.now() - timedelta(days=1)).isoformat()} # Very new user

def _get_product_details(product_id: str):
    """Simulate fetching product details."""
    # In a real system, this would query a product catalog service/database
    if product_id == "PROD001":
        return {"product_launch_date": (datetime.now() - timedelta(days=90)).isoformat()} # Older product
    elif product_id == "PROD002":
        return {"product_launch_date": (datetime.now() - timedelta(days=7)).isoformat()} # Newer product (potential suspicious)
    elif product_id == "PROD003":
        return {"product_launch_date": (datetime.now() - timedelta(days=5)).isoformat()} # Newer product (potential suspicious)
    else:
        return {"product_launch_date": (datetime.now() - timedelta(days=30)).isoformat()} # Default new product

def enrich_review_data(input_file: str = 'data/raw_reviews.json', output_file: str = 'data/enriched_reviews.json'):
    """
    Enriches review data with reviewer account age, product launch date,
    review sentiment, length, and keywords.
    """
    print(f"[{datetime.now().isoformat()}] Starting review data enrichment...")
    reviews = []
    if os.path.exists(input_file):
        with open(input_file, 'r') as f:
            try:
                reviews = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {input_file} is empty or malformed. No reviews to enrich.")
                reviews = []
    else:
        print(f"Error: Input file {input_file} not found. Cannot enrich data.")
        return

    enriched_reviews = []
    for review in reviews:
        # Enrich with account creation date
        user_details = _get_user_account_details(review['user_id'])
        review['account_creation_date'] = user_details['account_creation_date']

        # Enrich with product launch date
        product_details = _get_product_details(review['product_id'])
        review['product_launch_date'] = product_details['product_launch_date']

        # New enrichments: sentiment, length, keywords
        review_text = review.get('review_text', '')
        review['review_sentiment'] = _mock_sentiment_analyzer(review_text)
        review['review_length'] = len(review_text)
        review['review_keywords'] = _mock_keyword_extractor(review_text)

        enriched_reviews.append(review)
        print(f"[{datetime.now().isoformat()}] Enriched review_id: {review['review_id']} with text analysis and metadata.")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(enriched_reviews, f, indent=4)

    print(f"[{datetime.now().isoformat()}] Finished review data enrichment. Total enriched reviews: {len(enriched_reviews)}")

if __name__ == '__main__':
    # Ensure raw_reviews.json exists for this to run
    # Example usage:
    # from src.data_ingestion.data_ingestion import ingest_review_data
    # ingest_review_data()
    enrich_review_data()
