# aris_detection_and_workflow.py

import datetime
from collections import defaultdict
import json

# --- Data Models (Conceptual, simplified) ---
class Review:
    def __init__(self, review_id, product_id, reviewer_id, text, timestamp, is_flagged=False, flag_reason=None):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.text = text
        self.timestamp = timestamp
        self.is_flagged = is_flagged
        self.flag_reason = flag_reason
        self.is_abusive = False
        self.is_removed = False

class ReviewerAccount:
    def __init__(self, reviewer_id, registration_timestamp):
        self.reviewer_id = reviewer_id
        self.registration_timestamp = registration_timestamp
        self.is_suspicious = False # Can be updated by a separate process

# --- User Story 1: Spike Detection ---

def detect_spike_zscore(product_id, historical_volumes, current_volume, window_size=24, threshold=3.0):
    """Detects spikes using a Z-score method."""
    if len(historical_volumes) < window_size:
        return False, "Not enough historical data to calculate Z-score"

    mean_volume = sum(historical_volumes) / window_size
    std_dev_volume = (sum([(x - mean_volume) ** 2 for x in historical_volumes]) / window_size) ** 0.5

    if std_dev_volume == 0:
        # If std dev is 0, all historical data points are the same.
        # A spike occurs if current volume is greater and non-zero.
        return current_volume > mean_volume and current_volume > 0, "Infinite Z-score (all historical same)"
    
    z_score = (current_volume - mean_volume) / std_dev_volume

    if z_score > threshold:
        return True, f"Spike detected: Z-score {z_score:.2f} > {threshold}"
    return False, f"No spike: Z-score {z_score:.2f}"

# Pseudocode for ReviewVolumeAggregator
current_hourly_counts = defaultdict(int)
last_flushed_hour = None # Simulate in-memory buffer

def process_new_review_event_aggregator(review_data):
    product_id = review_data['product_id']
    current_hour = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    
    global last_flushed_hour
    if last_flushed_hour is None:
        last_flushed_hour = current_hour

    if current_hour > last_flushed_hour:
        # In a real system, this would trigger a flush of previous hour's data to DB
        print(f"Aggregator: New hour, flushing data for {last_flushed_hour}")
        # flush_hourly_data(last_flushed_hour, current_hourly_counts)
        current_hourly_counts.clear()
        last_flushed_hour = current_hour

    current_hourly_counts[product_id] += 1
    print(f"Aggregator: Product {product_id} count for {current_hour}: {current_hourly_counts[product_id]}")

# Pseudocode for SpikeDetector service
def run_spike_detection_service():
    """Simulates the spike detection service running periodically."""
    print("\n--- Running Spike Detection ---")
    product_ids = ['P123', 'P456'] # Example product IDs
    
    # Dummy data retrieval
    historical_data_P123 = [10, 12, 11, 15, 13, 14, 16, 12, 11, 10, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    historical_data_P456 = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

    latest_volume_P123 = 100 # Artificially high to cause a spike
    latest_volume_P456 = 30

    for product_id in product_ids:
        if product_id == 'P123':
            historical_volumes = historical_data_P123
            current_volume = latest_volume_P123
        else:
            historical_volumes = historical_data_P456
            current_volume = latest_volume_P456

        is_spike, reason = detect_spike_zscore(product_id, historical_volumes, current_volume)

        if is_spike:
            print(f"Spike detected for Product {product_id}: {reason}. Volume: {current_volume}")
            process_spike_detected_event({
                'product_id': product_id,
                'timestamp': datetime.datetime.now().isoformat(),
                'reason': reason,
                'current_volume': current_volume
            })
        else:
            print(f"No spike for Product {product_id}: {reason}. Volume: {current_volume}")

# Pseudocode for FlaggingService processing spike event
def process_spike_detected_event(event_data):
    product_id = event_data['product_id']
    spike_timestamp = event_data['timestamp']
    spike_reason = event_data['reason']
    spike_volume = event_data['current_volume']

    # In a real system: Create a FlaggedItem entry in DB, update associated reviews
    print(f"FlaggingService: Product {product_id} flagged for 'Sudden Volume Spike' at {spike_timestamp}. Details: {spike_reason}, Volume: {spike_volume}")

# --- User Story 2: Account Clustering ---

def is_new_account(registration_timestamp):
    """Checks if an account is considered 'new'."""
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    return registration_timestamp >= seven_days_ago

def is_historically_suspicious(reviewer_id):
    """Checks if a reviewer is historically suspicious (placeholder)."""
    suspicious_ids = {'REV001', 'REV_BAD_ACTOR_001'} # Example bad actors
    return reviewer_id in suspicious_ids

# Helper classes for demo
class DemoReview:
    def __init__(self, review_id, product_id, reviewer_id, timestamp):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.timestamp = timestamp

class DemoReviewerAccount:
    def __init__(self, reviewer_id, registration_timestamp):
        self.reviewer_id = reviewer_id
        self.registration_timestamp = registration_timestamp

# Pseudocode for AccountClusterDetector service
def find_suspicious_review_clusters_service():
    """Identifies clusters of reviews from new/suspicious accounts."""
    print("\n--- Running Account Cluster Detection ---")
    
    # Dummy data: reviews from last 24 hours
    now = datetime.datetime.now()
    recent_reviews_demo = [
        DemoReview('R101', 'P789', 'REV001', now - datetime.timedelta(hours=1)), # Historically suspicious
        DemoReview('R102', 'P789', 'REV003', now - datetime.timedelta(hours=2)), # New
        DemoReview('R103', 'P789', 'REV004', now - datetime.timedelta(hours=3)), # New
        DemoReview('R104', 'P789', 'REV005', now - datetime.timedelta(hours=4)), # New
        DemoReview('R105', 'P789', 'REV006', now - datetime.timedelta(hours=5)), # New
        DemoReview('R106', 'P789', 'REV007', now - datetime.timedelta(hours=6)), # New
        DemoReview('R107', 'P789', 'REV008', now - datetime.timedelta(hours=7)), # Clean
        DemoReview('R201', 'P111', 'REV010', now - datetime.timedelta(hours=1)), # Clean
        DemoReview('R202', 'P111', 'REV011', now - datetime.timedelta(hours=2)), # Clean
    ]

    # Dummy account details retrieval
    def get_reviewer_account_details_demo(reviewer_id):
        if reviewer_id == 'REV001':
            return DemoReviewerAccount('REV001', now - datetime.timedelta(days=100)) # Historically suspicious
        elif reviewer_id in ['REV003', 'REV004', 'REV005', 'REV006', 'REV007']:
            return DemoReviewerAccount(reviewer_id, now - datetime.timedelta(days=1)) # New
        elif reviewer_id == 'REV008' or reviewer_id in ['REV010', 'REV011']:
            return DemoReviewerAccount(reviewer_id, now - datetime.timedelta(days=30)) # Clean
        return None

    reviews_by_product = defaultdict(list)
    for review in recent_reviews_demo:
        reviews_by_product[review.product_id].append(review)

    suspicious_clusters = []

    for product_id, reviews in reviews_by_product.items():
        suspicious_reviewers_count = 0
        reviewer_ids_in_cluster = set()
        for review in reviews:
            reviewer_ids_in_cluster.add(review.reviewer_id)

        for reviewer_id in reviewer_ids_in_cluster:
            account_details = get_reviewer_account_details_demo(reviewer_id)
            if account_details:
                if is_new_account(account_details.registration_timestamp) or \
                   is_historically_suspicious(reviewer_id):
                    suspicious_reviewers_count += 1
        
        # Cluster criteria: > 3 suspicious reviewers AND > 50% of reviewers in cluster are suspicious
        if suspicious_reviewers_count > 3 and len(reviewer_ids_in_cluster) > 0 and \
           (suspicious_reviewers_count / len(reviewer_ids_in_cluster)) > 0.5:
            
            suspicious_clusters.append({
                'product_id': product_id,
                'review_ids': [r.review_id for r in reviews],
                'suspicious_reviewers_count': suspicious_reviewers_count,
                'total_reviewers_in_cluster': len(reviewer_ids_in_cluster),
                'reason': 'Account Cluster'
            })
            
    for cluster in suspicious_clusters:
        print(f"ClusterDetector: Suspicious cluster found: Product {cluster['product_id']}, Reviews: {cluster['review_ids']}")
        process_cluster_detected_event(cluster)

# Pseudocode for FlaggingService processing cluster event
def process_cluster_detected_event(event_data):
    product_id = event_data['product_id']
    review_ids = event_data['review_ids']
    cluster_reason = event_data['reason']
    details = {'suspicious_reviewers_count': event_data['suspicious_reviewers_count'], 'review_ids': review_ids}

    # In a real system: Create a FlaggedItem entry for the product/cluster, update individual reviews
    print(f"FlaggingService: Product {product_id} and reviews {review_ids} flagged for '{cluster_reason}'. Details: {json.dumps(details)}")


# --- User Story 3: Linguistic Pattern Analysis ---

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import numpy as np
    
    # Initialize NLP tools once
    vectorizer = TfidfVectorizer(stop_words='english')
    sentiment_analyzer = SentimentIntensityAnalyzer()
    
    # In-memory store for recent review vectors for demo
    # In a real system, this would be a persistent store or vector DB
    recent_review_vectors_demo = defaultdict(list) # {product_id: [(review_id, vector, text), ...]}

    # Dummy function to fit the vectorizer on some initial corpus
    def initialize_vectorizer(corpus):
        if corpus:
            vectorizer.fit(corpus)

    # Call this once at startup with a representative sample of reviews
    initialize_vectorizer([
        "This product is amazing, I love it!",
        "Terrible experience, very bad quality.",
        "It's okay, nothing special.",
        "I bought this and it's fantastic!",
        "Worst purchase ever, completely disappointed."
    ])

    def preprocess_text(text):
        return text.lower() # Simple preprocessing

    def analyze_review_content_service(review_data):
        """Analyzes review content for suspicious linguistic patterns."""
        print("\n--- Running Linguistic Analysis ---")
        review_id = review_data['review_id']
        product_id = review_data['product_id']
        review_text = review_data['review_text']

        processed_text = preprocess_text(review_text)

        # 1. Sentiment Analysis
        sentiment_scores = sentiment_analyzer.polarity_scores(processed_text)
        compound_sentiment = sentiment_scores['compound']
        
        is_sentiment_outlier = False
        if abs(compound_sentiment) > 0.9: # Example threshold for extreme sentiment
            is_sentiment_outlier = True
            print(f"Linguistic Analysis: Extreme sentiment detected for Review {review_id}: {compound_sentiment}")

        # 2. Similarity Scoring (against recent reviews for the same product)
        is_highly_similar = False
        
        # Use the *fitted* vectorizer to transform the current review
        # Handle empty vocabulary case
        if not vectorizer.vocabulary_:
             print("Linguistic Analysis: Warning - TF-IDF vectorizer not fitted with vocabulary. Skipping similarity.")
             current_vector = None
        else:
            current_vector = vectorizer.transform([processed_text]) 

        if current_vector is not None and product_id in recent_review_vectors_demo and len(recent_review_vectors_demo[product_id]) > 0:
            # Re-transform historical texts using the same fitted vectorizer
            historical_texts = [item[2] for item in recent_review_vectors_demo[product_id]]
            historical_vectors = vectorizer.transform(historical_texts)

            if historical_vectors.shape[0] > 0: # Ensure there are vectors to compare against
                similarities = cosine_similarity(current_vector, historical_vectors)
                max_similarity = np.max(similarities)

                if max_similarity > 0.8: # Example threshold for high similarity
                    is_highly_similar = True
                    print(f"Linguistic Analysis: High similarity detected for Review {review_id}: Max similarity {max_similarity:.2f}")

        # Update recent_review_vectors_demo (add current review) - limited size in real system
        if current_vector is not None:
            recent_review_vectors_demo[product_id].append((review_id, current_vector, processed_text))
            # Keep a limited history, e.g., last 100 reviews per product
            if len(recent_review_vectors_demo[product_id]) > 100:
                recent_review_vectors_demo[product_id].pop(0)
        
        # Decision to flag
        if is_sentiment_outlier or is_highly_similar:
            reason = []
            if is_sentiment_outlier: reason.append('Extreme Sentiment')
            if is_highly_similar: reason.append('Highly Similar Content')
            print(f"Linguistic Analysis: Flagging Review {review_id} for linguistic patterns: {', '.join(reason)}")
            process_linguistic_abuse_event({
                'review_id': review_id,
                'product_id': product_id,
                'reasons': reason
            })
        else:
            print(f"Linguistic Analysis: Review {review_id} passed linguistic checks.")

except ImportError:
    print("\n--- NLP Libraries not installed. Skipping Linguistic Pattern Analysis Demo ---")
    print("Please install scikit-learn and nltk: pip install scikit-learn nltk")
    print("Also, download VADER lexicon for nltk: import nltk; nltk.download('vader_lexicon')")
    # Define dummy functions if imports fail
    def analyze_review_content_service(review_data):
        print("\n--- Skipping Linguistic Analysis: Libraries missing ---")
    def process_linguistic_abuse_event(event_data):
        print("\n--- Skipping Linguistic Abuse Event Processing: Libraries missing ---")


# Pseudocode for FlaggingService processing linguistic event
def process_linguistic_abuse_event(event_data):
    review_id = event_data['review_id']
    product_id = event_data['product_id']
    reasons = event_data['reasons']

    # In a real system: Create a FlaggedItem entry for the review, update individual review
    print(f"FlaggingService: Review {review_id} flagged for 'Suspicious Linguistic Pattern'. Reasons: {', '.join(reasons)}")

# --- User Story 4 & 5: Analyst Workflow API (Flask Pseudocode) ---
# Note: In a real deployment, these would be in a separate service.
# For simplicity, mocked within this single file.

# from flask import Flask, jsonify, request
# app = Flask(__name__)

def get_current_analyst_id():
    # Placeholder for fetching analyst ID from authentication context
    return 'ANL001'

# Dummy data for API
flagged_items_db = [
    {'flagged_item_id': 'FI001', 'item_type': 'product', 'item_id': 'P123', 
     'flag_reason': 'Sudden Volume Spike', 'flag_timestamp': '2023-10-27T10:00:00Z', 
     'priority_score': 9.5, 'status': 'new', 'flag_details': {'volume': 100, 'z_score': 4.1}},
    {'flagged_item_id': 'FI002', 'item_type': 'review', 'item_id': 'R101', 
     'flag_reason': 'Suspicious Linguistic Pattern', 'flag_timestamp': '2023-10-27T10:30:00Z',
     'priority_score': 8.2, 'status': 'new', 'flag_details': {'reasons': ['Extreme Sentiment']}},
    {'flagged_item_id': 'FI003', 'item_type': 'review', 'item_id': 'R102', 
     'flag_reason': 'Suspicious Account Cluster', 'flag_timestamp': '2023-10-27T11:00:00Z',
     'priority_score': 8.9, 'status': 'new', 'flag_details': {'review_count': 5, 'new_accounts': 4}},
]

reviews_db = {
    'R1001': {'review_id': 'R1001', 'text': 'Great product!', 'reviewer_id': 'A1', 'product_id': 'P123', 'timestamp': '2023-10-27T10:05:00Z', 'is_abusive': False, 'is_removed': False},
    'R1002': {'review_id': 'R1002', 'text': 'Love it!', 'reviewer_id': 'A2', 'product_id': 'P123', 'timestamp': '2023-10-27T10:10:00Z', 'is_abusive': False, 'is_removed': False},
    'R101': {'review_id': 'R101', 'text': 'OMG! This is the most fantastic product EVER!!! You MUST buy it!', 'reviewer_id': 'REV003', 'product_id': 'P789', 'timestamp': '2023-10-27T10:25:00Z', 'is_abusive': False, 'is_removed': False},
    'R102': {'review_id': 'R102', 'text': 'This is a good product. I like it.', 'reviewer_id': 'REV004', 'product_id': 'P789', 'timestamp': '2023-10-27T10:55:00Z', 'is_abusive': False, 'is_removed': False},
}

products_db = {
    'P123': {'product_id': 'P123', 'name': 'Amazing Widget'},
    'P789': {'product_id': 'P789', 'name': 'Excellent Gadget'},
}

reviewer_accounts_db = {
    'A1': {'reviewer_id': 'A1', 'username': 'UserA1', 'registration_timestamp': '2022-01-01T00:00:00Z'},
    'A2': {'reviewer_id': 'A2', 'username': 'UserA2', 'registration_timestamp': '2022-02-01T00:00:00Z'},
    'REV003': {'reviewer_id': 'REV003', 'username': 'NewReviewer', 'registration_timestamp': '2023-10-26T00:00:00Z'},
    'REV004': {'reviewer_id': 'REV004', 'username': 'AnotherNewbie', 'registration_timestamp': '2023-10-25T00:00:00Z'},
}

# @app.route('/api/flagged-items', methods=['GET'])
def api_get_flagged_items():
    """Simulates API endpoint for fetching flagged items."""
    # Filter, sort, paginate logic would go here
    return json.dumps(flagged_items_db)

# @app.route('/api/flagged-items/<item_id>', methods=['GET'])
def api_get_flagged_item_details(item_id):
    """Simulates API endpoint for fetching flagged item details."""
    flagged_item = next((item for item in flagged_items_db if item['flagged_item_id'] == item_id), None)
    if not flagged_item:
        # return jsonify({'message': 'Flagged item not found'}), 404
        return json.dumps({'message': 'Flagged item not found'}), 404

    details = flagged_item.copy()
    if flagged_item['item_type'] == 'review':
        review_info = reviews_db.get(flagged_item['item_id'])
        if review_info:
            details['review_info'] = review_info
            details['product_info'] = products_db.get(review_info['product_id'])
            details['reviewer_info'] = reviewer_accounts_db.get(review_info['reviewer_id'])
    elif flagged_item['item_type'] == 'product':
        details['product_info'] = products_db.get(flagged_item['item_id'])
        # Optionally, fetch associated reviews for the spike period
        details['associated_reviews'] = [r for r_id, r in reviews_db.items() if r['product_id'] == flagged_item['item_id'] and r['timestamp'] >= flagged_item['flag_timestamp']]

    # return jsonify(details)
    return json.dumps(details)

# @app.route('/api/reviews/<review_id>/mark-abusive', methods=['PATCH'])
def api_mark_review_abusive(review_id):
    """Simulates API endpoint for marking review as abusive."""
    analyst_id = get_current_analyst_id()
    review = reviews_db.get(review_id)
    if not review:
        # return jsonify({'message': 'Review not found'}), 404
        return json.dumps({'message': 'Review not found'}), 404
    
    review['is_abusive'] = True
    review['abusive_timestamp'] = datetime.datetime.now().isoformat()

    # Update associated FlaggedItem status
    for item in flagged_items_db:
        if item['item_type'] == 'review' and item['item_id'] == review_id:
            item['status'] = 'abusive_confirmed'
            break

    print(f"Analyst API: Review {review_id} marked as abusive by analyst {analyst_id}.")
    # return jsonify({'message': f'Review {review_id} marked as abusive'}), 200
    return json.dumps({'message': f'Review {review_id} marked as abusive'}), 200

# @app.route('/api/reviews/<review_id>/remove', methods=['PATCH'])
def api_remove_review(review_id):
    """Simulates API endpoint for initiating review removal."""
    analyst_id = get_current_analyst_id()
    review = reviews_db.get(review_id)
    if not review:
        # return jsonify({'message': 'Review not found'}), 404
        return json.dumps({'message': 'Review not found'}), 404
    
    review['is_removed'] = True
    review['removal_timestamp'] = datetime.datetime.now().isoformat()

    # Update associated FlaggedItem status
    for item in flagged_items_db:
        if item['item_type'] == 'review' and item['item_id'] == review_id:
            item['status'] = 'removal_requested'
            break

    # In a real system: publish event to a message queue for ReviewRemovalService
    print(f"Analyst API: Review {review_id} removal requested by analyst {analyst_id}. (Event published)")
    # return jsonify({'message': f'Review {review_id} removal requested'}), 200
    return json.dumps({'message': f'Review {review_id} removal requested'}), 200

# Placeholder for running the Flask app directly for testing
# if __name__ == '__main__':
#     # This part would only run if the file is executed directly, not when imported.
#     # For actual API, you'd run a Flask/Gunicorn server.
#     print("--- Running Demos ---")
#     process_new_review_event_aggregator({'product_id': 'P123', 'review_id': 'R_NEW_001'})
#     process_new_review_event_aggregator({'product_id': 'P123', 'review_id': 'R_NEW_002'})
#     run_spike_detection_service()
#     find_suspicious_review_clusters_service()
#     analyze_review_content_service({
#         'review_id': 'R_NLP_001', 
#         'product_id': 'P789', 
#         'review_text': 'OMG! This is the most fantastic product EVER!!! You MUST buy it!'
#     })
#     analyze_review_content_service({
#         'review_id': 'R_NLP_002', 
#         'product_id': 'P789', 
#         'review_text': 'OMG! This is the most fantastic product EVER!!! You MUST buy it!' # Duplicate
#     })
#     analyze_review_content_service({
#         'review_id': 'R_NLP_003', 
#         'product_id': 'P789', 
#         'review_text': 'This is just a normal review. Nothing to see here.'
#     })
#     print("\n--- Analyst API Demo (Conceptual) ---")
#     print(f"Flagged items: {api_get_flagged_items()}")
#     print(f"Details for FI002: {api_get_flagged_item_details('FI002')}")
#     print(f"Mark R101 abusive: {api_mark_review_abusive('R101')}")
#     print(f"Remove R102: {api_remove_review('R102')}")
#     print(f"Updated R101 status: {reviews_db['R101']}")
#     print(f"Updated FI002 status: {next((item for item in flagged_items_db if item['flagged_item_id'] == 'FI002'), None)}")
