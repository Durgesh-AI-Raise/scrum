import datetime
from collections import deque
import statistics
import json
import uuid

# Task 1.1: Data Model for Review Event
# This represents an incoming review event.
# In a real system, this would be validated upon ingestion.
#
# review_event = {
#     "reviewId": "r12345",
#     "productId": "p98765",
#     "reviewerId": "u54321",
#     "timestamp": "2023-10-27T10:30:00Z", # ISO 8601 format
#     "rating": 5,
#     "countryCode": "US"
# }

# Task 1.2: Pseudocode for Data Ingestion Service
# This service would typically consume from a message queue (e.g., Kafka)
# and store the events in a time-series optimized data store.
class ReviewIngestionService:
    def __init__(self, storage_client=None):
        self.storage_client = storage_client # Placeholder for a database client

    def ingest_event(self, review_event):
        # In a real system:
        # 1. Validate review_event schema
        # 2. Add processing metadata (e.g., ingestion timestamp)
        # 3. Store in a time-series database (e.g., InfluxDB, Cassandra, or a NoSQL DB like MongoDB indexed by timestamp/productId)
        # For this pseudocode, we just print
        if all(k in review_event for k in ["reviewId", "productId", "timestamp"]):
            print(f"Ingesting review event: {review_event['reviewId']} for product {review_event['productId']} at {review_event['timestamp']}")
            # Example storage: self.storage_client.insert(review_event)
            return True
        else:
            print(f"ERROR: Malformed review event: {review_event}")
            return False

# Task 1.3: Algorithm to detect volume spikes
class ReviewSpikeDetector:
    def __init__(self, window_size_minutes=15, historical_window_hours=24, std_dev_threshold=3.0, min_reviews_for_spike=10):
        """
        Initializes the ReviewSpikeDetector.

        Args:
            window_size_minutes (int): The duration of a single aggregation window in minutes.
            historical_window_hours (int): The duration of the historical data window to consider for baseline calculation.
            std_dev_threshold (float): Number of standard deviations above the average to consider a spike.
            min_reviews_for_spike (int): Minimum number of reviews in a window for a spike to be considered valid.
        """
        self.window_size = datetime.timedelta(minutes=window_size_minutes)
        self.historical_window = datetime.timedelta(hours=historical_window_hours)
        self.std_dev_threshold = std_dev_threshold
        self.min_reviews_for_spike = min_reviews_for_spike
        
        # In a real system, this would be a persistent data store storing aggregated counts
        # {productId: deque({"timestamp": ISO_STRING, "count": INT})}
        self.product_review_history = {} 

    def _get_historical_counts(self, product_id, current_time):
        """
        Retrieves relevant historical review counts for a given product.
        In a real system, this would query a database.
        """
        if product_id not in self.product_review_history:
            return []
        
        relevant_history = []
        # Create a list copy to iterate safely if deque is modified elsewhere
        for event in list(self.product_review_history[product_id]): 
            event_time = datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            if current_time - event_time <= self.historical_window:
                relevant_history.append(event['count'])
        return relevant_history

    def detect_spike(self, product_id, current_window_review_count, current_window_end_time_iso):
        """
        Detects if a review volume spike has occurred for a product.

        Args:
            product_id (str): The ID of the product.
            current_window_review_count (int): The number of reviews in the current window.
            current_window_end_time_iso (str): ISO 8601 string for the end time of the current window.

        Returns:
            dict or None: A dictionary with spike details if detected, otherwise None.
        """
        current_time = datetime.datetime.fromisoformat(current_window_end_time_iso.replace('Z', '+00:00'))

        # Update history with the current window's data
        if product_id not in self.product_review_history:
            # maxlen is approximate; ensure enough history is kept
            self.product_review_history[product_id] = deque(maxlen=int(self.historical_window.total_seconds() / self.window_size.total_seconds()) + 5)
        self.product_review_history[product_id].append({
            "timestamp": current_window_end_time_iso,
            "count": current_window_review_count
        })

        historical_counts = self._get_historical_counts(product_id, current_time)

        # Need sufficient historical data to establish a reliable baseline
        if len(historical_counts) < 5: 
            return None 

        avg_volume = statistics.mean(historical_counts)
        std_dev_volume = statistics.stdev(historical_counts) if len(historical_counts) > 1 else 0

        # Calculate the threshold for a spike
        spike_threshold = avg_volume + (self.std_dev_threshold * std_dev_volume)

        # Check for spike conditions
        if current_window_review_count >= self.min_reviews_for_spike and current_window_review_count > spike_threshold:
            return {
                "productId": product_id,
                "spikeDetected": True,
                "currentVolume": current_window_review_count,
                "averageVolume": avg_volume,
                "stdDevVolume": std_dev_volume,
                "threshold": spike_threshold,
                "timestamp": current_window_end_time_iso,
                "reason": f"Review volume ({current_window_review_count}) significantly higher than historical average ({avg_volume:.2f} + {self.std_dev_threshold}*{std_dev_volume:.2f} = {spike_threshold:.2f})."
            }
        return None

# Task 1.4: Implement alerting mechanism for detected spikes
# This class integrates spike detection with an alerting mechanism.
class ReviewSpikeDetectionService(ReviewSpikeDetector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # In a real system, this would be a Kafka producer or a client for a dedicated alert database
        self.alert_publisher = self._initialize_alert_publisher()

    def _initialize_alert_publisher(self):
        # Placeholder for initializing a messaging queue producer or database client
        print("INFO: Initialized alert publisher (placeholder).")
        return None # In a real system, return a KafkaProducer or DB client instance

    def _publish_alert(self, alert_data):
        """
        Publishes the detected alert.
        In a real system, this would send a message to a topic or save to an alert database.
        """
        print(f"\n--- REVIEW VOLUME SPIKE ALERT ---")
        print(f"Alert ID: {alert_data['alertId']}")
        print(f"Type: {alert_data['type']}")
        print(f"Entity ID: {alert_data['entityId']}")
        print(f"Timestamp: {alert_data['timestamp']}")
        print(f"Severity: {alert_data['severity']}")
        print(f"Reason: {alert_data['details']['reason']}")
        print(f"Details: {json.dumps(alert_data['details'], indent=2)}")
        print(f"---------------------------------\n")
        # Example for real system:
        # if self.alert_publisher:
        #     self.alert_publisher.send('moderation_alerts_topic', value=json.dumps(alert_data).encode('utf-8'))
        # else:
        #     print("WARNING: Alert publisher not configured, printing to console.")

    def process_review_counts_and_alert(self, product_id, current_window_review_count, current_window_end_time_iso):
        """
        Processes aggregated review counts, detects spikes, and publishes alerts if found.
        """
        spike_details = self.detect_spike(product_id, current_window_review_count, current_window_end_time_iso)
        if spike_details:
            # Data Model for Alert Event
            alert_event = {
                "alertId": str(uuid.uuid4()), # Generate a unique ID for the alert
                "type": "REVIEW_VOLUME_SPIKE",
                "entityId": product_id,
                "timestamp": current_window_end_time_iso,
                "severity": "HIGH",
                "details": spike_details,
                "status": "NEW" # Status for moderator dashboard (NEW, ACKNOWLEDGED, RESOLVED)
            }
            self._publish_alert(alert_event)
        return spike_details

# Example Usage (for demonstration purposes)
if __name__ == '__main__':
    print("--- Demonstrating Review Volume Spike Detection and Alerting ---")

    ingestion_service = ReviewIngestionService()
    spike_detection_service = ReviewSpikeDetectionService(
        window_size_minutes=5, 
        historical_window_hours=1, 
        std_dev_threshold=2.5, 
        min_reviews_for_spike=5
    )
    
    product_A = "prod-X789"
    current_time_dt = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)

    print("\n--- Simulating normal activity for Product A ---")
    for i in range(15): # Simulate 15 windows (75 minutes) of normal activity
        # Simulate review events being ingested and then aggregated into counts
        # In a real system, these 'current_window_review_count' would come from an aggregation job
        count = 3 + (i % 3) # Cycles between 3, 4, 5 reviews per 5-min window
        timestamp_iso = (current_time_dt + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
        
        # Simulate ingestion (optional for this demo, focusing on detection)
        # for _ in range(count):
        #     ingestion_service.ingest_event({"reviewId": str(uuid.uuid4()), "productId": product_A, "timestamp": timestamp_iso, "reviewerId": "u"+str(uuid.uuid4())[:8]})

        result = spike_detection_service.process_review_counts_and_alert(product_A, count, timestamp_iso)
        if not result:
            print(f"[{timestamp_iso}] No spike detected for {product_A}. Count: {count}")

    print("\n--- Simulating a spike for Product A ---")
    spike_count = 35 # Significantly higher
    spike_timestamp_iso = (current_time_dt + datetime.timedelta(minutes=15*5)).isoformat().replace('+00:00', 'Z')
    result = spike_detection_service.process_review_counts_and_alert(product_A, spike_count, spike_timestamp_iso)
    if result and result['spikeDetected']:
        print(f"[{spike_timestamp_iso}] Successfully detected spike and alerted for {product_A}. Count: {spike_count}")
    else:
        print(f"[{spike_timestamp_iso}] Failed to detect spike for {product_A}. Count: {spike_count}")

    print("\n--- Simulating post-spike normal activity for Product A ---")
    for i in range(16, 20):
        count = 4 + (i % 2) # Cycles between 4, 5 reviews per 5-min window
        timestamp_iso = (current_time_dt + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
        result = spike_detection_service.process_review_counts_and_alert(product_A, count, timestamp_iso)
        if not result:
            print(f"[{timestamp_iso}] No spike detected for {product_A}. Count: {count}")