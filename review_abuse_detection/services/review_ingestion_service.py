
# review_abuse_detection/services/review_ingestion_service.py

from datetime import datetime, timedelta, timezone
# Assuming a database ORM or direct client 'db' is available
# from your_project.database import db

# Placeholder for a simplified database interaction
class MockReviewVelocityDB:
    def __init__(self):
        self.data = {} # {(product_id, timestamp_hour): {review_count_last_hour, review_count_last_day, ...}}

    def find_or_create(self, product_id, timestamp):
        key = (product_id, timestamp)
        if key not in self.data:
            self.data[key] = {
                'product_id': product_id,
                'timestamp': timestamp,
                'review_count_last_hour': 0,
                'review_count_last_day': 0,
                'average_velocity_last_7_days': 0.0,
                'is_anomaly': False
            }
        return self.data[key]

    def save(self, entry):
        key = (entry['product_id'], entry['timestamp'])
        self.data[key] = entry
        
    def get_hourly_entries_for_day(self, product_id, date):
        # Helper to sum up daily counts for a product
        daily_entries = []
        for (p_id, ts), entry in self.data.items():
            if p_id == product_id and ts.date() == date:
                daily_entries.append(entry)
        return daily_entries

db_mock_review_velocity = MockReviewVelocityDB() # Using mock for pseudocode

# Placeholder for triggering velocity calculation (Task 1.1.3)
def trigger_velocity_calculation(product_id, timestamp):
    print(f"Triggering velocity calculation for product {product_id} at {timestamp}")
    # In a real system, this would push a message to a queue
    # or directly call the velocity detection service.
    # For now, we'll simulate a direct call for simplicity in pseudocode.
    # from .velocity_detection_service import calculate_and_flag_velocity_anomalies
    # calculate_and_flag_velocity_anomalies(product_id, timestamp)


def process_new_review_event(review_data):
    """
    Processes a new review event, updating review velocity data.
    """
    product_id = review_data.get('product_id')
    created_at_str = review_data.get('created_at') # ISO format string

    if not product_id or not created_at_str:
        print("Invalid review event data: product_id or created_at missing.")
        return

    try:
        # Ensure created_at is timezone-aware
        created_at = datetime.fromisoformat(created_at_str).astimezone(timezone.utc)
    except ValueError:
        print(f"Invalid datetime format for created_at: {created_at_str}")
        return
    
    # Round timestamp to the nearest hour (start of the hour)
    hourly_timestamp = created_at.replace(minute=0, second=0, microsecond=0)
    
    # Get or create the hourly velocity entry
    velocity_entry = db_mock_review_velocity.find_or_create(
        product_id=product_id, 
        timestamp=hourly_timestamp
    )
    
    # Increment hourly count
    velocity_entry['review_count_last_hour'] += 1
    
    # For `review_count_last_day`, this requires summing up all hourly entries for the current day.
    # For simplicity in this ingestion service, we'll just update the current hourly entry.
    # A separate daily aggregation job or a more complex query will sum up the daily total.
    # In a real scenario, this would involve querying the last 24 hours or having a daily aggregated table.
    # For MVP, we defer exact daily sum calculation to the detection algorithm or a nightly job.

    db_mock_review_velocity.save(velocity_entry)

    print(f"Updated velocity for product {product_id} at {hourly_timestamp}. Current hour count: {velocity_entry['review_count_last_hour']}")

    # After ingestion, trigger the velocity detection logic
    trigger_velocity_calculation(product_id, hourly_timestamp)

# Example usage (simulating a Kafka consumer)
if __name__ == "__main__":
    print("Simulating ReviewIngestionService...")
    
    # Simulate a new review for product P1
    review1 = {
        'review_id': 'R1',
        'product_id': 'P1',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    process_new_review_event(review1)

    # Simulate another review for the same product in the same hour
    review2 = {
        'review_id': 'R2',
        'product_id': 'P1',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    process_new_review_event(review2)

    # Simulate a review for a different product
    review3 = {
        'review_id': 'R3',
        'product_id': 'P2',
        'created_at': (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    }
    process_new_review_event(review3)

    # You would typically have a consumer loop here:
    # consumer = KafkaConsumer('new-product-reviews', ...)
    # for message in consumer:
    #     review_data = json.loads(message.value.decode('utf-8'))
    #     process_new_review_event(review_data)
