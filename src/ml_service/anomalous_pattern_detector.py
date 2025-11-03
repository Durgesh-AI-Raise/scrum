# src/ml_service/anomalous_pattern_detector.py
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from sklearn.ensemble import IsolationForest
from sklearn.metrics.pairwise import cosine_similarity
from collections import deque
import numpy as np
from datetime import datetime, timedelta
import joblib # To load/save models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Consumers and Producers
consumer = KafkaConsumer(
    'review_features', # Consumes feature-engineered data
    bootstrap_servers=['kafka:9092'],
    group_id='anomalous_pattern_detector_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# --- Model Loading (Simulated for Baseline) ----
# In a production environment, models would be trained offline and loaded.
# For this baseline, we'll create dummy models or re-train on a small sample.

# Isolation Forest for general anomaly detection
# It's an unsupervised model, so we can fit it without explicit anomaly labels.
isolation_forest_model = IsolationForest(contamination='auto', random_state=42)
# Placeholder: In reality, load a pre-trained model:
# isolation_forest_model = joblib.load('models/isolation_forest_review_text.pkl')

# TF-IDF Vectorizer (same as used in feature engineering, should be consistent)
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
# Placeholder: tfidf_vectorizer = joblib.load('models/tfidf_vectorizer.pkl')

# --- Parameters for Anomaly Detection ----
COSINE_SIMILARITY_THRESHOLD = 0.95 # For duplicate detection
RECENT_REVIEWS_WINDOW_SIZE = 1000  # Number of recent reviews to keep in memory for duplicate check
review_history_vectors = deque(maxlen=RECENT_REVIEWS_WINDOW_SIZE)
review_history_ids = deque(maxlen=RECENT_REVIEWS_WINDOW_SIZE)

# For volume anomaly detection
VOLUME_WINDOW_SECONDS = 3600 # 1 hour
VOLUME_THRESHOLD_Z_SCORE = 3 # Flag if review count is 3 std devs above mean

# In-memory store for recent review counts (for volume anomaly)
# { 'product_id': { 'timestamp_bucket': count } }
# This is a simplification; a proper streaming solution (e.g., Flink) would be better for volume.
review_volume_data = {}
historical_volume_means_stds = {} # { 'product_id': {'mean': X, 'std': Y} } - would be pre-calculated

def detect_anomalous_patterns(review_features, original_review_data):
    flag_reasons = []
    is_flagged = False
    
    # 1. Isolation Forest for general text/metadata anomalies
    # Combine text TF-IDF and numerical metadata features
    text_vector = review_features['text_features'].get('tfidf_vector', [])
    # Convert device_type to numerical (simple one-hot or embedding, for now just 0/1)
    # This requires a more robust mapping for production
    # device_type_numeric = 1 if review_features['metadata_features'].get('device_type') == 'mobile' else 0
    
    # Ensure all features for IF are numerical
    # Dummy numerical features for ip_address_hash and text_length/word_count for initial baseline
    # In a real system, ip_address_hash would need more complex feature engineering (e.g., frequency encoding)
    # For now, let's simplify to a minimal set of numerical features for IsolationForest
    # We will need to ensure feature vectors have consistent length.
    
    # For baseline, let's only use text_vector and rating if available
    # A robust solution would handle missing features and align dimensions.
    
    if text_vector and review_features['metadata_features'].get('rating') is not None:
        numerical_features = text_vector + [review_features['metadata_features']['rating']]
        # Reshape for single sample prediction
        try:
            # Need to fit IsolationForest initially with some data or load a pre-fitted one
            # For simplicity, let's assume `isolation_forest_model` is already fitted on a dummy dataset
            # This is a hack for the baseline; proper training is required.
            if not hasattr(isolation_forest_model, 'tree_root_'): # Check if model is fitted
                logger.warning("Isolation Forest model not fitted. Fitting with dummy data for baseline.")
                dummy_data = np.random.rand(100, len(numerical_features)) # 100 samples, feature dimension
                isolation_forest_model.fit(dummy_data)

            anomaly_score = isolation_forest_model.decision_function([numerical_features])[0]
            if anomaly_score < -0.1: # Threshold for anomaly (can be tuned)
                is_flagged = True
                flag_reasons.append("anomalous_pattern_isolation_forest")
                logger.info(f"Review {review_features['review_id']} flagged by Isolation Forest (score: {anomaly_score})")
        except Exception as e:
            logger.error(f"Error during Isolation Forest prediction: {e}")
            
    # 2. Duplicate Review Detection (TF-IDF + Cosine Similarity)
    current_review_tfidf_vector = review_features['text_features'].get('tfidf_vector')
    if current_review_tfidf_vector:
        if review_history_vectors: # Check if there are reviews to compare against
            # Calculate cosine similarity with all vectors in the history
            similarities = cosine_similarity([current_review_tfidf_vector], list(review_history_vectors))[0]
            if np.max(similarities) > COSINE_SIMILARITY_THRESHOLD:
                is_flagged = True
                flag_reasons.append("duplicate_review")
                most_similar_idx = np.argmax(similarities)
                logger.info(f"Review {review_features['review_id']} flagged as duplicate of {review_history_ids[most_similar_idx]} (similarity: {np.max(similarities)})")
        
        # Add current review to history
        review_history_vectors.append(current_review_tfidf_vector)
        review_history_ids.append(review_features['review_id'])

    # 3. Volume Anomaly Detection (Simplified for baseline)
    # This requires more robust state management and historical data
    # For baseline, a simplified in-memory count per product_id per hour
    product_id = review_features['product_id']
    timestamp_str = review_features['timestamp']
    if timestamp_str:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Create an hourly bucket key
        hour_bucket = timestamp.strftime('%Y-%m-%d-%H')

        if product_id not in review_volume_data:
            review_volume_data[product_id] = {}
        
        review_volume_data[product_id][hour_bucket] = review_volume_data[product_id].get(hour_bucket, 0) + 1
        
        # Basic check for sudden spike in the current hour compared to, say, previous hours
        # This is a very simplistic baseline. A real system needs a sliding window average.
        current_hour_count = review_volume_data[product_id][hour_bucket]
        
        # This is highly simplified: to truly detect spikes, you need a baseline of
        # expected volume. For a baseline, we'll just check if the current count is very high.
        # A more robust solution would compute moving averages and standard deviations.
        
        # Placeholder for real volume anomaly logic:
        # if product_id in historical_volume_means_stds:
        #     mean = historical_volume_means_stds[product_id]['mean']
        #     std = historical_volume_means_stds[product_id]['std']
        #     if current_hour_count > mean + VOLUME_THRESHOLD_Z_SCORE * std:
        #         is_flagged = True
        #         flag_reasons.append("volume_spike")

        # Simplified for baseline: if count in current hour exceeds a fixed high threshold
        if current_hour_count > 50: # Arbitrary high threshold for a baseline
             is_flagged = True
             flag_reasons.append("sudden_volume_spike_baseline")
             logger.info(f"Review {review_features['review_id']} flagged for volume spike on product {product_id} ({current_hour_count} reviews in hour)")


    # Construct the output review data
    # Original review data needs to be passed through or re-fetched.
    # For now, let's assume original_review_data is passed or we reconstruct.
    output_review = original_review_data.copy()
    output_review['is_flagged'] = is_flagged
    output_review['flag_reason'] = list(set(flag_reasons)) # Remove duplicates

    return output_review

if __name__ == '__main__':
    logger.info("Starting anomalous pattern detection service...")
    
    # Initial "fitting" of TF-IDF and Isolation Forest if not loaded
    # This is a crucial simplification for the baseline.
    # In a real system, these would be loaded pre-trained.
    
    # To fit TF-IDF and Isolation Forest, we need some initial data.
    # For a baseline, let's simulate this by consuming a few messages first.
    # In a real-time system, this "fitting" would be done offline.
    
    sample_texts_for_tfidf_fit = []
    sample_features_for_if_fit = []
    
    logger.info("Collecting initial data for dummy model fitting...")
    initial_messages = []
    for i, message in enumerate(consumer):
        initial_messages.append(message)
        if i >= 50: # Collect 50 messages to "fit"
            break
    
    if initial_messages:
        for msg in initial_messages:
            review_features = msg.value
            if 'text_features' in review_features and review_features['text_features'].get('tfidf_vector'):
                # We need the original text to fit TFIDF, not the vector
                # This highlights a dependency: original text needed for TFIDF fit
                # For this baseline, we'll skip direct TFIDF re-fit here and assume the FE service passes coherent vectors.
                pass # TFIDF is assumed to be consistently applied by feature_engineering_reviews.py
            
            # For Isolation Forest, we need numerical features
            text_vector_for_if = review_features['text_features'].get('tfidf_vector', [])
            rating_for_if = review_features['metadata_features'].get('rating')
            
            if text_vector_for_if and rating_for_if is not None:
                combined_features = text_vector_for_if + [rating_for_if]
                sample_features_for_if_fit.append(combined_features)
                
        if sample_features_for_if_fit:
            # Fit Isolation Forest on the collected sample
            try:
                isolation_forest_model.fit(np.array(sample_features_for_if_fit))
                logger.info(f"Isolation Forest model fitted on {len(sample_features_for_if_fit)} samples.")
            except Exception as e:
                logger.error(f"Failed to fit Isolation Forest: {e}")
        else:
            logger.warning("No suitable features collected to fit Isolation Forest.")

    # Reset consumer or start new one to process all messages from beginning
    # For this simple script, we'll continue processing from where we left off,
    # assuming the initial messages were processed for "fitting" purposes.
    # In a real setup, you'd have a separate offline training pipeline.
    
    for message in consumer: # Continue consuming
        review_features = message.value
        original_review = { # Reconstruct a simplified original review for output
            "review_id": review_features.get("review_id"),
            "product_id": review_features.get("product_id"),
            "user_id": review_features.get("user_id"),
            "review_text": "placeholder_text", # In a real system, pass original text through feature engineering
            "rating": review_features['metadata_features'].get("rating"),
            "timestamp": review_features.get("timestamp"),
            "device_info": review_features['metadata_features'].get("device_type"),
            "ip_address": review_features['metadata_features'].get("ip_address_hash"), # Pass hash if that's all we have
            "location_data": None # Not in features, so set to None
        }

        try:
            flagged_review_data = detect_anomalous_patterns(review_features, original_review)
            producer.send('flagged_reviews_stream', flagged_review_data)
            logger.info(f"Processed review {flagged_review_data['review_id']}. Flagged: {flagged_review_data['is_flagged']} with reasons: {flagged_review_data['flag_reason']}")
        except Exception as e:
            logger.error(f"Error during anomaly detection for review {review_features.get('review_id', 'N/A')}: {e}")
        producer.flush()