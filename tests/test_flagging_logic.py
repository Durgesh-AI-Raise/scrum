import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from backend.flagging_logic import flag_review, SUSPICIOUS_KEYWORDS, VELOCITY_THRESHOLD_HOURS, VELOCITY_THRESHOLD_COUNT

@pytest.fixture
def mock_db_client():
    mock = Mock()
    mock.count_reviews_for_product_in_window.return_value = 0
    mock.check_for_duplicate_review_text.return_value = False
    return mock

def test_review_with_suspicious_keyword_is_flagged(mock_db_client):
    review_data = {
        "review_id": "r1",
        "product_id": "p1",
        "user_id": "u1",
        "review_text": f"This product is a total {SUSPICIOUS_KEYWORDS[0]}!",
        "rating": 1,
        "submission_date": datetime.utcnow().isoformat()
    }
    flagged_review = flag_review(review_data, mock_db_client)
    assert flagged_review['is_flagged'] is True
    assert "Suspicious keyword usage detected." in flagged_review['flag_reason']
    assert flagged_review['flag_date'] is not None

def test_review_with_high_velocity_is_flagged(mock_db_client):
    mock_db_client.count_reviews_for_product_in_window.return_value = VELOCITY_THRESHOLD_COUNT
    review_data = {
        "review_id": "r2",
        "product_id": "p2",
        "user_id": "u2",
        "review_text": "Great product!",
        "rating": 5,
        "submission_date": datetime.utcnow().isoformat()
    }
    flagged_review = flag_review(review_data, mock_db_client)
    assert flagged_review['is_flagged'] is True
    assert f"Unusual review velocity detected for product (>{VELOCITY_THRESHOLD_COUNT} in {VELOCITY_THRESHOLD_HOURS}h)." in flagged_review['flag_reason']
    assert flagged_review['flag_date'] is not None

def test_review_with_duplicate_content_is_flagged(mock_db_client):
    mock_db_client.check_for_duplicate_review_text.return_value = True
    review_data = {
        "review_id": "r3",
        "product_id": "p3",
        "user_id": "u3",
        "review_text": "Very happy with this purchase.",
        "rating": 4,
        "submission_date": datetime.utcnow().isoformat()
    }
    flagged_review = flag_review(review_data, mock_db_client)
    assert flagged_review['is_flagged'] is True
    assert "Duplicate review content detected." in flagged_review['flag_reason']
    assert flagged_review['flag_date'] is not None

def test_non_suspicious_review_is_not_flagged(mock_db_client):
    review_data = {
        "review_id": "r4",
        "product_id": "p4",
        "user_id": "u4",
        "review_text": "This is a genuine and positive review.",
        "rating": 5,
        "submission_date": datetime.utcnow().isoformat()
    }
    flagged_review = flag_review(review_data, mock_db_client)
    assert flagged_review['is_flagged'] is False
    assert flagged_review['flag_reason'] is None
    assert flagged_review['flag_date'] is None

def test_review_with_multiple_flags(mock_db_client):
    mock_db_client.count_reviews_for_product_in_window.return_value = VELOCITY_THRESHOLD_COUNT
    mock_db_client.check_for_duplicate_review_text.return_value = False # Not duplicating but high velocity
    review_data = {
        "review_id": "r5",
        "product_id": "p5",
        "user_id": "u5",
        "review_text": f"This is a {SUSPICIOUS_KEYWORDS[0]} product and a total waste!",
        "rating": 1,
        "submission_date": datetime.utcnow().isoformat()
    }
    flagged_review = flag_review(review_data, mock_db_client)
    assert flagged_review['is_flagged'] is True
    assert "Suspicious keyword usage detected." in flagged_review['flag_reason']
    assert f"Unusual review velocity detected for product (>{VELOCITY_THRESHOLD_COUNT} in {VELOCITY_THRESHOLD_HOURS}h)." in flagged_review['flag_reason']
    assert flagged_review['flag_date'] is not None