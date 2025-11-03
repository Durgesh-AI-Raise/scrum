import unittest
from unittest.mock import MagicMock, patch
import datetime
import json
from collections import deque
import statistics

# Assuming review_volume_detection.py is available or its classes are imported
# For self-contained execution, we'll re-define simplified versions or assume imports.
# In a real project, you would typically import like this:
# from review_volume_detection import ReviewIngestionService, ReviewSpikeDetector, ReviewSpikeDetectionService

# --- Mocking the classes from review_volume_detection.py for testing purposes ---
# These mocks are simplified to allow the test suite to be self-contained and executable.
# In a real scenario, you'd import the actual classes and mock their dependencies.

class MockReviewIngestionService:
    def ingest_event(self, review_event):
        # Simplified validation for testing
        if all(k in review_event for k in ["reviewId", "productId", "timestamp"]):
            return True
        return False

class MockReviewSpikeDetector:
    def __init__(self, window_size_minutes=15, historical_window_hours=24, std_dev_threshold=3.0, min_reviews_for_spike=10):
        self.window_size = datetime.timedelta(minutes=window_size_minutes)
        self.historical_window = datetime.timedelta(hours=historical_window_hours)
        self.std_dev_threshold = std_dev_threshold
        self.min_reviews_for_spike = min_reviews_for_spike
        self.product_review_history = {}

    def _get_historical_counts(self, product_id, current_time):
        if product_id not in self.product_review_history:
            return []
        
        relevant_history = []
        for event in list(self.product_review_history[product_id]):
            event_time = datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            if current_time - event_time <= self.historical_window:
                relevant_history.append(event['count'])
        return relevant_history

    def detect_spike(self, product_id, current_window_review_count, current_window_end_time_iso):
        current_time = datetime.datetime.fromisoformat(current_window_end_time_iso.replace('Z', '+00:00'))

        if product_id not in self.product_review_history:
            self.product_review_history[product_id] = deque(maxlen=int(self.historical_window.total_seconds() / self.window_size.total_seconds()) + 5)
        self.product_review_history[product_id].append({
            "timestamp": current_window_end_time_iso,
            "count": current_window_review_count
        })

        historical_counts = self._get_historical_counts(product_id, current_time)

        if len(historical_counts) < 5: # Need sufficient historical data to establish a reliable baseline
            return None

        avg_volume = statistics.mean(historical_counts)
        std_dev_volume = statistics.stdev(historical_counts) if len(historical_counts) > 1 else 0
        spike_threshold = avg_volume + (self.std_dev_threshold * std_dev_volume)

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

class MockReviewSpikeDetectionService(MockReviewSpikeDetector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mock the alert publisher to capture calls without needing a real message queue
        self.alert_publisher = MagicMock()

    def _publish_alert(self, alert_data):
        self.alert_publisher.send(alert_data) # This will record the call to the mock

    def process_review_counts_and_alert(self, product_id, current_window_review_count, current_window_end_time_iso):
        spike_details = self.detect_spike(product_id, current_window_review_count, current_window_end_time_iso)
        if spike_details:
            # Data Model for Alert Event (simplified alertId for consistent testing)
            alert_event = {
                "alertId": "test-alert-id", 
                "type": "REVIEW_VOLUME_SPIKE",
                "entityId": product_id,
                "timestamp": current_window_end_time_iso,
                "severity": "HIGH",
                "details": spike_details,
                "status": "NEW"
            }
            self._publish_alert(alert_event)
        return spike_details


class TestReviewVolumeDetection(unittest.TestCase):

    def test_ingest_event_valid(self):
        ingestion_service = MockReviewIngestionService()
        valid_event = {
            "reviewId": "r1", "productId": "p1", "reviewerId": "u1",
            "timestamp": "2023-01-01T10:00:00Z", "rating": 5, "countryCode": "US"
        }
        self.assertTrue(ingestion_service.ingest_event(valid_event))

    def test_ingest_event_invalid_missing_product_id(self):
        ingestion_service = MockReviewIngestionService()
        invalid_event = {
            "reviewId": "r2", "reviewerId": "u2", 
            "timestamp": "2023-01-01T10:05:00Z", "rating": 4, "countryCode": "GB"
        }
        self.assertFalse(ingestion_service.ingest_event(invalid_event))

    def test_ingest_event_invalid_missing_timestamp(self):
        ingestion_service = MockReviewIngestionService()
        invalid_event = {
            "reviewId": "r3", "productId": "p3", "reviewerId": "u3", 
            "rating": 3, "countryCode": "CA"
        }
        self.assertFalse(ingestion_service.ingest_event(invalid_event))

    def test_detect_spike_no_spike(self):
        detector = MockReviewSpikeDetector(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.5, min_reviews_for_spike=5)
        product_id = "prod-X"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        # Populate historical data with normal fluctuations
        for i in range(12): # Simulate 1 hour of data (12 windows of 5 minutes)
            count = 5 + (i % 2) # Alternating 5 and 6 reviews
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            detector.detect_spike(product_id, count, timestamp) # This builds history, but shouldn't trigger a spike

        # Test current window with normal volume, ensuring no spike is detected
        current_time = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        result = detector.detect_spike(product_id, 6, current_time)
        self.assertIsNone(result)

    def test_detect_spike_with_clear_spike(self):
        detector = MockReviewSpikeDetector(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.0, min_reviews_for_spike=5)
        product_id = "prod-Y"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        # Populate historical data with normal fluctuations
        for i in range(12): # Simulate 1 hour of data
            count = 5 + (i % 2)
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            detector.detect_spike(product_id, count, timestamp)

        # Test current window with a clear spike
        current_time = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        spike_count = 25 # Significantly higher than historical average
        result = detector.detect_spike(product_id, spike_count, current_time)
        self.assertIsNotNone(result)
        self.assertTrue(result['spikeDetected'])
        self.assertEqual(result['productId'], product_id)
        self.assertEqual(result['currentVolume'], spike_count)
        self.assertIn("significantly higher", result['reason'])

    def test_detect_spike_insufficient_historical_data(self):
        detector = MockReviewSpikeDetector(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.0, min_reviews_for_spike=5)
        product_id = "prod-Z"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        # Only a few data points (less than 5, which is the internal threshold for std_dev calculation)
        for i in range(3):
            count = 5
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            detector.detect_spike(product_id, count, timestamp)

        current_time = (base_time + datetime.timedelta(minutes=3*5)).isoformat().replace('+00:00', 'Z')
        result = detector.detect_spike(product_id, 20, current_time) # Even if count is high
        self.assertIsNone(result) # Should not detect spike due to insufficient historical data

    def test_detect_spike_below_min_reviews_for_spike_threshold(self):
        detector = MockReviewSpikeDetector(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.0, min_reviews_for_spike=10) # Set min_reviews_for_spike high
        product_id = "prod-W"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        for i in range(12):
            count = 5 + (i % 2) # Normal historical count
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            detector.detect_spike(product_id, count, timestamp)

        current_time = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        spike_count_below_min = 8 # This count might be above threshold but below min_reviews_for_spike
        result = detector.detect_spike(product_id, spike_count_below_min, current_time)
        self.assertIsNone(result) # Should not detect spike if current count is below min_reviews_for_spike

    def test_detect_spike_high_std_dev_threshold(self):
        detector = MockReviewSpikeDetector(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=5.0, min_reviews_for_spike=5) # High threshold
        product_id = "prod-HighThresh"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        for i in range(12):
            count = 5 + (i % 2)
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            detector.detect_spike(product_id, count, timestamp)
        
        current_time = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        # A count that would be a spike with a lower threshold, but not with 5.0 std_dev_threshold
        result = detector.detect_spike(product_id, 15, current_time)
        self.assertIsNone(result)

    @patch('uuid.uuid4', return_value=type('obj', (object,), {'hex': 'mock-uuid-hex'})) # Mock uuid.uuid4 to get consistent alertId for testing
    def test_process_review_counts_and_alert_on_spike(self, mock_uuid4):
        service = MockReviewSpikeDetectionService(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.0, min_reviews_for_spike=5)
        product_id = "prod-Alert"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        # Populate historical data without triggering alerts
        for i in range(12):
            count = 5 + (i % 2)
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            service.process_review_counts_and_alert(product_id, count, timestamp)
            service.alert_publisher.send.reset_mock() # Reset mock to only check calls for the spike itself

        # Trigger a spike and verify alert
        spike_count = 30
        spike_timestamp = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        result = service.process_review_counts_and_alert(product_id, spike_count, spike_timestamp)

        self.assertIsNotNone(result)
        self.assertTrue(result['spikeDetected'])
        service.alert_publisher.send.assert_called_once() # Ensure the alert publisher was called exactly once
        
        # Verify the content of the sent alert
        called_alert = service.alert_publisher.send.call_args[0][0]
        self.assertEqual(called_alert['alertId'], "test-alert-id")
        self.assertEqual(called_alert['type'], "REVIEW_VOLUME_SPIKE")
        self.assertEqual(called_alert['entityId'], product_id)
        self.assertEqual(called_alert['timestamp'], spike_timestamp)
        self.assertEqual(called_alert['severity'], "HIGH")
        self.assertEqual(called_alert['status'], "NEW")
        self.assertEqual(called_alert['details']['currentVolume'], spike_count)
        self.assertIn("significantly higher", called_alert['details']['reason'])

    def test_process_review_counts_and_alert_no_spike(self):
        service = MockReviewSpikeDetectionService(window_size_minutes=5, historical_window_hours=1, std_dev_threshold=2.0, min_reviews_for_spike=5)
        product_id = "prod-NoAlert"
        base_time = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        # Populate historical data with normal fluctuations
        for i in range(12): 
            count = 5 + (i % 2)
            timestamp = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            service.detect_spike(product_id, count, timestamp) # Build history

        # Process a window with normal volume, ensure no alert is sent
        current_time = (base_time + datetime.timedelta(minutes=12*5)).isoformat().replace('+00:00', 'Z')
        result = service.process_review_counts_and_alert(product_id, 7, current_time)
        self.assertIsNone(result)
        service.alert_publisher.send.assert_not_called() # Ensure no alert was published

if __name__ == '__main__':
    unittest.main()