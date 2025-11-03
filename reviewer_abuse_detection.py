import datetime
import json
import uuid
import statistics

# --- Task 2.1: Data Model for Reviewer Activity Patterns ---
# This model captures aggregated information about a reviewer's activity.
# In a real system, this would be a record in a NoSQL database (e.g., MongoDB, DynamoDB).
#
# reviewer_activity = {
#     "reviewerId": "u54321",
#     "totalReviews": 15,
#     "sumRatings": 65, # Sum to compute averageRating
#     "averageRating": 4.33,
#     "reviewTimestamps": ["2023-10-20T10:00:00Z", "2023-10-21T11:00:00Z", ...], # Or aggregated counts
#     "productCategoryCounts": {"Electronics": 8, "Books": 5, "Apparel": 2},
#     "accountCreationDate": "2023-10-15T09:00:00Z", # Crucial for 'brand new account'
#     "lastActivityTimestamp": "2023-10-27T12:30:00Z"
# }

# --- Task 2.2: Implement Data Ingestion for Reviewer Account Activity ---
class ReviewerActivityIngestionService:
    def __init__(self, activity_db_client=None, product_catalog_service=None):
        # activity_db_client: Placeholder for a database client (e.g., for MongoDB, DynamoDB)
        # product_catalog_service: Placeholder for a service to get product categories
        self.activity_db_client = activity_db_client
        self.product_catalog_service = product_catalog_service

    def _get_reviewer_activity(self, reviewer_id):
        # In a real system, this would fetch from the database.
        # For pseudocode, simulate fetching or return an empty dict for new reviewers.
        # self.activity_db_client.get(reviewer_id)
        return {}

    def _upsert_reviewer_activity(self, reviewer_activity):
        # In a real system, this would save/update to the database.
        # self.activity_db_client.upsert(reviewer_activity)
        pass

    def _get_product_category(self, product_id):
        # Placeholder for looking up product category based on product_id
        # self.product_catalog_service.get_category(product_id)
        # For demonstration, return a dummy category
        return "Electronics" if hash(product_id) % 2 == 0 else "Books" # Simulate disparate categories

    def ingest_review_event(self, review_event, account_creation_date_iso):
        """
        Ingests a review event and updates the reviewer's activity profile.

        Args:
            review_event (dict): The incoming review event.
            account_creation_date_iso (str): ISO 8601 string of the reviewer's account creation date.
        """
        reviewer_id = review_event.get('reviewerId')
        product_id = review_event.get('productId')
        rating = review_event.get('rating')
        timestamp_iso = review_event.get('timestamp')
        review_id = review_event.get('reviewId')

        if not all([reviewer_id, product_id, rating, timestamp_iso, review_id, account_creation_date_iso]):
            print(f"ERROR: Missing required fields in review event or account creation date: {review_event}")
            return False
        
        # In a real system: fetch reviewer_activity from DB
        # For pseudocode, we'll build it up or mock a persistent state
        # For simplicity, we'll use a local dictionary to simulate state for this example
        # In a real streaming app, state would be managed by the stream processor or a state store.
        
        # Simulating fetching existing activity - in a real DB, this is an upsert pattern
        reviewer_activity = self._get_reviewer_activity(reviewer_id)
        
        if not reviewer_activity:
            reviewer_activity = {
                "reviewerId": reviewer_id,
                "totalReviews": 0,
                "sumRatings": 0,
                "averageRating": 0.0,
                "productCategoryCounts": {},
                "accountCreationDate": account_creation_date_iso,
                "lastActivityTimestamp": "", # Will be updated
                "associatedReviewIds": [] # To track reviews for potential flagging
            }
        
        # Update metrics
        reviewer_activity["totalReviews"] += 1
        reviewer_activity["sumRatings"] += rating
        reviewer_activity["averageRating"] = reviewer_activity["sumRatings"] / reviewer_activity["totalReviews"]
        reviewer_activity["lastActivityTimestamp"] = max(reviewer_activity["lastActivityTimestamp"], timestamp_iso) if reviewer_activity["lastActivityTimestamp"] else timestamp_iso
        reviewer_activity["associatedReviewIds"].append(review_id)

        # Update product category counts
        category = self._get_product_category(product_id)
        if category:
            reviewer_activity["productCategoryCounts"][category] = reviewer_activity["productCategoryCounts"].get(category, 0) + 1

        # In a real system: self._upsert_reviewer_activity(reviewer_activity)
        print(f"INFO: Updated activity for reviewer {reviewer_id}. Total reviews: {reviewer_activity['totalReviews']}")
        return reviewer_activity # Return updated activity for subsequent detection


# --- Task 2.3: Develop Algorithms for Identifying Unusual Patterns ---
class UnusualActivityDetector:
    def __init__(self, new_account_threshold_days=14, high_volume_threshold=20, 
                 disparate_category_threshold=5, high_rating_min_avg=4.5, min_reviews_for_disparate=10):
        """
        Initializes the UnusualActivityDetector with configurable thresholds.

        Args:
            new_account_threshold_days (int): Max age in days for an account to be considered 'new'.
            high_volume_threshold (int): Minimum total reviews for an account to be considered 'high volume'.
            disparate_category_threshold (int): Minimum distinct categories to be considered 'disparate'.
            high_rating_min_avg (float): Minimum average rating for 'many 5-star reviews' pattern.
            min_reviews_for_disparate (int): Minimum total reviews to consider for disparate categories check.
        """
        self.new_account_threshold_days = new_account_threshold_days
        self.high_volume_threshold = high_volume_threshold
        self.disparate_category_threshold = disparate_category_threshold
        self.high_rating_min_avg = high_rating_min_avg
        self.min_reviews_for_disparate = min_reviews_for_disparate

    def detect_patterns(self, reviewer_activity):
        """
        Detects unusual activity patterns based on the provided reviewer activity data.

        Args:
            reviewer_activity (dict): The reviewer's aggregated activity data.

        Returns:
            list: A list of flagged reasons (strings) if unusual patterns are found, otherwise an empty list.
        """
        flags = []
        reviewer_id = reviewer_activity['reviewerId']
        total_reviews = reviewer_activity.get('totalReviews', 0)
        average_rating = reviewer_activity.get('averageRating', 0.0)
        product_category_counts = reviewer_activity.get('productCategoryCounts', {})
        account_creation_date_iso = reviewer_activity.get('accountCreationDate')

        if not account_creation_date_iso:
            print(f"WARNING: Account creation date missing for reviewer {reviewer_id}. Skipping age-based checks.")
            return flags

        current_time = datetime.datetime.now(datetime.timezone.utc)
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


# --- Task 2.4: Implement Flagging Mechanism for Unusual Accounts ---
class FlaggingService:
    def __init__(self, flagged_db_client=None):
        # flagged_db_client: Placeholder for a database client to store flagged reviews/reviewers
        self.flagged_db_client = flagged_db_client
        # In a real system, these would interact with a persistent store
        self._flagged_reviewers_cache = {}
        self._flagged_reviews_cache = {}

    def _get_flagged_reviewer(self, reviewer_id):
        # Simulate DB fetch
        return self._flagged_reviewers_cache.get(reviewer_id)

    def _upsert_flagged_reviewer(self, flagged_reviewer_data):
        # Simulate DB upsert
        self._flagged_reviewers_cache[flagged_reviewer_data['reviewerId']] = flagged_reviewer_data

    def _upsert_flagged_review(self, review_id, flagged_review_data):
        # Simulate DB upsert
        self._flagged_reviews_cache[review_id] = flagged_review_data

    def flag_reviewer_and_reviews(self, reviewer_id, detected_flags, associated_review_ids, product_id_lookup={}):
        """
        Flags a reviewer and their associated reviews based on detected unusual patterns.

        Args:
            reviewer_id (str): The ID of the reviewer to flag.
            detected_flags (list): List of strings describing the unusual patterns detected.
            associated_review_ids (list): List of review IDs posted by the flagged reviewer.
            product_id_lookup (dict): A dictionary to lookup product_id for a given review_id (optional, for FlaggedReview).
        """
        if not detected_flags:
            return
        
        current_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

        # Update/Create FlaggedReviewer record
        flagged_reviewer = self._get_flagged_reviewer(reviewer_id)
        if not flagged_reviewer:
            flagged_reviewer = {
                "reviewerId": reviewer_id,
                "flaggedReason": [],
                "firstFlagTimestamp": current_time_iso,
                "lastFlagTimestamp": current_time_iso,
                "status": "ACTIVE", # Initial status for moderation
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
        print(f"INFO: Flagged reviewer {reviewer_id}. Reasons: {', '.join(detected_flags)}")

        # Create/Update FlaggedReview records for each associated review
        for review_id in associated_review_ids:
            # A simple approach: create a new flag entry. In a complex system, you might append to existing.
            flag_entry = {
                "reviewId": review_id,
                "productId": product_id_lookup.get(review_id, "UNKNOWN"), # Best to have product ID available with review event
                "reviewerId": reviewer_id,
                "flagType": "UNUSUAL_ACCOUNT_ACTIVITY",
                "flagReason": "; ".join(detected_flags), # Combine all flags for the review
                "flagTimestamp": current_time_iso,
                "status": "NEW"
            }
            self._upsert_flagged_review(review_id, flag_entry)
            print(f"INFO: Flagged review {review_id} by {reviewer_id} for unusual account activity.")


# Example of how these services would interact in a pipeline:
if __name__ == '__main__':
    print("--- Demonstrating Reviewer Abuse Detection ---")

    # Initialize services
    ingestion_service = ReviewerActivityIngestionService()
    detector = UnusualActivityDetector(
        new_account_threshold_days=7,
        high_volume_threshold=5, # Lowered for quick demo
        disparate_category_threshold=2, # Lowered for quick demo
        high_rating_min_avg=4.0, # Lowered for quick demo
        min_reviews_for_disparate=3 # Lowered for quick demo
    )
    flagging_service = FlaggingService()

    # Simulate a new reviewer with high volume and disparate 5-star reviews
    reviewer_1_id = "u_new_abuser_1"
    reviewer_1_creation_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)).isoformat().replace('+00:00', 'Z')
    
    # Mock reviewer activity state (in a real system, this would be from DB)
    mock_reviewer_activity_db = {
        reviewer_1_id: {
            "reviewerId": reviewer_1_id,
            "totalReviews": 0,
            "sumRatings": 0,
            "averageRating": 0.0,
            "productCategoryCounts": {},
            "accountCreationDate": reviewer_1_creation_date,
            "lastActivityTimestamp": "",
            "associatedReviewIds": []
        }
    }
    ingestion_service._get_reviewer_activity = lambda r_id: mock_reviewer_activity_db.get(r_id, {})
    ingestion_service._upsert_reviewer_activity = lambda data: mock_reviewer_activity_db.update({data['reviewerId']: data})

    print(f"\n--- Simulating a new abusive reviewer ({reviewer_1_id}) ---")
    product_id_to_category = {}
    for i in range(7): # 7 reviews in a short period by a new account
        review_id = f"r{uuid.uuid4().hex[:8]}"
        product_id = f"p{uuid.uuid4().hex[:8]}"
        rating = 5 if i % 2 == 0 else 4 # Mix of 4 and 5 stars
        timestamp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=i)).isoformat().replace('+00:00', 'Z')
        
        # Simulate different categories
        category = "Electronics" if i < 3 else ("Books" if i < 5 else "Tools")
        ingestion_service._get_product_category = lambda prod_id: category # Override for demo
        product_id_to_category[product_id] = category # For product_id_lookup in flagging

        review_event = {
            "reviewId": review_id,
            "productId": product_id,
            "reviewerId": reviewer_1_id,
            "timestamp": timestamp,
            "rating": rating,
            "countryCode": "US"
        }
        
        updated_activity = ingestion_service.ingest_review_event(review_event, reviewer_1_creation_date)
        if updated_activity:
            mock_reviewer_activity_db[reviewer_1_id] = updated_activity # Update mock state

    # After ingesting reviews, run detection
    current_reviewer_activity = mock_reviewer_activity_db.get(reviewer_1_id)
    if current_reviewer_activity:
        detected_flags = detector.detect_patterns(current_reviewer_activity)
        if detected_flags:
            print(f"\nDetected unusual patterns for {reviewer_1_id}: {detected_flags}")
            product_id_lookup_for_flagging = {rid: ingestion_service._get_product_category(rid) for rid in current_reviewer_activity['associatedReviewIds']}
            flagging_service.flag_reviewer_and_reviews(
                reviewer_1_id, 
                detected_flags, 
                current_reviewer_activity['associatedReviewIds'],
                product_id_lookup = product_id_to_category # Pass actual product IDs
            )
        else:
            print(f"No unusual patterns detected for {reviewer_1_id}.")
    
    print(f"\nFlagged Reviewers Cache: {json.dumps(flagging_service._flagged_reviewers_cache, indent=2)}")
    print(f"\nFlagged Reviews Cache: {json.dumps(flagging_service._flagged_reviews_cache, indent=2)}")


    print("\n--- Simulating a normal reviewer ---")
    reviewer_2_id = "u_normal_reviewer_2"
    reviewer_2_creation_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=300)).isoformat().replace('+00:00', 'Z')

    # Mock reviewer activity state for normal reviewer
    mock_reviewer_activity_db[reviewer_2_id] = {
        "reviewerId": reviewer_2_id,
        "totalReviews": 0,
        "sumRatings": 0,
        "averageRating": 0.0,
        "productCategoryCounts": {},
        "accountCreationDate": reviewer_2_creation_date,
        "lastActivityTimestamp": "",
        "associatedReviewIds": []
    }

    for i in range(5): # 5 reviews over time by an old account
        review_id = f"r{uuid.uuid4().hex[:8]}"
        product_id = f"p{uuid.uuid4().hex[:8]}"
        rating = 3 + (i % 3) # Mix of 3, 4, 5 stars
        timestamp = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=i*10)).isoformat().replace('+00:00', 'Z')

        category = "Books" if i < 3 else "Apparel" # Fewer categories
        ingestion_service._get_product_category = lambda prod_id: category # Override for demo
        product_id_to_category[product_id] = category

        review_event = {
            "reviewId": review_id,
            "productId": product_id,
            "reviewerId": reviewer_2_id,
            "timestamp": timestamp,
            "rating": rating,
            "countryCode": "US"
        }
        updated_activity = ingestion_service.ingest_review_event(review_event, reviewer_2_creation_date)
        if updated_activity:
            mock_reviewer_activity_db[reviewer_2_id] = updated_activity # Update mock state

    current_reviewer_activity_2 = mock_reviewer_activity_db.get(reviewer_2_id)
    if current_reviewer_activity_2:
        detected_flags_2 = detector.detect_patterns(current_reviewer_activity_2)
        if detected_flags_2:
            print(f"\nDetected unusual patterns for {reviewer_2_id}: {detected_flags_2}")
        else:
            print(f"\nNo unusual patterns detected for {reviewer_2_id}.")

    print("------------------------------------------")