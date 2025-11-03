import unittest
from unittest.mock import MagicMock, patch
import datetime
import json
import uuid
import statistics

# --- Mocking the classes from reviewer_abuse_detection.py for testing purposes ---
# These mocks are simplified to allow the test suite to be self-contained and executable.
# In a real scenario, you'd import the actual classes and mock their dependencies.

class MockReviewerActivityIngestionService:
    def __init__(self, activity_db_client=None, product_catalog_service=None):
        self.activity_db_client = activity_db_client if activity_db_client else {} # In-memory mock DB
        self.product_catalog_service = product_catalog_service if product_catalog_service else MagicMock()

    def _get_reviewer_activity(self, reviewer_id):
        return self.activity_db_client.get(reviewer_id, {})

    def _upsert_reviewer_activity(self, reviewer_activity):
        self.activity_db_client[reviewer_activity['reviewerId']] = reviewer_activity

    def _get_product_category(self, product_id):
        # Default mock behavior, can be overridden by test cases
        if self.product_catalog_service.get_category.called:
            return self.product_catalog_service.get_category(product_id)
        return "DefaultCategory" # Simulate a fallback category

    def ingest_review_event(self, review_event, account_creation_date_iso):
        reviewer_id = review_event.get('reviewerId')
        product_id = review_event.get('productId')
        rating = review_event.get('rating')
        timestamp_iso = review_event.get('timestamp')
        review_id = review_event.get('reviewId')

        if not all([reviewer_id, product_id, rating, timestamp_iso, review_id, account_creation_date_iso]):
            return False
        
        reviewer_activity = self._get_reviewer_activity(reviewer_id)
        
        if not reviewer_activity:
            reviewer_activity = {
                "reviewerId": reviewer_id,
                "totalReviews": 0,
                "sumRatings": 0,
                "averageRating": 0.0,
                "productCategoryCounts": {},
                "accountCreationDate": account_creation_date_iso,
                "lastActivityTimestamp": "",
                "associatedReviewIds": []
            }
        
        reviewer_activity["totalReviews"] += 1
        reviewer_activity["sumRatings"] += rating
        reviewer_activity["averageRating"] = reviewer_activity["sumRatings"] / reviewer_activity["totalReviews"]
        reviewer_activity["lastActivityTimestamp"] = max(reviewer_activity["lastActivityTimestamp"], timestamp_iso) if reviewer_activity["lastActivityTimestamp"] else timestamp_iso
        reviewer_activity["associatedReviewIds"].append(review_id)

        category = self._get_product_category(product_id)
        if category:
            reviewer_activity["productCategoryCounts"][category] = reviewer_activity["productCategoryCounts"].get(category, 0) + 1

        self._upsert_reviewer_activity(reviewer_activity)
        return reviewer_activity

class MockUnusualActivityDetector:
    def __init__(self, new_account_threshold_days=14, high_volume_threshold=20, 
                 disparate_category_threshold=5, high_rating_min_avg=4.5, min_reviews_for_disparate=10):
        self.new_account_threshold_days = new_account_threshold_days
        self.high_volume_threshold = high_volume_threshold
        self.disparate_category_threshold = disparate_category_threshold
        self.high_rating_min_avg = high_rating_min_avg
        self.min_reviews_for_disparate = min_reviews_for_disparate

    def detect_patterns(self, reviewer_activity, current_time=None):
        flags = []
        reviewer_id = reviewer_activity['reviewerId']
        total_reviews = reviewer_activity.get('totalReviews', 0)
        average_rating = reviewer_activity.get('averageRating', 0.0)
        product_category_counts = reviewer_activity.get('productCategoryCounts', {})
        account_creation_date_iso = reviewer_activity.get('accountCreationDate')

        if not account_creation_date_iso:
            return flags

        current_time = current_time if current_time else datetime.datetime.now(datetime.timezone.utc)
        account_creation_date = datetime.datetime.fromisoformat(account_creation_date_iso.replace('Z', '+00:00'))

        # Pattern 1: "Brand new accounts with high review volume"
        account_age_days = (current_time - account_creation_date).days
        if account_age_days <= self.new_account_threshold_days and total_reviews >= self.high_volume_threshold:
            flags.append(f"Brand new account (created {account_age_days} days ago) with high review volume ({total_reviews} reviews).")

        # Pattern 2: "Many 5-star reviews across disparate products"
        distinct_categories = len(product_category_counts)
        if (total_reviews >= self.min_reviews_for_disparate and 
            distinct_categories >= self.disparate_category_threshold and 
            average_rating >= self.high_rating_min_avg):
            flags.append(f"High number of reviews ({total_reviews}) with high average rating ({average_rating:.1f}) across {distinct_categories} disparate product categories.")
        
        return flags

class MockFlaggingService:
    def __init__(self, flagged_db_client=None, flagged_reviews_db_client=None):
        self.flagged_db_client = flagged_db_client if flagged_db_client else {} # In-memory mock DB for flagged reviewers
        self.flagged_reviews_db_client = flagged_reviews_db_client if flagged_reviews_db_client else {} # In-memory mock DB for flagged reviews

    def _get_flagged_reviewer(self, reviewer_id):
        return self.flagged_db_client.get(reviewer_id)

    def _upsert_flagged_reviewer(self, flagged_reviewer_data):
        self.flagged_db_client[flagged_reviewer_data['reviewerId']] = flagged_reviewer_data

    def _upsert_flagged_review(self, review_id, flagged_review_data):
        self.flagged_reviews_db_client[review_id] = flagged_review_data

    def flag_reviewer_and_reviews(self, reviewer_id, detected_flags, associated_review_ids, product_id_lookup={}, current_time_iso=None):
        if not detected_flags:
            return
        
        current_time_iso = current_time_iso if current_time_iso else datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

        flagged_reviewer = self._get_flagged_reviewer(reviewer_id)
        if not flagged_reviewer:
            flagged_reviewer = {
                "reviewerId": reviewer_id,
                "flaggedReason": [],
                "firstFlagTimestamp": current_time_iso,
                "lastFlagTimestamp": current_time_iso,
                "status": "ACTIVE",
                "associatedReviewIds": [],
                "metadata": {}
            }
        else:
            flagged_reviewer["lastFlagTimestamp"] = current_time_iso

        for reason in detected_flags:
            if reason not in flagged_reviewer["flaggedReason"]:
                flagged_reviewer["flaggedReason"].append(reason)
        
        for r_id in associated_review_ids:
            if r_id not in flagged_reviewer["associatedReviewIds"]:
                flagged_reviewer["associatedReviewIds"].append(r_id)

        self._upsert_flagged_reviewer(flagged_reviewer)

        for review_id in associated_review_ids:
            flag_entry = {
                "reviewId": review_id,
                "productId": product_id_lookup.get(review_id, "UNKNOWN"),
                "reviewerId": reviewer_id,
                "flagType": "UNUSUAL_ACCOUNT_ACTIVITY",
                "flagReason": "; ".join(detected_flags),
                "flagTimestamp": current_time_iso,
                "status": "NEW"
            }
            self._upsert_flagged_review(review_id, flag_entry)


class TestReviewerAbuseDetection(unittest.TestCase):

    def setUp(self):
        # Reset mock DBs for each test
        self.mock_activity_db = {}
        self.mock_flagged_reviewers_db = {}
        self.mock_flagged_reviews_db = {}
        self.mock_product_catalog = MagicMock()
        self.ingestion_service = MockReviewerActivityIngestionService(
            activity_db_client=self.mock_activity_db,
            product_catalog_service=self.mock_product_catalog
        )
        self.detector = MockUnusualActivityDetector(
            new_account_threshold_days=7,
            high_volume_threshold=5,
            disparate_category_threshold=2,
            high_rating_min_avg=4.0,
            min_reviews_for_disparate=3
        )
        self.flagging_service = MockFlaggingService(
            flagged_db_client=self.mock_flagged_reviewers_db,
            flagged_reviews_db_client=self.mock_flagged_reviews_db
        )

    # --- Tests for ReviewerActivityIngestionService ---
    def test_ingest_review_event_valid_new_reviewer(self):
        reviewer_id = "u1"
        creation_date = "2023-10-20T10:00:00Z"
        review_event = {
            "reviewId": "r1", "productId": "p1", "reviewerId": reviewer_id,
            "timestamp": "2023-10-21T10:00:00Z", "rating": 5, "countryCode": "US"
        }
        self.mock_product_catalog.get_category.return_value = "Electronics"

        updated_activity = self.ingestion_service.ingest_review_event(review_event, creation_date)
        
        self.assertIsNotNone(updated_activity)
        self.assertEqual(updated_activity['reviewerId'], reviewer_id)
        self.assertEqual(updated_activity['totalReviews'], 1)
        self.assertEqual(updated_activity['sumRatings'], 5)
        self.assertEqual(updated_activity['averageRating'], 5.0)
        self.assertEqual(updated_activity['productCategoryCounts'], {"Electronics": 1})
        self.assertEqual(updated_activity['associatedReviewIds'], ["r1"])
        self.assertEqual(self.mock_activity_db[reviewer_id], updated_activity)
        self.mock_product_catalog.get_category.assert_called_once_with("p1")

    def test_ingest_review_event_valid_existing_reviewer(self):
        reviewer_id = "u2"
        creation_date = "2023-10-10T09:00:00Z"
        # Initial activity
        initial_activity = {
            "reviewerId": reviewer_id,
            "totalReviews": 1, "sumRatings": 4, "averageRating": 4.0,
            "productCategoryCounts": {"Books": 1}, "accountCreationDate": creation_date,
            "lastActivityTimestamp": "2023-10-15T11:00:00Z", "associatedReviewIds": ["r_old"]
        }
        self.mock_activity_db[reviewer_id] = initial_activity

        # New review event
        review_event = {
            "reviewId": "r_new", "productId": "p2", "reviewerId": reviewer_id,
            "timestamp": "2023-10-22T12:00:00Z", "rating": 5, "countryCode": "GB"
        }
        self.mock_product_catalog.get_category.return_value = "Movies"

        updated_activity = self.ingestion_service.ingest_review_event(review_event, creation_date)

        self.assertIsNotNone(updated_activity)
        self.assertEqual(updated_activity['totalReviews'], 2)
        self.assertEqual(updated_activity['sumRatings'], 9)
        self.assertEqual(updated_activity['averageRating'], 4.5)
        self.assertEqual(updated_activity['productCategoryCounts'], {"Books": 1, "Movies": 1})
        self.assertEqual(updated_activity['lastActivityTimestamp'], "2023-10-22T12:00:00Z")
        self.assertIn("r_new", updated_activity['associatedReviewIds'])

    def test_ingest_review_event_missing_fields(self):
        reviewer_id = "u3"
        creation_date = "2023-10-20T10:00:00Z"
        invalid_event = {
            "reviewId": "r3", "productId": "p3", # Missing reviewerId
            "timestamp": "2023-10-21T10:00:00Z", "rating": 5, "countryCode": "US"
        }
        result = self.ingestion_service.ingest_review_event(invalid_event, creation_date)
        self.assertFalse(result)
        self.assertNotIn(reviewer_id, self.mock_activity_db) # No activity should be created/updated

    def test_ingest_review_event_product_category_counts(self):
        reviewer_id = "u4"
        creation_date = "2023-10-20T10:00:00Z"
        
        # First review for Electronics
        self.mock_product_catalog.get_category.side_effect = ["Electronics", "Books", "Electronics"]
        review_event_1 = {"reviewId": "r4_1", "productId": "p4_1", "reviewerId": reviewer_id, "timestamp": "2023-10-21T10:00:00Z", "rating": 5, "countryCode": "US"}
        self.ingestion_service.ingest_review_event(review_event_1, creation_date)

        # Second review for Books
        review_event_2 = {"reviewId": "r4_2", "productId": "p4_2", "reviewerId": reviewer_id, "timestamp": "2023-10-21T11:00:00Z", "rating": 4, "countryCode": "US"}
        self.ingestion_service.ingest_review_event(review_event_2, creation_date)

        # Third review for Electronics
        review_event_3 = {"reviewId": "r4_3", "productId": "p4_3", "reviewerId": reviewer_id, "timestamp": "2023-10-21T12:00:00Z", "rating": 5, "countryCode": "US"}
        self.ingestion_service.ingest_review_event(review_event_3, creation_date)

        activity = self.mock_activity_db.get(reviewer_id)
        self.assertIsNotNone(activity)
        self.assertEqual(activity['productCategoryCounts'], {"Electronics": 2, "Books": 1})
        self.assertEqual(self.mock_product_catalog.get_category.call_count, 3)

    # --- Tests for UnusualActivityDetector ---
    @patch('datetime.datetime')
    def test_detect_patterns_new_account_high_volume(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat # Keep original for parsing

        reviewer_activity = {
            "reviewerId": "u_new_high_vol",
            "totalReviews": 10,
            "sumRatings": 45,
            "averageRating": 4.5,
            "productCategoryCounts": {"CatA": 5, "CatB": 5},
            "accountCreationDate": "2023-10-25T10:00:00Z", # 2 days old, less than 7 day threshold
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10"]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertIn("Brand new account (created 2 days ago) with high review volume (10 reviews).", flags)
        self.assertEqual(len(flags), 1)

    @patch('datetime.datetime')
    def test_detect_patterns_old_account_high_volume_no_flag(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_activity = {
            "reviewerId": "u_old_high_vol",
            "totalReviews": 10,
            "sumRatings": 45,
            "averageRating": 4.5,
            "productCategoryCounts": {"CatA": 5, "CatB": 5},
            "accountCreationDate": "2023-01-01T10:00:00Z", # Old account, more than 7 days
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10"]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertNotIn("Brand new account (created", " ".join(flags)) # Should not flag for 'new account'
        self.assertEqual(len(flags), 0)

    @patch('datetime.datetime')
    def test_detect_patterns_disparate_five_star_reviews(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_activity = {
            "reviewerId": "u_disparate_5star",
            "totalReviews": 15, # >= min_reviews_for_disparate (3)
            "sumRatings": 70,
            "averageRating": 4.66, # >= high_rating_min_avg (4.0)
            "productCategoryCounts": {"Electronics": 5, "Books": 5, "Apparel": 5}, # >= disparate_category_threshold (2)
            "accountCreationDate": "2023-01-01T10:00:00Z",
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": [f"r{i}" for i in range(1, 16)]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertIn("High number of reviews (15) with high average rating (4.7) across 3 disparate product categories.", flags)
        self.assertEqual(len(flags), 1)

    @patch('datetime.datetime')
    def test_detect_patterns_insufficient_reviews_for_disparate_no_flag(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_activity = {
            "reviewerId": "u_low_reviews_disparate",
            "totalReviews": 2, # < min_reviews_for_disparate (3)
            "sumRatings": 10,
            "averageRating": 5.0,
            "productCategoryCounts": {"Electronics": 1, "Books": 1},
            "accountCreationDate": "2023-01-01T10:00:00Z",
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": ["r1", "r2"]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertFalse(any("disparate product categories" in f for f in flags))

    @patch('datetime.datetime')
    def test_detect_patterns_low_average_rating_no_flag(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_activity = {
            "reviewerId": "u_low_avg_rating",
            "totalReviews": 10,
            "sumRatings": 30,
            "averageRating": 3.0, # < high_rating_min_avg (4.0)
            "productCategoryCounts": {"Electronics": 5, "Books": 5},
            "accountCreationDate": "2023-01-01T10:00:00Z",
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": [f"r{i}" for i in range(1, 11)]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertFalse(any("disparate product categories" in f for f in flags))

    @patch('datetime.datetime')
    def test_detect_patterns_multiple_flags(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_activity = {
            "reviewerId": "u_multi_flag",
            "totalReviews": 10, # High volume
            "sumRatings": 50,
            "averageRating": 5.0, # High average rating
            "productCategoryCounts": {"Cat1": 3, "Cat2": 3, "Cat3": 4}, # Disparate categories
            "accountCreationDate": "2023-10-26T10:00:00Z", # New account (1 day old)
            "lastActivityTimestamp": "2023-10-27T09:00:00Z",
            "associatedReviewIds": [f"r{i}" for i in range(1, 11)]
        }
        flags = self.detector.detect_patterns(reviewer_activity, current_time=mock_dt.now.return_value)
        self.assertEqual(len(flags), 2)
        self.assertIn("Brand new account (created 1 days ago) with high review volume (10 reviews).", flags)
        self.assertIn("High number of reviews (10) with high average rating (5.0) across 3 disparate product categories.", flags)

    # --- Tests for FlaggingService ---
    @patch('datetime.datetime')
    def test_flag_reviewer_and_reviews_new_flagging(self, mock_dt):
        test_time = datetime.datetime(2023, 10, 27, 12, 30, 0, tzinfo=datetime.timezone.utc)
        mock_dt.now.return_value = test_time
        mock_dt.fromisoformat = datetime.datetime.fromisoformat # To ensure datetime parsing works

        reviewer_id = "u_flag_new"
        detected_flags = ["Pattern A detected"]
        associated_review_ids = ["rev1", "rev2"]
        product_id_lookup = {"rev1": "prod_x", "rev2": "prod_y"}
        
        self.flagging_service.flag_reviewer_and_reviews(reviewer_id, detected_flags, associated_review_ids, product_id_lookup, current_time_iso=test_time.isoformat().replace('+00:00', 'Z'))

        # Verify flagged reviewer
        flagged_reviewer = self.mock_flagged_reviewers_db.get(reviewer_id)
        self.assertIsNotNone(flagged_reviewer)
        self.assertEqual(flagged_reviewer['reviewerId'], reviewer_id)
        self.assertEqual(flagged_reviewer['flaggedReason'], ["Pattern A detected"])
        self.assertEqual(flagged_reviewer['status'], "ACTIVE")
        self.assertEqual(set(flagged_reviewer['associatedReviewIds']), set(associated_review_ids))

        # Verify flagged reviews
        flagged_rev1 = self.mock_flagged_reviews_db.get("rev1")
        self.assertIsNotNone(flagged_rev1)
        self.assertEqual(flagged_rev1['reviewerId'], reviewer_id)
        self.assertEqual(flagged_rev1['productId'], "prod_x")
        self.assertEqual(flagged_rev1['flagReason'], "Pattern A detected")
        self.assertEqual(flagged_rev1['status'], "NEW")

        flagged_rev2 = self.mock_flagged_reviews_db.get("rev2")
        self.assertIsNotNone(flagged_rev2)
        self.assertEqual(flagged_rev2['reviewerId'], reviewer_id)
        self.assertEqual(flagged_rev2['productId'], "prod_y")

    @patch('datetime.datetime')
    def test_flag_reviewer_and_reviews_existing_flagging(self, mock_dt):
        initial_time = datetime.datetime(2023, 10, 26, 10, 0, 0, tzinfo=datetime.timezone.utc)
        later_time = datetime.datetime(2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.now.return_value = later_time
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_id = "u_flag_existing"
        # Pre-exist some flagging data
        self.mock_flagged_reviewers_db[reviewer_id] = {
            "reviewerId": reviewer_id,
            "flaggedReason": ["Old pattern detected"],
            "firstFlagTimestamp": initial_time.isoformat().replace('+00:00', 'Z'),
            "lastFlagTimestamp": initial_time.isoformat().replace('+00:00', 'Z'),
            "status": "ACTIVE",
            "associatedReviewIds": ["old_rev1"],
            "metadata": {}
        }

        new_detected_flags = ["New pattern detected"]
        new_associated_review_ids = ["new_rev1", "new_rev2"]
        product_id_lookup = {"new_rev1": "p_new_1", "new_rev2": "p_new_2"}

        self.flagging_service.flag_reviewer_and_reviews(
            reviewer_id, 
            new_detected_flags, 
            new_associated_review_ids, 
            product_id_lookup,
            current_time_iso=later_time.isoformat().replace('+00:00', 'Z')
        )

        flagged_reviewer = self.mock_flagged_reviewers_db.get(reviewer_id)
        self.assertIsNotNone(flagged_reviewer)
        self.assertIn("Old pattern detected", flagged_reviewer['flaggedReason'])
        self.assertIn("New pattern detected", flagged_reviewer['flaggedReason'])
        self.assertEqual(flagged_reviewer['firstFlagTimestamp'], initial_time.isoformat().replace('+00:00', 'Z')) # Should not change
        self.assertEqual(flagged_reviewer['lastFlagTimestamp'], later_time.isoformat().replace('+00:00', 'Z')) # Should update
        self.assertIn("old_rev1", flagged_reviewer['associatedReviewIds'])
        self.assertIn("new_rev1", flagged_reviewer['associatedReviewIds'])
        self.assertIn("new_rev2", flagged_reviewer['associatedReviewIds'])

    def test_flag_reviewer_and_reviews_empty_flags_no_action(self):
        reviewer_id = "u_no_flag"
        detected_flags = []
        associated_review_ids = ["rev_x"]
        
        self.flagging_service.flag_reviewer_and_reviews(reviewer_id, detected_flags, associated_review_ids)

        self.assertNotIn(reviewer_id, self.mock_flagged_reviewers_db)
        self.assertNotIn("rev_x", self.mock_flagged_reviews_db)

    # --- Integration Test ---
    @patch('datetime.datetime')
    @patch('uuid.uuid4', return_value=type('obj', (object,), {'hex': 'mock-uuid-hex'}))
    def test_full_pipeline_detection_and_flagging(self, mock_uuid4, mock_dt):
        # Setup mock time
        base_time = datetime.datetime(2023, 11, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        mock_dt.now.return_value = base_time
        mock_dt.fromisoformat = datetime.datetime.fromisoformat

        reviewer_id = "u_pipeline_abuser"
        account_creation_date_iso = (base_time - datetime.timedelta(days=3)).isoformat().replace('+00:00', 'Z')

        # Simulate product categories
        product_categories = {
            "pA": "Electronics", "pB": "Books", "pC": "Apparel", "pD": "Toys", "pE": "Home"
        }
        self.mock_product_catalog.get_category.side_effect = lambda pid: product_categories.get(pid, "Misc")

        # Ingest review events to trigger patterns
        review_events = []
        for i in range(6): # 6 reviews in a short period (high volume)
            review_id = f"r{i+1}"
            product_id = list(product_categories.keys())[i % len(product_categories)] # Ensures disparate categories
            rating = 5 if i % 2 == 0 else 4 # High average rating
            timestamp_iso = (base_time + datetime.timedelta(minutes=i*5)).isoformat().replace('+00:00', 'Z')
            event = {
                "reviewId": review_id, "productId": product_id, "reviewerId": reviewer_id,
                "timestamp": timestamp_iso, "rating": rating, "countryCode": "US"
            }
            review_events.append(event)
            self.ingestion_service.ingest_review_event(event, account_creation_date_iso)

        # Get the updated reviewer activity
        current_reviewer_activity = self.mock_activity_db.get(reviewer_id)
        self.assertIsNotNone(current_reviewer_activity)
        self.assertEqual(current_reviewer_activity['totalReviews'], 6)
        self.assertGreaterEqual(len(current_reviewer_activity['productCategoryCounts']), self.detector.disparate_category_threshold)
        self.assertGreaterEqual(current_reviewer_activity['averageRating'], self.detector.high_rating_min_avg)

        # Detect patterns
        mock_dt.now.return_value = base_time + datetime.timedelta(minutes=len(review_events)*5 + 10) # Advance time slightly
        detected_flags = self.detector.detect_patterns(current_reviewer_activity, current_time=mock_dt.now.return_value)
        
        self.assertGreater(len(detected_flags), 0)
        self.assertIn("Brand new account (created 3 days ago) with high review volume (6 reviews).", detected_flags)
        self.assertIn("High number of reviews (6) with high average rating (4.5) across 5 disparate product categories.", detected_flags)

        # Flag reviewer and reviews
        associated_review_ids_from_activity = current_reviewer_activity['associatedReviewIds']
        
        # Create product_id_lookup for flagging service from review_events
        product_id_lookup = {event['reviewId']: event['productId'] for event in review_events}

        self.flagging_service.flag_reviewer_and_reviews(
            reviewer_id, 
            detected_flags, 
            associated_review_ids_from_activity, 
            product_id_lookup=product_id_lookup,
            current_time_iso=mock_dt.now.return_value.isoformat().replace('+00:00', 'Z')
        )

        # Verify flagging service state
        flagged_reviewer = self.mock_flagged_reviewers_db.get(reviewer_id)
        self.assertIsNotNone(flagged_reviewer)
        self.assertEqual(set(flagged_reviewer['flaggedReason']), set(detected_flags))
        self.assertEqual(set(flagged_reviewer['associatedReviewIds']), set(associated_review_ids_from_activity))

        for review_id in associated_review_ids_from_activity:
            flagged_review = self.mock_flagged_reviews_db.get(review_id)
            self.assertIsNotNone(flagged_review)
            self.assertEqual(flagged_review['reviewerId'], reviewer_id)
            self.assertEqual(flagged_review['productId'], product_id_lookup[review_id])
            self.assertEqual(flagged_review['flagReason'], "; ".join(detected_flags))
            self.assertEqual(flagged_review['status'], "NEW")

if __name__ == '__main__':
    unittest.main()