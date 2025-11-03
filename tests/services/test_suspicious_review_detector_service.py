import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import json
from typing import List, Dict

# Assuming the SuspiciousReviewDetectorService is in app/services/suspicious_review_detector_service.py
# For testing, we create a mock version that includes the rule logic.
# In a real scenario, you'd import the actual service and mock its dependencies.

class MockSuspiciousReviewDetectorService:
    """
    A mock version of the service to facilitate testing without actual MQ/DB connections.
    Includes the rule logic from the actual service for isolated testing.
    """
    def __init__(self):
        self.flagged_events = [] # To capture events that would be published
        self.suspicious_keywords = ["best product ever!!!", "super great", "must buy", "amazing quality"]

    def _process_review_event(self, message: str):
        review_data = json.loads(message)
        review_id = review_data['review_id']
        product_id = review_data['product_id']
        user_id = review_data['user_id']
        rating = review_data['rating']
        review_text = review_data['review_text']
        submission_timestamp = datetime.fromisoformat(review_data['submission_timestamp'].replace('Z', '+00:00'))
        user_creation_timestamp_str = review_data.get('user_creation_timestamp')
        user_creation_timestamp = datetime.fromisoformat(user_creation_timestamp_str.replace('Z', '+00:00')) if user_creation_timestamp_str else None

        flagged_rules = []

        # Mock fetching additional data for rules - test cases will inject this via _mock_ attributes
        user_reviews_history = getattr(self, '_mock_user_reviews_history', [])
        product_stats = getattr(self, '_mock_product_stats', {})


        # Apply Rule 1: Rapid Submission Velocity
        if self._check_rapid_submission_velocity(user_id, submission_timestamp, user_creation_timestamp, user_reviews_history):
            flagged_rules.append("RapidSubmissionVelocity")

        # Apply Rule 2: Unusual Rating Deviation
        if self._check_unusual_rating_deviation(product_id, rating, product_stats):
            flagged_rules.append("UnusualRatingDeviation")

        # Apply Rule 3: Repetitive Phrases
        if self._check_repetitive_phrases(review_text):
            flagged_rules.append("RepetitivePhrases")

        if flagged_rules:
            flagged_event = {
                "review_id": review_id,
                "flagged_by_rules": flagged_rules,
                "flagging_timestamp": datetime.now().isoformat()
            }
            self.flagged_events.append(flagged_event)

    def _check_rapid_submission_velocity(self, user_id: str, current_review_timestamp: datetime, user_creation_timestamp: datetime, user_reviews_history: List[datetime]) -> bool:
        """
        Rule 1: Rapid Submission Velocity
        Criteria:
        * User Account Age: Less than 24 hours old.
        * Review Count: Submits more than 5 reviews (including current one).
        * Time Window: Within a 60-minute period (relative to current review).
        """
        if not user_creation_timestamp or (current_review_timestamp - user_creation_timestamp).total_seconds() / 3600 >= 24:
            return False

        recent_reviews_count = 0
        time_window_start = current_review_timestamp - timedelta(minutes=60)

        for timestamp in user_reviews_history:
            if time_window_start <= timestamp < current_review_timestamp:
                recent_reviews_count += 1

        recent_reviews_count += 1 # Include the current review
        return recent_reviews_count > 5

    def _check_unusual_rating_deviation(self, product_id: str, review_rating: int, product_stats: Dict) -> bool:
        """
        Rule 2: Unusual Rating Deviation
        Criteria:
        * Product Review Count: Product has more than 100 existing reviews.
        * Rating Deviation: The review's rating is more than 2 standard deviations away from the product's current average rating.
        """
        total_reviews_count = product_stats.get("total_reviews_count", 0)
        if total_reviews_count <= 100:
            return False

        avg_rating = product_stats.get("average_rating")
        std_dev = product_stats.get("standard_deviation")

        if avg_rating is None or std_dev is None or std_dev == 0:
            return False

        z_score = (review_rating - avg_rating) / std_dev
        return abs(z_score) > 2

    def _check_repetitive_phrases(self, review_text: str) -> bool:
        """
        Rule 3: Repetitive Phrases (Basic Keyword Matching)
        Criteria:
        * The presence of more than one instance of a suspicious keyword/phrase in a single review.
        """
        detected_keywords_count = 0
        for keyword in self.suspicious_keywords:
            if keyword.lower() in review_text.lower():
                detected_keywords_count += 1
        return detected_keywords_count > 1

# --- Test Cases ---

@pytest.fixture
def detector_service():
    """Provides a fresh mock detector service for each test."""
    return MockSuspiciousReviewDetectorService()

def test_rapid_submission_velocity_flags_new_user_rapid_reviews(detector_service):
    """
    Test case for Rule 1: Rapid Submission Velocity.
    A new user submits more than 5 reviews within 60 minutes.
    """
    user_creation = datetime(2025, 1, 1, 9, 0, 0)
    review_timestamps = [
        datetime(2025, 1, 1, 9, 5, 0),
        datetime(2025, 1, 1, 9, 10, 0),
        datetime(2025, 1, 1, 9, 15, 0),
        datetime(2025, 1, 1, 9, 20, 0),
        datetime(2025, 1, 1, 9, 25, 0)
    ] # 5 reviews prior to current
    current_review_time = datetime(2025, 1, 1, 9, 30, 0) # This makes it the 6th review, within 30 mins of creation and 60 mins of first review

    detector_service._mock_user_reviews_history = review_timestamps # Inject mock history

    mock_event = {
        "review_id": "r1", "product_id": "p1", "user_id": "u1", "rating": 5,
        "review_text": "Good product.",
        "submission_timestamp": current_review_time.isoformat() + "Z",
        "user_creation_timestamp": user_creation.isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 1
    assert detector_service.flagged_events[0]['review_id'] == "r1"
    assert "RapidSubmissionVelocity" in detector_service.flagged_events[0]['flagged_by_rules']

def test_rapid_submission_velocity_does_not_flag_old_user(detector_service):
    """
    Test case for Rule 1: Rapid Submission Velocity.
    An old user submits many reviews, should not be flagged.
    """
    user_creation = datetime(2024, 1, 1, 9, 0, 0) # User created long ago
    review_timestamps = [
        datetime(2025, 1, 1, 9, 5, 0),
        datetime(2025, 1, 1, 9, 10, 0),
        datetime(2025, 1, 1, 9, 15, 0),
        datetime(2025, 1, 1, 9, 20, 0),
        datetime(2025, 1, 1, 9, 25, 0)
    ]
    current_review_time = datetime(2025, 1, 1, 9, 30, 0)

    detector_service._mock_user_reviews_history = review_timestamps

    mock_event = {
        "review_id": "r2", "product_id": "p1", "user_id": "u2", "rating": 5,
        "review_text": "Good product.",
        "submission_timestamp": current_review_time.isoformat() + "Z",
        "user_creation_timestamp": user_creation.isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 0 # Should not be flagged

def test_rapid_submission_velocity_does_not_flag_new_user_few_reviews(detector_service):
    """
    Test case for Rule 1: Rapid Submission Velocity.
    A new user submits fewer than 6 reviews within 60 minutes.
    """
    user_creation = datetime(2025, 1, 1, 9, 0, 0)
    review_timestamps = [
        datetime(2025, 1, 1, 9, 5, 0),
        datetime(2025, 1, 1, 9, 10, 0),
        datetime(2025, 1, 1, 9, 15, 0)
    ] # 3 reviews prior to current
    current_review_time = datetime(2025, 1, 1, 9, 20, 0) # This makes it the 4th review

    detector_service._mock_user_reviews_history = review_timestamps

    mock_event = {
        "review_id": "r_few", "product_id": "p_few", "user_id": "u_few", "rating": 5,
        "review_text": "Good product.",
        "submission_timestamp": current_review_time.isoformat() + "Z",
        "user_creation_timestamp": user_creation.isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 0 # Should not be flagged

def test_unusual_rating_deviation_flags_low_rating_high_avg(detector_service):
    """
    Test case for Rule 2: Unusual Rating Deviation.
    A 1-star review for a product with high average rating and low std dev.
    """
    product_stats = {
        "average_rating": 4.5,
        "standard_deviation": 0.3,
        "total_reviews_count": 200 # Sufficient reviews
    }
    detector_service._mock_product_stats = product_stats

    mock_event = {
        "review_id": "r3", "product_id": "p2", "user_id": "u3", "rating": 1,
        "review_text": "Terrible product, completely useless.",
        "submission_timestamp": datetime.now().isoformat() + "Z",
        "user_creation_timestamp": (datetime.now() - timedelta(days=10)).isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 1
    assert detector_service.flagged_events[0]['review_id'] == "r3"
    assert "UnusualRatingDeviation" in detector_service.flagged_events[0]['flagged_by_rules']

def test_unusual_rating_deviation_does_not_flag_normal_rating(detector_service):
    """
    Test case for Rule 2: Unusual Rating Deviation.
    A 4-star review for a product with high average rating and low std dev.
    """
    product_stats = {
        "average_rating": 4.5,
        "standard_deviation": 0.3,
        "total_reviews_count": 200
    }
    detector_service._mock_product_stats = product_stats

    mock_event = {
        "review_id": "r4", "product_id": "p2", "user_id": "u4", "rating": 4,
        "review_text": "Good product, almost perfect.",
        "submission_timestamp": datetime.now().isoformat() + "Z",
        "user_creation_timestamp": (datetime.now() - timedelta(days=10)).isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 0 # Should not be flagged

def test_unusual_rating_deviation_does_not_flag_insufficient_reviews(detector_service):
    """
    Test case for Rule 2: Unusual Rating Deviation.
    Product has too few reviews for deviation check.
    """
    product_stats = {
        "average_rating": 4.5,
        "standard_deviation": 0.3,
        "total_reviews_count": 50 # Insufficient reviews
    }
    detector_service._mock_product_stats = product_stats

    mock_event = {
        "review_id": "r_insuf", "product_id": "p_insuf", "user_id": "u_insuf", "rating": 1,
        "review_text": "Very bad.",
        "submission_timestamp": datetime.now().isoformat() + "Z",
        "user_creation_timestamp": (datetime.now() - timedelta(days=10)).isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 0 # Should not be flagged

def test_repetitive_phrases_flags_multiple_keywords(detector_service):
    """
    Test case for Rule 3: Repetitive Phrases.
    Review contains multiple suspicious keywords.
    """
    mock_event = {
        "review_id": "r5", "product_id": "p3", "user_id": "u5", "rating": 5,
        "review_text": "This is the best product ever!!! I must buy more, it's super great!",
        "submission_timestamp": datetime.now().isoformat() + "Z",
        "user_creation_timestamp": (datetime.now() - timedelta(days=5)).isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 1
    assert detector_service.flagged_events[0]['review_id'] == "r5"
    assert "RepetitivePhrases" in detector_service.flagged_events[0]['flagged_by_rules']

def test_repetitive_phrases_does_not_flag_single_keyword(detector_service):
    """
    Test case for Rule 3: Repetitive Phrases.
    Review contains only one suspicious keyword (MVP criteria: >1 keyword).
    """
    mock_event = {
        "review_id": "r6", "product_id": "p4", "user_id": "u6", "rating": 4,
        "review_text": "This product is super great, I really like it.",
        "submission_timestamp": datetime.now().isoformat() + "Z",
        "user_creation_timestamp": (datetime.now() - timedelta(days=5)).isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 0 # Should not be flagged

def test_multiple_rules_trigger(detector_service):
    """
    Test case where multiple rules are triggered by a single review.
    """
    user_creation = datetime(2025, 1, 1, 9, 0, 0)
    review_timestamps = [
        datetime(2025, 1, 1, 9, 5, 0), datetime(2025, 1, 1, 9, 10, 0),
        datetime(2025, 1, 1, 9, 15, 0), datetime(2025, 1, 1, 9, 20, 0),
        datetime(2025, 1, 1, 9, 25, 0)
    ]
    current_review_time = datetime(2025, 1, 1, 9, 30, 0)

    detector_service._mock_user_reviews_history = review_timestamps
    detector_service._mock_product_stats = {
        "average_rating": 4.5, "standard_deviation": 0.3, "total_reviews_count": 200
    }

    mock_event = {
        "review_id": "r7", "product_id": "p5", "user_id": "u7", "rating": 1,
        "review_text": "This is the best product ever!!! Absolutely terrible, must buy a different one.",
        "submission_timestamp": current_review_time.isoformat() + "Z",
        "user_creation_timestamp": user_creation.isoformat() + "Z"
    }
    detector_service._process_review_event(json.dumps(mock_event))

    assert len(detector_service.flagged_events) == 1
    assert detector_service.flagged_events[0]['review_id'] == "r7"
    assert "RapidSubmissionVelocity" in detector_service.flagged_events[0]['flagged_by_rules']
    assert "UnusualRatingDeviation" in detector_service.flagged_events[0]['flagged_by_rules']
    assert "RepetitivePhrases" in detector_service.flagged_events[0]['flagged_by_rules']
