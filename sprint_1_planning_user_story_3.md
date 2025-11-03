# Sprint 1 Planning: User Story 3 - Basic Rules-Based Abuse Detection

**Sprint Goal:** To establish the foundational components of the Amazon Review Abuse Tracking System by implementing basic rules-based abuse detection.

## User Story 3: As a system, I want to implement basic rules-based detection (e.g., duplicate review text, unusually high review volume from a new reviewer), so that initial, clear abuse indicators can be generated.

---

### Task 3.1: Define initial set of basic detection rules

*   **Implementation Plan:**
    1.  **Brainstorm Abuse Patterns:** Identify common, easily detectable patterns of review abuse relevant to Amazon (e.g., exact duplicate text, unusually high frequency from a single reviewer, very short reviews with high ratings, reviews containing blacklisted keywords).
    2.  **Formalize Rules:** For each identified pattern, define a clear, unambiguous rule. This includes:
        *   **Rule ID:** Unique identifier (e.g., `DUP_TEXT`, `HIGH_VOLUME_NEW_REVIEWER`).
        *   **Description:** Human-readable explanation of the rule.
        *   **Conditions:** Specific criteria that trigger the rule (e.g., "review text is identical to another review by the same reviewer within X minutes/hours").
        *   **Severity:** Impact level (e.g., HIGH, MEDIUM, LOW).
        *   **Action (Initial):** What happens when triggered (e.g., "flag review", "log and alert").
    3.  **Prioritize Rules:** Select an initial set of 2-3 basic rules that are impactful and relatively straightforward to implement within this sprint.
    4.  **Document Rules:** Store the defined rules in a structured format (e.g., JSON, YAML, or a simple Python dictionary structure).

*   **Data Models and Architecture:**
    *   **Architecture:** The defined rules will be consumed by the Rule Engine. They can be stored in a configuration file or a dedicated rules database/service in a more advanced setup.
    *   **Data Model (Rule Definition - conceptual):**
        ```python
        class DetectionRule:
            rule_id: str
            description: str
            condition_expression: str # e.g., "review.text == another_review.text"
                                    # or a reference to a function/method
            severity: str # "HIGH", "MEDIUM", "LOW"
            action: str # "FLAG_REVIEW", "ALERT"
            parameters: Dict # e.g., {"time_window_minutes": 60, "min_reviews_per_hour": 5}
        ```
    *   **Initial Simple Rule Structure (Python dictionary):**
        ```python
        BASIC_DETECTION_RULES = [
            {
                "rule_id": "DUPLICATE_REVIEW_TEXT_EXACT",
                "description": "Flags reviews with exact same text by the same reviewer within a time window.",
                "condition_type": "text_match_same_reviewer",
                "parameters": {"time_window_hours": 24, "min_text_length": 50},
                "severity": "HIGH"
            },
            {
                "rule_id": "HIGH_REVIEW_VOLUME_NEW_REVIEWER",
                "description": "Flags new reviewers posting an unusually high number of reviews in a short period.",
                "condition_type": "reviewer_activity_spike",
                "parameters": {"time_window_hours": 1, "max_reviews_threshold": 5, "reviewer_age_days": 7},
                "severity": "MEDIUM"
            }
            # ... more rules
        ]
        ```

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The initial set of rules will be relatively simple and not require a complex, dynamic rule management system.
    *   **Technical Decision:** Rules will initially be hardcoded in a configuration file (e.g., `rules.py` or `rules.json`) rather than fetched from a database or external service for simplicity in this sprint.
    *   **Technical Decision:** The `condition_expression` can initially be a string reference to a specific Python function that implements the logic for that rule.

*   **Code Snippets/Pseudocode:**
    ```python
    # rules_config.py or rules_config.json
    # Example of how rules might be defined in a Python dictionary
    
    RULES_CONFIG = [
        {
            "rule_id": "DUPLICATE_REVIEW_TEXT_EXACT",
            "description": "Flags reviews with exact same text by the same reviewer within a time window.",
            "condition_function": "check_duplicate_review_text_exact", # Refers to a function in the rule engine
            "parameters": {
                "time_window_hours": 24,
                "min_text_length": 50
            },
            "severity": "HIGH"
        },
        {
            "rule_id": "HIGH_REVIEW_VOLUME_NEW_REVIEWER",
            "description": "Flags new reviewers posting an unusually high number of reviews in a short period.",
            "condition_function": "check_high_volume_new_reviewer",
            "parameters": {
                "time_window_hours": 1,
                "max_reviews_threshold": 5,
                "reviewer_age_days": 7 # Reviewer is considered 'new' if account age is less than this
            },
            "severity": "MEDIUM"
        },
        {
            "rule_id": "REVIEW_CONTAINS_BLACKLISTED_KEYWORDS",
            "description": "Flags reviews containing specific forbidden keywords.",
            "condition_function": "check_blacklisted_keywords",
            "parameters": {
                "keywords": ["scam", "fraud", "fake review", "buy *****", "deal now"]
            },
            "severity": "HIGH"
        }
    ]
    ```

---

### Task 3.2: Develop rule engine for flagging reviews

*   **Implementation Plan:**
    1.  **Load Rules:** Create a component that loads the defined rules from the configuration (from Task 3.1).
    2.  **Rule Evaluation Logic:** Develop a core function in the rule engine that takes a `ReviewMetadata` object (from the database after transformation) and a list of rules. It iterates through each rule and applies its condition.
    3.  **Condition Functions:** Implement specific Python functions for each `condition_function` defined in the rules (e.g., `check_duplicate_review_text_exact`, `check_high_volume_new_reviewer`). These functions will need to interact with the database to fetch historical review data or reviewer activity.
    4.  **Flagging Mechanism:** If a rule's condition is met, the engine should mark the review as `is_flagged=True` and store the `rule_id` and `severity` in the `flagging_reason` (JSONB) field of the `ReviewMetadata` object.
    5.  **Output:** The rule engine should return the updated `ReviewMetadata` object, including any flagging information.

*   **Data Models and Architecture:**
    *   **Architecture:** The `Rule Engine` will be a new service or a module within the `Processing Service` that consumes `ReviewMetadata` after it has been stored (or just before, depending on integration). It will query the database for historical data as needed.
    *   **Input Data Model:** `ReviewMetadata` (Python class from Task 2.1).
    *   **Output Data Model:** Updated `ReviewMetadata` object with `is_flagged` and `flagging_reason` populated.
    *   **Database Interactions:** The rule engine will need read access to the `reviews` table (and potentially other tables like `reviewers` if created) to evaluate conditions.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The rule engine will run synchronously as part of the review processing pipeline for this sprint.
    *   **Technical Decision:** The rule engine will be implemented in Python. Condition functions will be plain Python functions for simplicity, dynamically called based on the `condition_function` string in the rule config.
    *   **Technical Decision:** Database queries for historical data (e.g., to check for duplicates or reviewer activity) will be optimized with appropriate indexes (already planned in Task 2.1) to avoid performance bottlenecks.

*   **Code Snippets/Pseudocode:**
    ```python
    import json
    import logging
    from datetime import datetime, timedelta
    from typing import List, Dict, Any, Optional
    from sqlalchemy.orm import Session

    # Assume Review class and Session are imported from data_storage_module (Task 2.2)
    # from your_project.data_storage import Review, Session

    # Mock Review class for pseudocode context
    class MockReview:
        def __init__(self, review_id, product_asin, reviewer_id, review_timestamp, review_text, rating, helpfulness_votes=0, is_flagged=False, flagging_reason=None, moderation_status='PENDING', is_public=True):
            self.review_id = review_id
            self.product_asin = product_asin
            self.reviewer_id = reviewer_id
            self.review_timestamp = review_timestamp
            self.review_text = review_text
            self.rating = rating
            self.helpfulness_votes = helpfulness_votes
            self.is_flagged = is_flagged
            self.flagging_reason = flagging_reason if flagging_reason is not None else []
            self.moderation_status = moderation_status
            self.is_public = is_public

        def to_dict(self):
            return {
                'review_id': self.review_id,
                'product_asin': self.product_asin,
                'reviewer_id': self.reviewer_id,
                'review_timestamp': self.review_timestamp.isoformat(),
                'review_text': self.review_text,
                'rating': self.rating,
                'is_flagged': self.is_flagged,
                'flagging_reason': self.flagging_reason,
                'moderation_status': self.moderation_status
            }
    
    # Mock Session and database query (in a real scenario, this would be SQLAlchemy Session)
    class MockDBSession:
        def __init__(self, reviews_data):
            self._reviews_data = {r.review_id: r for r in reviews_data}

        def query(self, model):
            return MockDBQuery(model, self._reviews_data)

    class MockDBQuery:
        def __init__(self, model, reviews_data):
            self._model = model
            self._reviews_data = reviews_data
            self._filters = []

        def filter_by(self, **kwargs):
            self._filters.append(kwargs)
            return self
        
        def filter(self, *args):
            # Simplified filter for timestamp comparison
            for arg in args:
                self._filters.append(str(arg)) # Store as string for inspection
            return self

        def all(self):
            results = []
            for review_id, review in self._reviews_data.items():
                match = True
                for f in self._filters:
                    if isinstance(f, dict):
                        for k, v in f.items():
                            if getattr(review, k) != v:
                                match = False
                                break
                    elif isinstance(f, str) and "review_timestamp <" in f: # Very basic parsing for demo
                        # Example: "review_timestamp < '2023-11-03T10:00:00Z'"
                        try:
                            # Extract timestamp string and compare
                            ts_str = f.split(" < ")[1].strip("'")
                            compare_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if review.review_timestamp >= compare_ts:
                                match = False
                                break
                        except Exception:
                            pass # Ignore malformed filters for this mock
                if match:
                    results.append(review)
            return results
        
        def first(self):
            results = self.all()
            return results[0] if results else None



    logger = logging.getLogger(__name__)

    # --- Condition Functions (implementations of specific rules) ---

    def check_duplicate_review_text_exact(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        """
        Checks for exact duplicate review text by the same reviewer within a time window.
        """
        time_window_hours = parameters.get("time_window_hours", 24)
        min_text_length = parameters.get("min_text_length", 50)

        if not current_review.review_text or len(current_review.review_text) < min_text_length:
            return False # Ignore very short reviews for this rule

        # Query DB for reviews by the same reviewer within the time window
        start_time = current_review.review_timestamp - timedelta(hours=time_window_hours)

        # In a real ORM, this would be a proper query
        # existing_reviews = db_session.query(Review).filter(
        #    Review.reviewer_id == current_review.reviewer_id,
        #    Review.review_timestamp >= start_time,
        #    Review.review_id != current_review.review_id # Exclude current review if already in DB
        # ).all()
        
        # Mocked DB query
        existing_reviews = db_session.query(MockReview).filter_by(reviewer_id=current_review.reviewer_id).filter(
            f"review_timestamp >= '{start_time.isoformat()}'"
        ).all()

        for review in existing_reviews:
            if review.review_text == current_review.review_text:
                logger.info(f"Found duplicate text for review {current_review.review_id} by {current_review.reviewer_id}")
                return True
        return False

    def check_high_volume_new_reviewer(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        """
        Checks if a 'new' reviewer has posted an unusually high volume of reviews.
        (Simplified: Assumes 'reviewer_age_days' is known, or derived from first review).
        For this sprint, we'll simplify and check review count in a window.
        """
        time_window_hours = parameters.get("time_window_hours", 1)
        max_reviews_threshold = parameters.get("max_reviews_threshold", 5)
        reviewer_age_days = parameters.get("reviewer_age_days", 7) # Conceptual, might need actual reviewer entity

        # For simplicity, assume all reviews ingested are from 'new' reviewers for this check's scope
        # In a real system, 'reviewer_age' would come from a Reviewer profile or first review date.
        
        # Count reviews by this reviewer in the last 'time_window_hours'
        start_time = current_review.review_timestamp - timedelta(hours=time_window_hours)
        
        # Mocked DB query
        recent_reviews = db_session.query(MockReview).filter_by(reviewer_id=current_review.reviewer_id).filter(
            f"review_timestamp >= '{start_time.isoformat()}'"
        ).all()

        if len(recent_reviews) > max_reviews_threshold:
            logger.info(f"High volume ({len(recent_reviews)}) for reviewer {current_review.reviewer_id} in {time_window_hours} hours.")
            return True
        return False
    
    def check_blacklisted_keywords(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        """
        Checks if the review text contains any blacklisted keywords.
        """
        keywords = [k.lower() for k in parameters.get("keywords", [])]
        review_text_lower = current_review.review_text.lower() if current_review.review_text else ""

        for keyword in keywords:
            if keyword in review_text_lower:
                logger.info(f"Review {current_review.review_id} contains blacklisted keyword: {keyword}")
                return True
        return False

    # Mapping of condition_function names to actual functions
    CONDITION_FUNCTIONS = {
        "check_duplicate_review_text_exact": check_duplicate_review_text_exact,
        "check_high_volume_new_reviewer": check_high_volume_new_reviewer,
        "check_blacklisted_keywords": check_blacklisted_keywords
    }

    # Assume RULES_CONFIG is imported from rules_config.py (Task 3.1)
    RULES_CONFIG_MOCK = [
        {
            "rule_id": "DUPLICATE_REVIEW_TEXT_EXACT",
            "description": "Flags reviews with exact same text by the same reviewer within a time window.",
            "condition_function": "check_duplicate_review_text_exact",
            "parameters": {
                "time_window_hours": 24,
                "min_text_length": 50
            },
            "severity": "HIGH"
        },
        {
            "rule_id": "HIGH_REVIEW_VOLUME_NEW_REVIEWER",
            "description": "Flags new reviewers posting an unusually high number of reviews in a short period.",
            "condition_function": "check_high_volume_new_reviewer",
            "parameters": {
                "time_window_hours": 1,
                "max_reviews_threshold": 2,
                "reviewer_age_days": 7
            },
            "severity": "MEDIUM"
        },
         {
            "rule_id": "REVIEW_CONTAINS_BLACKLISTED_KEYWORDS",
            "description": "Flags reviews containing specific forbidden keywords.",
            "condition_function": "check_blacklisted_keywords",
            "parameters": {
                "keywords": ["scam", "fraud", "fake review", "deal now"]
            },
            "severity": "HIGH"
        }
    ]


    def run_rule_engine(review_to_check: MockReview, db_session: MockDBSession) -> MockReview:
        """
        Applies all configured rules to a given review and updates its flagging status.
        """
        flagged_reasons = []
        review_to_check.is_flagged = False # Reset flag for re-evaluation if needed

        for rule_config in RULES_CONFIG_MOCK:
            rule_id = rule_config["rule_id"]
            condition_function_name = rule_config["condition_function"]
            parameters = rule_config.get("parameters", {})
            severity = rule_config["severity"]

            if condition_function_name not in CONDITION_FUNCTIONS:
                logger.error(f"Unknown condition function: {condition_function_name} for rule {rule_id}")
                continue

            condition_func = CONDITION_FUNCTIONS[condition_function_name]

            try:
                if condition_func(current_review=review_to_check, db_session=db_session, parameters=parameters):
                    flagged_reasons.append({
                        "rule_id": rule_id,
                        "severity": severity,
                        "timestamp": datetime.utcnow().isoformat() + 'Z'
                    })
                    review_to_check.is_flagged = True
                    logger.warning(f"Review {review_to_check.review_id} flagged by rule: {rule_id}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id} for review {review_to_check.review_id}: {e}", exc_info=True)
        
        review_to_check.flagging_reason = flagged_reasons
        return review_to_check

    # Example of how it would be used in the processing service:
    # def process_review_for_abuse_detection(review_from_db: Review, db_session: Session):
    #     updated_review = run_rule_engine(review_from_db, db_session)
    #     # Persist updated_review back to the database
    #     # db_session.add(updated_review)
    #     # db_session.commit()

    ```

---

### Task 3.3: Integrate rule engine with ingested data

*   **Implementation Plan:**
    1.  **Identify Integration Point:** The most logical point is after the raw review data has been transformed and successfully stored in the `reviews` database table (from Task 2.2 and 2.3).
    2.  **Modify Processing Service:** Update the `Processing Service` (the Kafka consumer that stores data) to invoke the rule engine.
    3.  **Fetch Review for Evaluation:** After a new review is inserted or updated in the database, fetch it back as a `ReviewMetadata` object to pass to the rule engine. This ensures the rule engine works with the latest persisted state.
    4.  **Apply Rule Engine:** Call the `run_rule_engine` function with the fetched review and a database session.
    5.  **Persist Flagging Status:** After the rule engine returns the updated `ReviewMetadata` object, save its `is_flagged` status and `flagging_reason` back to the database. This will be an `UPDATE` operation on the existing review record.

*   **Data Models and Architecture:**
    *   **Architecture:** The `Processing Service` now acts as an orchestrator: `Kafka Consumer -> Raw Data Transformation -> Database Storage -> Rule Engine Evaluation -> Update Database`.
    *   **Data Flow:** Raw message from Kafka -> `transformed_data` (dict) -> `insert_or_update_review` (creates/updates `Review` in DB) -> `Review` object fetched -> `run_rule_engine` -> `Review` object updated with flags -> `update_review_flagging_status` (persists flags).
    *   No new data models, but existing `Review` model fields (`is_flagged`, `flagging_reason`) will now be actively populated.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The latency introduced by running the rule engine synchronously will be acceptable for the initial "real-time" requirements of this sprint.
    *   **Technical Decision:** The rule engine will operate directly on `Review` ORM objects and use the same database session as the data storage mechanism to ensure transactional consistency.
    *   **Technical Decision:** If a rule requires historical data, the rule's condition function will perform the necessary database queries.

*   **Code Snippets/Pseudocode:**
    ```python
    import json
    from datetime import datetime
    import logging

    # Assume imports from Task 2.2 (data storage) and Task 3.2 (rule engine)
    # from your_project.data_storage import Session, Review, insert_or_update_review
    # from your_project.rule_engine import run_rule_engine
    
    # Re-using mocks for demonstration purposes here
    class SessionManager:
        def __init__(self, reviews_data=None):
            self.reviews_data = reviews_data if reviews_data is not None else []

        def __enter__(self):
            self.session = MockDBSession(self.reviews_data) # Use MockDBSession from Task 3.2
            return self.session

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass # No commit/rollback for mock, but real session would have it
    
    # Mock insert_or_update_review to work with SessionManager and MockReview
    def mock_insert_or_update_review(review_data: dict, session: MockDBSession):
        review_id = review_data['review_id']
        existing_review = session.query(MockReview).filter_by(review_id=review_id).first()

        if existing_review:
            for key, value in review_data.items():
                setattr(existing_review, key, value)
            print(f"MOCK DB: Updated review {review_id}")
            return existing_review # Return the updated mock object
        else:
            new_review = MockReview(
                review_id=review_data['review_id'],
                product_asin=review_data['product_asin'],
                reviewer_id=review_data['reviewer_id'],
                review_timestamp=review_data['review_timestamp'],
                review_text=review_data.get('review_text'),
                rating=review_data['rating'],
                helpfulness_votes=review_data.get('helpfulness_votes', 0)
            )
            session._reviews_data[review_id] = new_review # Add to mock data
            print(f"MOCK DB: Inserted new review {review_id}")
            return new_review

    def update_review_flagging_status(review: MockReview, session: MockDBSession):
        # In a real ORM, this would be a session.add(review) and session.commit()
        # For mock, the review object passed is already updated.
        session._reviews_data[review.review_id] = review # Ensure mock data reflects update
        print(f"MOCK DB: Updated flagging status for review {review.review_id}: is_flagged={review.is_flagged}, reasons={review.flagging_reason}")

    # Assume transform_raw_review_to_db_format is imported
    # from your_project.data_processing import transform_raw_review_to_db_format

    logger = logging.getLogger(__name__)

    def integrated_review_processing_pipeline(raw_review_message: str, db_manager: SessionManager):
        """
        Integrated pipeline: consume raw, transform, store, apply rules, update flags.
        """
        try:
            raw_review_dict = json.loads(raw_review_message)

            # 1. Transform raw data
            transformed_data = test_transform_raw_review_to_db_format(raw_review_dict) # From Task 2.3
            if not transformed_data:
                logger.warning(f"Skipping pipeline for malformed raw review (ID: {raw_review_dict.get('review_id', 'N/A')}).")
                return
            
            with db_manager as session:
                # 2. Store or update review in database
                # This function now also returns the Review ORM object
                persisted_review_obj = mock_insert_or_update_review(transformed_data, session) # Modified to return obj

                # 3. Apply rule engine to the persisted review
                updated_review_obj = run_rule_engine(persisted_review_obj, session) # From Task 3.2

                # 4. Persist updated flagging status back to database
                update_review_flagging_status(updated_review_obj, session)
                logger.info(f"Successfully processed review {updated_review_obj.review_id}. Flagged: {updated_review_obj.is_flagged}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from message: {raw_review_message}. Error: {e}")
        except Exception as e:
            logger.critical(f"Critical error in review processing pipeline for message: {raw_review_message}. Error: {e}", exc_info=True)
            # Consider sending original raw_review_message to DLQ here for full pipeline failures

    # Example of running the integrated pipeline (would be in Kafka consumer loop)
    # if __name__ == '__main__':
    #     # Setup initial mock DB state for testing rule engine
    #     initial_db_reviews = [
    #         MockReview(id="R_DUP_ORIG", asin="B001", reviewer_id="U1", review_timestamp=datetime.fromisoformat("2023-10-31T10:00:00Z"), review_text="This is a very original review text by user 1.", rating=5.0),
    #         MockReview(id="R_VOL_OLD", asin="B002", reviewer_id="U2", review_timestamp=datetime.fromisoformat("2023-10-31T09:00:00Z"), review_text="Old review by user 2.", rating=4.0),
    #         MockReview(id="R_VOL_OLD2", asin="B002", reviewer_id="U2", review_timestamp=datetime.fromisoformat("2023-10-31T09:10:00Z"), review_text="Another old review by user 2.", rating=4.0),
    #     ]
    #     db_manager_instance = SessionManager(initial_db_reviews)

    #     # Test case 1: Normal review
    #     msg1 = json.dumps({
    #         "review_id": "R_NORMAL", "product_asin": "B00X", "reviewer_id": "U_N",
    #         "review_text": "This is a perfectly normal review text from a new user.",
    #         "review_title": "Good", "rating": 4.5,
    #         "review_date": datetime.now().isoformat() + 'Z', "helpfulness_votes": 1,
    #         "ingestion_timestamp": datetime.utcnow().isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg1, db_manager_instance)

    #     # Test case 2: Duplicate review text (should flag based on 'DUPLICATE_REVIEW_TEXT_EXACT' rule)
    #     msg2_dup = json.dumps({
    #         "review_id": "R_DUP_NEW", "product_asin": "B001", "reviewer_id": "U1",
    #         "review_text": "This is a very original review text by user 1.", # Duplicate of R_DUP_ORIG
    #         "review_title": "Duplicate!", "rating": 5.0,
    #         "review_date": datetime.now().isoformat() + 'Z', "helpfulness_votes": 0,
    #         "ingestion_timestamp": datetime.utcnow().isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg2_dup, db_manager_instance)

    #     # Test case 3: High volume new reviewer (mocked for simplicity)
    #     # For this to trigger, we need more than max_reviews_threshold (2 in mock config) in time_window (1 hr)
    #     now = datetime.now()
    #     msg3_vol1 = json.dumps({
    #         "review_id": "R_VOL_3_1", "product_asin": "B00Z", "reviewer_id": "U3_NEW",
    #         "review_text": "First review by U3.", "rating": 5.0,
    #         "review_date": (now - timedelta(minutes=5)).isoformat() + 'Z', "ingestion_timestamp": (now - timedelta(minutes=4)).isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg3_vol1, db_manager_instance)
    #     msg3_vol2 = json.dumps({
    #         "review_id": "R_VOL_3_2", "product_asin": "B00Z", "reviewer_id": "U3_NEW",
    #         "review_text": "Second review by U3.", "rating": 5.0,
    #         "review_date": (now - timedelta(minutes=3)).isoformat() + 'Z', "ingestion_timestamp": (now - timedelta(minutes=2)).isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg3_vol2, db_manager_instance)
    #     msg3_vol3 = json.dumps({
    #         "review_id": "R_VOL_3_3", "product_asin": "B00Z", "reviewer_id": "U3_NEW",
    #         "review_text": "Third review by U3.", "rating": 5.0,
    #         "review_date": (now - timedelta(minutes=1)).isoformat() + 'Z', "ingestion_timestamp": (now - timedelta(minutes=0)).isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg3_vol3, db_manager_instance) # This one should trigger

    #     # Test case 4: Blacklisted keywords
    #     msg4_blacklist = json.dumps({
    #         "review_id": "R_BLACKLIST", "product_asin": "B00Y", "reviewer_id": "U_BL",
    #         "review_text": "This product is a total scam and fraud.", "review_title": "Bad!", "rating": 1.0,
    #         "review_date": datetime.now().isoformat() + 'Z', "helpfulness_votes": 0,
    #         "ingestion_timestamp": datetime.utcnow().isoformat() + 'Z'
    #     })
    #     integrated_review_processing_pipeline(msg4_blacklist, db_manager_instance)

    ```

---

### Task 3.4: Write unit and integration tests for rules

*   **Implementation Plan:**
    1.  **Unit Tests for Condition Functions:** For each condition function (e.g., `check_duplicate_review_text_exact`), write dedicated unit tests. Mock the database interaction to isolate the logic of the condition. Cover positive (rule triggers) and negative (rule does not trigger) scenarios, edge cases (e.g., empty text, boundary conditions for time windows).
    2.  **Unit Test for Rule Engine Orchestration:** Test the `run_rule_engine` function. Mock the individual condition functions to ensure the engine correctly iterates through rules, calls the appropriate functions, and aggregates flagging reasons.
    3.  **Integration Tests (Rule Engine + DB):** Set up a dedicated test database (e.g., in-memory SQLite with SQLAlchemy) or a dedicated test database (e.g., Dockerized PostgreSQL). Populate it with specific test data. Run the `run_rule_engine` against this test data and verify that the `is_flagged` status and `flagging_reason` in the database are updated correctly.
    4.  **End-to-End Tests (Full Pipeline):** Create test scenarios that simulate raw review messages being ingested, transformed, stored, and then processed by the rule engine. Assert the final state of the review in the database after the entire pipeline has run.
    5.  **Performance Considerations (Tests):** While not full performance tests, ensure integration tests with a reasonable amount of data run efficiently to catch immediate performance regressions in rule evaluation.

*   **Data Models and Architecture:**
    *   No new data models/architecture. Testing focuses on validating the correctness and robustness of the `Rule Engine` and its interaction with the `Review` data model and database.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A testing framework like `unittest` or `pytest` is used. `unittest.mock` will be heavily utilized for mocking external dependencies (database, other services).
    *   **Technical Decision:** Integration tests will use a fresh, isolated test database for each run to ensure test independence and prevent side effects.
    *   **Technical Decision:** Test data will be carefully crafted to explicitly trigger and not trigger each rule, verifying both positive and negative cases.

*   **Code Snippets/Pseudocode:**
    ```python
    import unittest
    from unittest.mock import patch, MagicMock
    from datetime import datetime, timedelta, timezone
    import json
    import logging

    # Suppress actual logging during tests to avoid cluttered output
    logging.disable(logging.CRITICAL)

    # Re-import/redefine necessary mocks and functions from previous tasks for self-contained test pseudocode
    class MockReview:
        def __init__(self, review_id, product_asin, reviewer_id, review_timestamp, review_text, rating, helpfulness_votes=0, is_flagged=False, flagging_reason=None, moderation_status='PENDING', is_public=True, ingestion_timestamp=None):
            self.review_id = review_id
            self.product_asin = product_asin
            self.reviewer_id = reviewer_id
            self.review_timestamp = review_timestamp
            self.review_text = review_text
            self.rating = rating
            self.helpfulness_votes = helpfulness_votes
            self.is_flagged = is_flagged
            self.flagging_reason = flagging_reason if flagging_reason is not None else []
            self.moderation_status = moderation_status
            self.is_public = is_public
            self.ingestion_timestamp = ingestion_timestamp if ingestion_timestamp else datetime.now(timezone.utc)

        def __repr__(self):
            return f"<MockReview {self.review_id} flagged={self.is_flagged}>"

        def to_dict(self):
            return {
                'review_id': self.review_id,
                'product_asin': self.product_asin,
                'reviewer_id': self.reviewer_id,
                'review_timestamp': self.review_timestamp.isoformat(),
                'review_text': self.review_text,
                'rating': self.rating,
                'is_flagged': self.is_flagged,
                'flagging_reason': self.flagging_reason,
                'moderation_status': self.moderation_status
            }
    
    # MockDBSession and MockDBQuery from Task 3.2
    class MockDBQuery:
        def __init__(self, model, reviews_data_dict):
            self._model = model
            self._reviews_data_dict = reviews_data_dict # Dictionary of MockReview objects
            self._filters = []

        def filter_by(self, **kwargs):
            self._filters.append(kwargs)
            return self
        
        def filter(self, *args):
            for arg in args:
                self._filters.append(str(arg))
            return self

        def all(self):
            results = []
            for review_id, review in self._reviews_data_dict.items():
                match = True
                for f in self._filters:
                    if isinstance(f, dict):
                        for k, v in f.items():
                            if getattr(review, k) != v:
                                match = False
                                break
                    elif isinstance(f, str) and "review_timestamp >=" in f: # Basic parsing for demo
                        try:
                            ts_str = f.split(" >= ")[1].strip("'")
                            compare_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if review.review_timestamp < compare_ts:
                                match = False
                                break
                        except Exception:
                            pass 
                if match:
                    results.append(review)
            return results
        
        def first(self):
            results = self.all()
            return results[0] if results else None

    class MockDBSession:
        def __init__(self, reviews_list):
            self._reviews_data = {r.review_id: r for r in reviews_list}

        def query(self, model):
            return MockDBQuery(model, self._reviews_data)

    # Condition functions and RULES_CONFIG_MOCK from Task 3.2
    def check_duplicate_review_text_exact(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        time_window_hours = parameters.get("time_window_hours", 24)
        min_text_length = parameters.get("min_text_length", 10) # Lowered for testing short texts
        if not current_review.review_text or len(current_review.review_text) < min_text_length:
            return False
        start_time = current_review.review_timestamp - timedelta(hours=time_window_hours)
        existing_reviews = db_session.query(MockReview).filter_by(reviewer_id=current_review.reviewer_id).filter(
            f"review_timestamp >= '{start_time.isoformat()}'"
        ).all()
        for review in existing_reviews:
            if review.review_text == current_review.review_text and review.review_id != current_review.review_id:
                return True
        return False

    def check_high_volume_new_reviewer(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        time_window_hours = parameters.get("time_window_hours", 1)
        max_reviews_threshold = parameters.get("max_reviews_threshold", 2) # Lowered for testing
        start_time = current_review.review_timestamp - timedelta(hours=time_window_hours)
        recent_reviews = db_session.query(MockReview).filter_by(reviewer_id=current_review.reviewer_id).filter(
            f"review_timestamp >= '{start_time.isoformat()}'"
        ).all()
        
        # Count reviews by this reviewer in the last 'time_window_hours', including the current one if not yet in DB
        count_including_current = len(recent_reviews)
        if current_review.review_id not in db_session._reviews_data: 
             count_including_current += 1

        return count_including_current > max_reviews_threshold
    
    def check_blacklisted_keywords(current_review: MockReview, db_session: MockDBSession, parameters: Dict) -> bool:
        keywords = [k.lower() for k in parameters.get("keywords", [])]
        review_text_lower = current_review.review_text.lower() if current_review.review_text else ""
        for keyword in keywords:
            if keyword in review_text_lower:
                return True
        return False

    CONDITION_FUNCTIONS = {
        "check_duplicate_review_text_exact": check_duplicate_review_text_exact,
        "check_high_volume_new_reviewer": check_high_volume_new_reviewer,
        "check_blacklisted_keywords": check_blacklisted_keywords
    }

    RULES_CONFIG_MOCK = [
        {
            "rule_id": "DUPLICATE_REVIEW_TEXT_EXACT",
            "description": "Flags reviews with exact same text by the same reviewer within a time window.",
            "condition_function": "check_duplicate_review_text_exact",
            "parameters": {
                "time_window_hours": 24,
                "min_text_length": 10
            },
            "severity": "HIGH"
        },
        {
            "rule_id": "HIGH_REVIEW_VOLUME_NEW_REVIEWER",
            "description": "Flags new reviewers posting an unusually high number of reviews in a short period.",
            "condition_function": "check_high_volume_new_reviewer",
            "parameters": {
                "time_window_hours": 1,
                "max_reviews_threshold": 2,
                "reviewer_age_days": 7
            },
            "severity": "MEDIUM"
        },
         {
            "rule_id": "REVIEW_CONTAINS_BLACKLISTED_KEYWORDS",
            "description": "Flags reviews containing specific forbidden keywords.",
            "condition_function": "check_blacklisted_keywords",
            "parameters": {
                "keywords": ["scam", "fraud", "fake review", "deal now"]
            },
            "severity": "HIGH"
        }
    ]

    def run_rule_engine(review_to_check: MockReview, db_session: MockDBSession) -> MockReview:
        flagged_reasons = []
        review_to_check.is_flagged = False 
        for rule_config in RULES_CONFIG_MOCK:
            rule_id = rule_config["rule_id"]
            condition_function_name = rule_config["condition_function"]
            parameters = rule_config.get("parameters", {})
            severity = rule_config["severity"]

            if condition_function_name not in CONDITION_FUNCTIONS:
                logging.error(f"Unknown condition function: {condition_function_name} for rule {rule_id}")
                continue

            condition_func = CONDITION_FUNCTIONS[condition_function_name]
            try:
                if condition_func(current_review=review_to_check, db_session=db_session, parameters=parameters):
                    flagged_reasons.append({
                        "rule_id": rule_id,
                        "severity": severity,
                        "timestamp": datetime.utcnow().isoformat() + 'Z'
                    })
                    review_to_check.is_flagged = True
            except Exception as e:
                logging.error(f"Error evaluating rule {rule_id} for review {review_to_check.review_id}: {e}", exc_info=True)
        
        review_to_check.flagging_reason = flagged_reasons
        return review_to_check

    # Mock transform_raw_review_to_db_format (from Task 2.3)
    def test_transform_raw_review_to_db_format(raw_review_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        transformed_data = {}
        try:
            transformed_data['review_id'] = raw_review_data['review_id']
            transformed_data['product_asin'] = raw_review_data['product_asin']
            transformed_data['reviewer_id'] = raw_review_data['reviewer_id']
            transformed_data['review_timestamp'] = datetime.fromisoformat(raw_review_data['review_date'].replace('Z', '+00:00'))
            transformed_data['ingestion_timestamp'] = datetime.fromisoformat(raw_review_data['ingestion_timestamp'].replace('Z', '+00:00'))
            transformed_data['review_text'] = raw_review_data.get('review_text')
            transformed_data['review_title'] = raw_review_data.get('review_title')
            transformed_data['rating'] = float(raw_review_data['rating'])
            transformed_data['helpfulness_votes'] = int(raw_review_data.get('helpfulness_votes', 0))
            transformed_data['is_flagged'] = False
            transformed_data['flagging_reason'] = None
            transformed_data['moderation_status'] = 'PENDING'
            transformed_data['is_public'] = True
            return transformed_data
        except Exception:
            return None

    # Mock SessionManager, mock_insert_or_update_review, update_review_flagging_status for pipeline testing
    class SessionManager:
        def __init__(self, reviews_list=None):
            self.reviews_data = reviews_list if reviews_list is not None else []
            self.session = MockDBSession(self.reviews_data)

        def __enter__(self):
            return self.session

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    def mock_insert_or_update_review(review_data: dict, session: MockDBSession):
        review_id = review_data['review_id']
        existing_review = session.query(MockReview).filter_by(review_id=review_id).first()

        if existing_review:
            for key, value in review_data.items():
                setattr(existing_review, key, value)
            return existing_review
        else:
            new_review = MockReview(
                review_id=review_data['review_id'],
                product_asin=review_data['product_asin'],
                reviewer_id=review_data['reviewer_id'],
                review_timestamp=review_data['review_timestamp'],
                review_text=review_data.get('review_text'),
                rating=review_data['rating'],
                helpfulness_votes=review_data.get('helpfulness_votes', 0),
                ingestion_timestamp=review_data['ingestion_timestamp'] # Added for completeness in test context
            )
            session._reviews_data[review_id] = new_review
            return new_review

    def update_review_flagging_status(review: MockReview, session: MockDBSession):
        session._reviews_data[review.review_id] = review

    def integrated_review_processing_pipeline(raw_review_message: str, db_manager: SessionManager):
        try:
            raw_review_dict = json.loads(raw_review_message)
            transformed_data = test_transform_raw_review_to_db_format(raw_review_dict)
            if not transformed_data:
                return
            
            with db_manager as session:
                persisted_review_obj = mock_insert_or_update_review(transformed_data, session)
                updated_review_obj = run_rule_engine(persisted_review_obj, session)
                update_review_flagging_status(updated_review_obj, session)

        except Exception:
            pass # Suppress for testing to control outcomes

    class TestRuleEngine(unittest.TestCase):

        def setUp(self):
            self.now = datetime.now(timezone.utc).replace(microsecond=0)
            self.sample_reviews_in_db = [
                MockReview(review_id="R001", product_asin="B001", reviewer_id="U1", review_timestamp=self.now - timedelta(hours=2),
                           review_text="This is a very unique and interesting review for product B001.", rating=5.0),
                MockReview(review_id="R002", product_asin="B001", reviewer_id="U1", review_timestamp=self.now - timedelta(minutes=30),
                           review_text="This is a very unique and interesting review for product B001.", rating=5.0), # Duplicate of R001 text
                MockReview(review_id="R003", product_asin="B002", reviewer_id="U2", review_timestamp=self.now - timedelta(minutes=5),
                           review_text="Short review.", rating=3.0),
                MockReview(review_id="R004", product_asin="B003", reviewer_id="U3", review_timestamp=self.now - timedelta(minutes=10),
                           review_text="Great product!", rating=4.0),
                MockReview(review_id="R005", product_asin="B003", reviewer_id="U3", review_timestamp=self.now - timedelta(minutes=8),
                           review_text="Another great product review.", rating=4.0),
                MockReview(review_id="R006", product_asin="B003", reviewer_id="U3", review_timestamp=self.now - timedelta(minutes=6),
                           review_text="Yet another great product review.", rating=4.0),
            ]
            self.db_session_mock = MockDBSession(self.sample_reviews_in_db)

        # --- Unit Tests for Condition Functions ---

        def test_check_duplicate_review_text_exact_triggers(self):
            # Review R002 has same text as R001 by U1 within 24 hours
            current_review = MockReview(review_id="R007", product_asin="B001", reviewer_id="U1", review_timestamp=self.now - timedelta(minutes=10),
                                        review_text="This is a very unique and interesting review for product B001.", rating=5.0)
            params = RULES_CONFIG_MOCK[0]['parameters']
            self.assertTrue(check_duplicate_review_text_exact(current_review, self.db_session_mock, params))

        def test_check_duplicate_review_text_exact_no_trigger_different_reviewer(self):
            current_review = MockReview(review_id="R008", product_asin="B004", reviewer_id="U_OTHER", review_timestamp=self.now,
                                        review_text="This is a very unique and interesting review for product B001.", rating=5.0)
            params = RULES_CONFIG_MOCK[0]['parameters']
            self.assertFalse(check_duplicate_review_text_exact(current_review, self.db_session_mock, params))

        def test_check_duplicate_review_text_exact_no_trigger_different_text(self):
            current_review = MockReview(review_id="R009", product_asin="B001", reviewer_id="U1", review_timestamp=self.now,
                                        review_text="Completely different review text.", rating=5.0)
            params = RULES_CONFIG_MOCK[0]['parameters']
            self.assertFalse(check_duplicate_review_text_exact(current_review, self.db_session_mock, params))
        
        def test_check_high_volume_new_reviewer_triggers(self):
            # U3 has 3 reviews in ~4 minutes. Threshold is 2 in 1 hour.
            current_review = MockReview(review_id="R010", product_asin="B003", reviewer_id="U3", review_timestamp=self.now,
                                        review_text="Fourth review by U3, should flag!", rating=4.0)
            params = RULES_CONFIG_MOCK[1]['parameters'] # max_reviews_threshold: 2
            self.assertTrue(check_high_volume_new_reviewer(current_review, self.db_session_mock, params))

        def test_check_high_volume_new_reviewer_no_trigger(self):
            # U2 has 2 reviews in 25 minutes. Threshold is 2 in 1 hour. This should not trigger (2 is not > 2)
            current_review = MockReview(review_id="R011", product_asin="B002", reviewer_id="U2", review_timestamp=self.now,
                                        review_text="Third review by U2.", rating=4.0)
            params = RULES_CONFIG_MOCK[1]['parameters'] # max_reviews_threshold: 2
            self.assertFalse(check_high_volume_new_reviewer(current_review, self.db_session_mock, params))

        def test_check_blacklisted_keywords_triggers(self):
            current_review = MockReview(review_id="R012", product_asin="B005", reviewer_id="U4", review_timestamp=self.now,
                                        review_text="This is a complete SCAM product, do not buy!", rating=1.0)
            params = RULES_CONFIG_MOCK[2]['parameters']
            self.assertTrue(check_blacklisted_keywords(current_review, self.db_session_mock, params))
        
        def test_check_blacklisted_keywords_no_trigger(self):
            current_review = MockReview(review_id="R013", product_asin="B005", reviewer_id="U4", review_timestamp=self.now,
                                        review_text="This product is great.", rating=5.0)
            params = RULES_CONFIG_MOCK[2]['parameters']
            self.assertFalse(check_blacklisted_keywords(current_review, self.db_session_mock, params))

        # --- Unit Tests for Rule Engine Orchestration ---
        def test_run_rule_engine_flags_review(self):
            # This review should trigger both DUPLICATE_REVIEW_TEXT_EXACT and REVIEW_CONTAINS_BLACKLISTED_KEYWORDS
            review_to_process = MockReview(review_id="R_PROCESS_1", product_asin="B001", reviewer_id="U1", 
                                           review_timestamp=self.now - timedelta(minutes=15), 
                                           review_text="This is a very unique and interesting review for product B001. This is a scam!", rating=5.0)
            
            updated_review = run_rule_engine(review_to_process, self.db_session_mock)

            self.assertTrue(updated_review.is_flagged)
            self.assertEqual(len(updated_review.flagging_reason), 2)
            rule_ids = {r['rule_id'] for r in updated_review.flagging_reason}
            self.assertIn("DUPLICATE_REVIEW_TEXT_EXACT", rule_ids)
            self.assertIn("REVIEW_CONTAINS_BLACKLISTED_KEYWORDS", rule_ids)

        def test_run_rule_engine_no_flags(self):
            review_to_process = MockReview(review_id="R_PROCESS_2", product_asin="B00Z", reviewer_id="U_CLEAN", 
                                           review_timestamp=self.now, 
                                           review_text="A perfectly clean and positive review.", rating=5.0)
            
            updated_review = run_rule_engine(review_to_process, self.db_session_mock)

            self.assertFalse(updated_review.is_flagged)
            self.assertEqual(len(updated_review.flagging_reason), 0)

        # --- Integration Test (Conceptual) ---
        # This would typically involve setting up a real (or Dockerized) database.
        # For this example, we'll use our enhanced mock session and pipeline.
        def test_integrated_pipeline_flags_correctly(self):
            db_manager = SessionManager(self.sample_reviews_in_db) # Start with existing reviews

            # Simulate a raw message that should trigger multiple rules
            raw_message_to_flag = json.dumps({
                "review_id": "R_E2E_FLAG", "product_asin": "B001", "reviewer_id": "U1",
                "review_text": "This is a very unique and interesting review for product B001. This is a scam!",
                "review_title": "Bad product and fraud", "rating": 1.0,
                "review_date": (self.now + timedelta(minutes=1)).isoformat() + 'Z', # After existing reviews
                "helpfulness_votes": 0,
                "ingestion_timestamp": (self.now + timedelta(minutes=2)).isoformat() + 'Z'
            })

            integrated_review_processing_pipeline(raw_message_to_flag, db_manager)

            # Now, retrieve the review from the mock DB via the manager's session
            with db_manager as session:
                final_review = session.query(MockReview).filter_by(review_id="R_E2E_FLAG").first()
            
            self.assertIsNotNone(final_review)
            self.assertTrue(final_review.is_flagged)
            self.assertEqual(len(final_review.flagging_reason), 2)
            rule_ids = {r['rule_id'] for r in final_review.flagging_reason}
            self.assertIn("DUPLICATE_REVIEW_TEXT_EXACT", rule_ids)
            self.assertIn("REVIEW_CONTAINS_BLACKLISTED_KEYWORDS", rule_ids)
            # We could also check moderation_status defaults to PENDING, etc.

        def test_integrated_pipeline_no_flags_correctly(self):
            db_manager = SessionManager(self.sample_reviews_in_db) # Start with existing reviews

            raw_message_clean = json.dumps({
                "review_id": "R_E2E_CLEAN", "product_asin": "B00X", "reviewer_id": "U_CLEAN_E2E",
                "review_text": "A wonderful product, highly recommended to everyone interested.",
                "review_title": "Excellent", "rating": 5.0,
                "review_date": (self.now + timedelta(minutes=5)).isoformat() + 'Z',
                "helpfulness_votes": 5,
                "ingestion_timestamp": (self.now + timedelta(minutes=6)).isoformat() + 'Z'
            })

            integrated_review_processing_pipeline(raw_message_clean, db_manager)

            with db_manager as session:
                final_review = session.query(MockReview).filter_by(review_id="R_E2E_CLEAN").first()
            
            self.assertIsNotNone(final_review)
            self.assertFalse(final_review.is_flagged)
            self.assertEqual(len(final_review.flagging_reason), 0)
            self.assertEqual(final_review.moderation_status, 'PENDING')


    # To run these tests:
    # if __name__ == '__main__':
    #     unittest.main(argv=['first-arg-is-ignored'], exit=False)

    ```
