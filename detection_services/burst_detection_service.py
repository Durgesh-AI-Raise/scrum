import json
from datetime import datetime
# from mq_client import consume_reviews_from_queue # Assuming MQ client
# from detection_models.burst_detector import ProductBurstDetector
# from flagged_review_storage import store_flagged_review_burst
# from state_manager import get_product_detector_state, save_product_detector_state # For distributed state (e.g., Redis)

product_detectors = {} # In-memory store for MVP, replace with persistent state for production

def process_review_for_burst_detection(review_json: str):
    review_data = json.loads(review_json)
    product_id = review_data['product_id']
    review_date = datetime.fromisoformat(review_data['review_date'])
    rating = review_data['rating']

    if product_id not in product_detectors:
        # For production, try to load state from Redis/DB
        # detector_state = get_product_detector_state(product_id)
        product_detectors[product_id] = ProductBurstDetector(product_id)
        # if detector_state: product_detectors[product_id].load_state(detector_state)

    detector = product_detectors[product_id]
    detector.add_review(review_date, rating)

    burst_alert = detector.detect_burst(datetime.now()) # Use current time for detection check

    if burst_alert:
        print(f"!!! BURST ALERT for Product {product_id}: {burst_alert['flag_reason']}")
        # store_flagged_review_burst(review_data['review_id'], burst_alert)
        # Optionally, publish to another queue for immediate human review/action

    # Periodically save detector state (e.g., every N reviews or M seconds)
    # save_product_detector_state(product_id, detector.get_state())

def run_burst_detection_consumer():
    """
    Starts the message queue consumer for burst detection.
    """
    print("Starting Burst Detection Service consumer...")
    # For an actual implementation, this would be a loop consuming from the MQ
    # for message in consume_reviews_from_queue():
    #    process_review_for_burst_detection(message)
    
    # Simulating message reception for demonstration
    example_reviews = [
        '''{"review_id": "r1", "product_id": "P1", "user_id": "U1", "rating": 5, "review_date": "2023-10-26T10:00:00"}''',
        '''{"review_id": "r2", "product_id": "P1", "user_id": "U2", "rating": 5, "review_date": "2023-10-26T10:05:00"}''',
        '''{"review_id": "r3", "product_id": "P2", "user_id": "U3", "rating": 1, "review_date": "2023-10-26T10:10:00"}''',
        '''{"review_id": "r4", "product_id": "P1", "user_id": "U4", "rating": 5, "review_date": "2023-10-26T10:15:00"}''',
        '''{"review_id": "r5", "product_id": "P1", "user_id": "U5", "rating": 5, "review_date": "2023-10-26T10:20:00"}''',
        '''{"review_id": "r6", "product_id": "P1", "user_id": "U6", "rating": 5, "review_date": "2023-10-26T10:25:00"}''',
        '''{"review_id": "r7", "product_id": "P1", "user_id": "U7", "rating": 5, "review_date": "2023-10-26T10:30:00"}'''
    ]
    for review in example_reviews:
        process_review_for_burst_detection(review)
        
if __name__ == "__main__":
    run_burst_detection_consumer()
