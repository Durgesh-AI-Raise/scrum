import json
from datetime import datetime
# from mq_client import consume_reviews_from_queue
# from detection_models.user_activity_detector import UserActivityDetector
# from flagged_review_storage import store_flagged_review_new_account
# from state_manager import get_user_detector_state, save_user_detector_state # For Redis state

user_detectors = {} # In-memory store for MVP, replace with persistent state for production

def process_review_for_user_activity(review_json: str):
    review_data = json.loads(review_json)
    user_id = review_data['user_id']
    review_date = datetime.fromisoformat(review_data['review_date'])
    product_id = review_data['product_id']

    if user_id not in user_detectors:
        # Load state for user from Redis/DB if exists, else create new
        user_detectors[user_id] = UserActivityDetector(user_id)

    detector = user_detectors[user_id]
    detector.add_review(review_date, product_id)

    activity_alert = detector.detect_unusual_activity(datetime.now()) # Use current time for detection check

    if activity_alert:
        print(f"!!! UNUSUAL ACTIVITY ALERT for User {user_id}: {activity_alert['flag_reason']}")
        # store_flagged_review_new_account(review_data['review_id'], activity_alert)
        # Optionally, publish to another queue for human review/action

    # Periodically save detector state
    # save_user_detector_state(user_id, detector.get_state())

def run_new_account_activity_consumer():
    """
    Starts the message queue consumer for new account activity detection.
    """
    print("Starting New Account Activity Detection Service consumer...")
    # Simulating message reception for demonstration
    example_reviews = [
        '''{"review_id": "nr1", "product_id": "PA", "user_id": "NEWU1", "rating": 5, "review_date": "2023-10-26T10:00:00"}''',
        '''{"review_id": "nr2", "product_id": "PB", "user_id": "NEWU1", "rating": 4, "review_date": "2023-10-26T10:05:00"}''',
        '''{"review_id": "nr3", "product_id": "PC", "user_id": "NEWU1", "rating": 5, "review_date": "2023-10-26T10:10:00"}''',
        '''{"review_id": "nr4", "product_id": "PD", "user_id": "NEWU1", "rating": 4, "review_date": "2023-10-26T10:15:00"}''',
        '''{"review_id": "nr5", "product_id": "PE", "user_id": "NEWU1", "rating": 5, "review_date": "2023-10-26T10:20:00"}''',
        '''{"review_id": "nr6", "product_id": "PF", "user_id": "NEWU1", "rating": 4, "review_date": "2023-10-26T10:25:00"}''',
        # Another user with normal activity
        '''{"review_id": "nr7", "product_id": "PG", "user_id": "OLD_U", "rating": 5, "review_date": "2023-01-01T10:00:00"}''',
        '''{"review_id": "nr8", "product_id": "PH", "user_id": "OLD_U", "rating": 4, "review_date": "2023-10-26T10:30:00"}'''
    ]
    for review in example_reviews:
        process_review_for_user_activity(review)
        
if __name__ == "__main__":
    run_new_account_activity_consumer()
