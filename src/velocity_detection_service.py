# src/velocity_detection_service.py
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, List, Deque
import uuid

from data_models import Review, VelocityThreshold, Alert, AbuseCategory
from abuse_config import get_abuse_category # To link alerts to abuse categories
# Assume velocity_config.py exists for loading VelocityThresholds
# For now, let's define mock thresholds here.
# In a real system, these would be loaded from a configuration service or file.

logging.basicConfig(level=logging.INFO)

# --- Mock Kinesis Consumer and DynamoDB for alerts ---
class MockKinesisConsumer:
    """Simulates reading records from Kinesis."""
    def __init__(self, stream_name):
        self.stream_name = stream_name
        self._mock_records = deque()

    def add_record(self, data: Dict):
        self._mock_records.append({
            'Data': json.dumps(data).encode('utf-8'),
            'PartitionKey': data.get('review_id') or data.get('product_id'),
            'SequenceNumber': str(uuid.uuid4())
        })

    def get_records(self, limit=1):
        if self._mock_records:
            return [self._mock_records.popleft()]
        return []

class MockAlertStorageClient:
    """Simulates storing alerts in DynamoDB."""
    def __init__(self, table_name):
        self.table_name = table_name
        self.alerts = [] # In-memory store for demonstration

    def put_item(self, TableName, Item):
        logging.info(f"Mock Alert Storage: Storing to {TableName}: {Item.to_dict()}")
        self.alerts.append(Item.to_dict())
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

# Instantiate mocks
kinesis_consumer = MockKinesisConsumer(stream_name="amazon-review-events")
alert_storage = MockAlertStorageClient(table_name="amazon-alerts")

# In a real system, load these from a config service or file (e.g., velocity_config.py)
MOCK_VELOCITY_THRESHOLDS: List[VelocityThreshold] = [
    VelocityThreshold(
        threshold_id="PROD_HIGH_VELOCITY_24H",
        entity_type="PRODUCT",
        window_size_hours=24,
        max_reviews_in_window=100, # More than 100 reviews for a product in 24 hours
        alert_level="CRITICAL",
        description="High review velocity for a product over 24 hours"
    ),
    VelocityThreshold(
        threshold_id="PROD_HIGH_VELOCITY_1H",
        entity_type="PRODUCT",
        window_size_hours=1,
        max_reviews_in_window=10, # More than 10 reviews for a product in 1 hour
        alert_level="WARNING",
        description="High review velocity for a product over 1 hour"
    ),
    VelocityThreshold(
        threshold_id="REV_HIGH_VELOCITY_24H",
        entity_type="REVIEWER",
        window_size_hours=24,
        max_reviews_in_window=20, # More than 20 reviews by a reviewer in 24 hours
        alert_level="CRITICAL",
        description="High review velocity by a reviewer over 24 hours"
    ),
    VelocityThreshold(
        threshold_id="REV_HIGH_VELOCITY_1H",
        entity_type="REVIEWER",
        window_size_hours=1,
        max_reviews_in_window=3, # More than 3 reviews by a reviewer in 1 hour
        alert_level="WARNING",
        description="High review velocity by a reviewer over 1 hour"
    )
]

# In-memory store for review timestamps for velocity calculation
# Structure: { "PRODUCT|product_id": deque_of_timestamps, "REVIEWER|reviewer_id": deque_of_timestamps }
# In a real system, this would be a distributed, persistent store (e.g., Redis, DynamoDB with TTL)
velocity_windows: Dict[str, Deque[datetime]] = defaultdict(deque)

def calculate_velocity(entity_key: str, window_size_hours: int, current_time: datetime) -> int:
    """Calculates the number of reviews within the specified time window."""
    window_start_time = current_time - timedelta(hours=window_size_hours)
    
    # Efficiently remove old timestamps from the left of the deque
    while velocity_windows[entity_key] and velocity_windows[entity_key][0] < window_start_time:
        velocity_windows[entity_key].popleft()
    
    return len(velocity_windows[entity_key])

def process_review_for_velocity(review_obj: Review):
    current_time = review_obj.ingestion_timestamp or datetime.now()

    # Update velocity windows for product
    product_key = f"PRODUCT|{review_obj.product_id}"
    velocity_windows[product_key].append(current_time)

    # Update velocity windows for reviewer
    reviewer_key = f"REVIEWER|{review_obj.reviewer_id}"
    velocity_windows[reviewer_key].append(current_time)

    logging.info(f"Processing review {review_obj.review_id} for velocity detection.")

    # Check against all defined velocity thresholds
    for threshold in MOCK_VELOCITY_THRESHOLDS:
        entity_id = None
        entity_key = None
        if threshold.entity_type == "PRODUCT":
            entity_id = review_obj.product_id
            entity_key = product_key
        elif threshold.entity_type == "REVIEWER":
            entity_id = review_obj.reviewer_id
            entity_key = reviewer_key
        
        if not entity_id or not entity_key:
            continue # Should not happen with correct configuration

        current_velocity = calculate_velocity(entity_key, threshold.window_size_hours, current_time)

        if current_velocity > threshold.max_reviews_in_window:
            logging.warning(
                f"!!! VELOCITY ALERT !!! "
                f"Entity: {threshold.entity_type} ID: {entity_id}, "
                f"Velocity: {current_velocity} reviews in {threshold.window_size_hours} hours, "
                f"Threshold: {threshold.max_reviews_in_window}. Level: {threshold.alert_level}"
            )

            # Create an Alert object
            # Link to VELOCITY_ANOMALY abuse category if applicable
            velocity_abuse_category = get_abuse_category("VELOCITY_ANOMALY")
            alert_type = velocity_abuse_category.category_name if velocity_abuse_category else "HIGH_REVIEW_VELOCITY"

            alert = Alert(
                entity_type=threshold.entity_type,
                entity_id=entity_id,
                alert_type=alert_type,
                triggered_threshold_id=threshold.threshold_id,
                current_velocity_value=current_velocity,
                context_reviews=[review_obj.review_id], # Include current review + others from window
                alert_timestamp=current_time,
                status="NEW",
                notes=f"Exceeded {threshold.description}"
            )
            # Store the alert
            alert_storage.put_item(TableName="amazon-alerts", Item=alert)

# Main loop for the Kinesis consumer (conceptual)
def run_velocity_detection_service():
    logging.info("Starting Velocity Detection Service consumer...")
    while True:
        records = kinesis_consumer.get_records(limit=10) # Get a batch of records
        if not records:
            # In a real service, add a sleep here or use long polling
            continue

        for record in records:
            try:
                data = json.loads(record['Data'].decode('utf-8'))
                review_obj = Review(**data)
                process_review_for_velocity(review_obj)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode Kinesis record: {e} - Data: {record['Data']}")
                # DLQ for malformed records
            except (TypeError, ValueError) as e:
                logging.error(f"Failed to parse review from Kinesis record: {e} - Data: {data}")
                # DLQ for invalid review data
            except Exception as e:
                logging.error(f"Unhandled error processing Kinesis record: {e}", exc_info=True)

if __name__ == '__main__':
    # This block is for demonstration.
    # In a real deployment, run_velocity_detection_service() would be started.

    # Simulate some incoming reviews
    print("Simulating review ingestion and velocity detection...")
    
    # Review 1 for Product A by Reviewer X
    review_data_1 = {
        "review_id": "rev1", "product_id": "prodA", "reviewer_id": "revX",
        "review_text": "Great product!", "rating": 5, "review_date": (datetime.now() - timedelta(minutes=50)).isoformat() + 'Z'
    }
    review_obj_1 = Review(**review_data_1)
    kinesis_consumer.add_record(review_obj_1.to_dict())

    # Review 2 for Product A by Reviewer X (within 1 hour threshold for reviewer)
    review_data_2 = {
        "review_id": "rev2", "product_id": "prodA", "reviewer_id": "revX",
        "review_text": "Another great one!", "rating": 5, "review_date": (datetime.now() - timedelta(minutes=45)).isoformat() + 'Z'
    }
    review_obj_2 = Review(**review_data_2)
    kinesis_consumer.add_record(review_obj_2.to_dict())

    # Review 3 for Product A by Reviewer X (triggers REV_HIGH_VELOCITY_1H)
    review_data_3 = {
        "review_id": "rev3", "product_id": "prodA", "reviewer_id": "revX",
        "review_text": "Super happy!", "rating": 5, "review_date": (datetime.now() - timedelta(minutes=40)).isoformat() + 'Z'
    }
    review_obj_3 = Review(**review_data_3)
    kinesis_consumer.add_record(review_obj_3.to_dict())

    # Review 4 for Product A by Reviewer Y (adds to product velocity)
    review_data_4 = {
        "review_id": "rev4", "product_id": "prodA", "reviewer_id": "revY",
        "review_text": "Good stuff.", "rating": 4, "review_date": (datetime.now() - timedelta(minutes=30)).isoformat() + 'Z'
    }
    review_obj_4 = Review(**review_data_4)
    kinesis_consumer.add_record(review_obj_4.to_dict())

    # Process all simulated records
    while True:
        records_to_process = kinesis_consumer.get_records(limit=1)
        if not records_to_process:
            break
        for record in records_to_process:
            data = json.loads(record['Data'].decode('utf-8'))
            review_obj = Review(**data)
            process_review_for_velocity(review_obj)

    print("\n--- Generated Alerts ---")
    for alert in alert_storage.alerts:
        print(alert)
    print("------------------------")
