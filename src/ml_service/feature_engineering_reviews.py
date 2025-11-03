# src/ml_service/feature_engineering_reviews.py
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Consumers and Producers
consumer = KafkaConsumer(
    'validated_reviews',
    bootstrap_servers=['kafka:9092'],
    group_id='review_feature_engineering_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Initialize TF-IDF Vectorizer (this should ideally be trained offline and loaded)
# For a baseline, we can fit on a sample of data or load a pre-trained one.
# For real-time, it will be loaded at service start.
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
# Assume 'fitted_tfidf_vectorizer.pkl' is loaded from a persistent storage in production
# For now, a placeholder or a simple fit on first few reviews

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    # Convert to lowercase, remove punctuation, etc.
    return text.lower() # Basic preprocessing

def hash_ip_address(ip_address):
    if ip_address:
        return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()
    return None

def feature_engineer_review(review_data):
    features = {
        "review_id": review_data.get("review_id"),
        "product_id": review_data.get("product_id"),
        "user_id": review_data.get("user_id"),
        "timestamp": review_data.get("timestamp"),
        "text_features": {},
        "metadata_features": {}
    }

    # Text Features (TF-IDF)
    review_text = preprocess_text(review_data.get("review_text", ""))
    if review_text:
        # In a real scenario, the vectorizer is fitted on a large corpus
        # Here, we'll simulate fitting or expect a loaded one.
        # For demonstration, we'll just transform.
        # A robust solution would handle new words and vocabulary updates.
        try:
            text_tfidf = tfidf_vectorizer.transform([review_text]).toarray().tolist()[0]
            features["text_features"]["tfidf_vector"] = text_tfidf
        except Exception as e:
            logger.warning(f"Error transforming text with TF-IDF: {e}")
            features["text_features"]["tfidf_vector"] = [] # Empty if error

        features["text_features"]["text_length"] = len(review_text)
        features["text_features"]["word_count"] = len(review_text.split())

    # Metadata Features
    features["metadata_features"]["rating"] = review_data.get("rating")
    features["metadata_features"]["device_type"] = review_data.get("device_info") # Keep as string for now
    features["metadata_features"]["ip_address_hash"] = hash_ip_address(review_data.get("ip_address"))

    return features

if __name__ == '__main__':
    # Small hack for initial TF-IDF fit if no model is loaded
    # In production, vectorizer would be loaded from a file/model registry
    logger.info("Performing initial TF-IDF fit on a few messages (dev only).")
    sample_texts = []
    for i, message in enumerate(consumer):
        if i >= 10: # Fit on first 10 messages for a basic vocab
            break
        review = message.value
        sample_texts.append(preprocess_text(review.get("review_text", "")))
    if sample_texts:
        tfidf_vectorizer.fit(sample_texts)
        logger.info(f"TF-IDF vectorizer fitted with {len(tfidf_vectorizer.vocabulary_)} terms.")

    # Reset consumer to process from the beginning or start a new consumer
    consumer.close() # Close the old consumer
    consumer = KafkaConsumer( # Create a new one for continuous processing
        'validated_reviews',
        bootstrap_servers=['kafka:9092'],
        group_id='review_feature_engineering_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    logger.info("Starting continuous feature engineering...")

    for message in consumer:
        review = message.value
        try:
            feature_engineered_data = feature_engineer_review(review)
            producer.send('review_features', feature_engineered_data)
            logger.info(f"Feature engineered and sent review: {feature_engineered_data['review_id']}")
        except Exception as e:
            logger.error(f"Error during feature engineering for review {review.get('review_id', 'N/A')}: {e}")
            # Optionally send to a dead letter queue for feature engineering failures
        producer.flush()