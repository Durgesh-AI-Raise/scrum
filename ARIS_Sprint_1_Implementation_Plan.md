
# ARIS Sprint 1: Implementation Plan

## Overall Architecture

The ARIS system will consist of several key components:

*   **Data Ingestion Layer:** For pulling data from various internal and external sources (e.g., fraudulent account lists, raw review data, reviewer purchase history).
*   **Detection Services:** Microservices or modules responsible for specific fraud detection logic (Account-Based, Content Analysis, Behavior Anomaly).
*   **Core API/Orchestration Service:** A central backend service that receives new reviews, orchestrates calls to detection services, stores results, and exposes APIs for the frontend.
*   **Database:** A relational database (e.g., PostgreSQL) to store reviews, flags, detection configurations, reviewer profiles, and analyst actions.
*   **Frontend Dashboard:** A web-based interface for Trust & Safety analysts to review flagged items and take actions.
*   **Reporting Module:** For aggregating and visualizing abuse trends.

## Data Models (High-Level)

The core data models will be foundational to ARIS.

1.  **Review (Table: `reviews`)**
    *   `review_id` (PK, UUID/String)
    *   `reviewer_id` (FK to `reviewers`, String)
    *   `product_id` (String)
    *   `review_text` (TEXT)
    *   `review_date` (TIMESTAMP)
    *   `rating` (INTEGER)
    *   `is_flagged` (BOOLEAN, default FALSE)
    *   `overall_abuse_score` (FLOAT, 0-1)
    *   `flag_reasons` (TEXT[], Array of strings, e.g., ["Account Fraud", "Profanity"])
    *   `status` (VARCHAR, e.g., "Pending", "Removed", "Legitimate")
    *   `action_taken_by` (FK to `analysts`, NULLABLE)
    *   `action_date` (TIMESTAMP, NULLABLE)
    *   `created_at` (TIMESTAMP)
    *   `updated_at` (TIMESTAMP)

2.  **Reviewer (Table: `reviewers`)**
    *   `reviewer_id` (PK, String)
    *   `reviewer_name` (VARCHAR)
    *   `email` (VARCHAR, INDEXED)
    *   `is_known_fraud` (BOOLEAN, default FALSE, updated by Account-Based Fraud Detection)
    *   `aggregated_behavior_metrics` (JSONB, for dynamic storage of metrics like `review_count_30d`, `unique_products_30d`)
    *   `created_at` (TIMESTAMP)
    *   `updated_at` (TIMESTAMP)

3.  **FraudulentAccount (Table: `fraudulent_accounts`)**
    *   `account_identifier` (PK, String, could be `reviewer_id` or `email`)
    *   `source` (VARCHAR, e.g., "Internal Blocklist", "Historical Data")
    *   `added_date` (TIMESTAMP)
    *   `created_at` (TIMESTAMP)

4.  **ContentKeywordFlag (Table: `content_keyword_flags`)**
    *   `keyword_id` (PK, UUID)
    *   `keyword` (VARCHAR, INDEXED)
    *   `category` (VARCHAR, e.g., "Profanity", "Incentive", "Competitor")
    *   `score_impact` (FLOAT, 0-1, how much this keyword contributes to overall score)
    *   `is_active` (BOOLEAN, default TRUE)

5.  **Analyst (Table: `analysts`)**
    *   `analyst_id` (PK, UUID)
    *   `username` (VARCHAR, UNIQUE)
    *   `password_hash` (VARCHAR)
    *   `role` (VARCHAR, e.g., "Admin", "Analyst")
    *   `created_at` (TIMESTAMP)

---

## Sprint Backlog: Detailed Implementation Plan

#### User Story 1: Account-Based Fraud Detection

*   **Task 1.1: Research data sources for fraudulent accounts**
    *   **Implementation Plan:** Identify accessible internal blocklists (e.g., a shared service or database table of banned users) and historical data of accounts involved in past fraud. Prioritize structured data with `reviewer_id` or `email` as identifiers.
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** Internal Amazon blocklists/fraud data exist and are accessible through an API or direct DB connection.
        *   **Decision:** For MVP, focus on `reviewer_id` as the primary key for `fraudulent_accounts` to directly link to `reviews.reviewer_id`. If `reviewer_id` is not available, `email` can be used as a fallback identifier.

*   **Task 1.2: Develop data ingestion pipeline for fraudulent account lists**
    *   **Implementation Plan:** Implement a Python script or service (e.g., a Lambda function or scheduled cron job) that connects to the identified data sources. It will fetch fraudulent account identifiers and insert them into the `fraudulent_accounts` table, handling de-duplication.
    *   **Code Snippets (Pseudocode):**
        ```python
        def ingest_fraudulent_accounts_pipeline():
            # Connect to internal blocklist source (e.g., API, DB)
            newly_identified_accounts = fetch_from_internal_blocklist()

            # Connect to historical fraud data source
            historical_fraud_accounts = fetch_from_historical_data()

            all_fraud_identifiers = set()
            for account in newly_identified_accounts + historical_fraud_accounts:
                all_fraud_identifiers.add(account['id_or_email']) # Normalize to a single identifier

            existing_fraud_identifiers = get_existing_fraudulent_accounts_from_db()

            for identifier in all_fraud_identifiers:
                if identifier not in existing_fraud_identifiers:
                    insert_into_fraudulent_accounts_db(
                        account_identifier=identifier,
                        source="Internal", # or "Historical"
                        added_date=datetime.now()
                    )
            log_ingestion_summary(len(all_fraud_identifiers), len(newly_added_accounts))
        ```

*   **Task 1.3: Implement logic to cross-reference reviews with fraudulent accounts**
    *   **Implementation Plan:** This logic will be part of the `ReviewProcessor` service. When a new review is ingested, a database lookup against the `fraudulent_accounts` table will determine if the `reviewer_id` (or associated `email`) is present.
    *   **Code Snippets (Pseudocode):**
        ```python
        def is_reviewer_fraudulent(reviewer_id):
            # Query the database
            # SELECT EXISTS(SELECT 1 FROM fraudulent_accounts WHERE account_identifier = :reviewer_id);
            # This would typically be a ORM call or direct SQL execution
            return database.query_exists("fraudulent_accounts", "account_identifier", reviewer_id)
        ```

*   **Task 1.4: Create mechanism to flag reviews from fraudulent accounts**
    *   **Implementation Plan:** If `is_reviewer_fraudulent` returns true, the review will be immediately flagged. Its `is_flagged` status will be set to `TRUE`, `overall_abuse_score` will receive a high initial value (e.g., 0.95), and "Account Fraud" will be added to `flag_reasons`.
    *   **Code Snippets (Pseudocode):**
        ```python
        def flag_review_if_from_fraudulent_account(review):
            if is_reviewer_fraudulent(review.reviewer_id):
                review.is_flagged = True
                review.overall_abuse_score = max(review.overall_abuse_score, 0.95) # High confidence score
                review.flag_reasons.append("Account Fraud")
                # Persist review changes to database
                update_review_in_db(review)
                return True
            return False
        ```

#### User Story 2: Review Content Analysis for Red Flags

*   **Task 2.1: Identify keywords/phrases for review content red flags**
    *   **Implementation Plan:** Collaborate with the Trust & Safety team to compile an initial seed list of keywords and phrases. Categories will include:
        *   **Profanity:** Common curse words.
        *   **Incentivized Language:** "free product", "discounted for review", "sponsored".
        *   **Competitor Mentions:** Specific competitor brand names.
        *   **Excessive Sentiment:** Patterns like "BEST. PRODUCT. EVER." or "absolutely disgusting".
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** T&S will provide an initial, manageable list for MVP.
        *   **Decision:** Store these in the `content_keyword_flags` table with an associated `score_impact` value (e.g., profanity might be 0.4, incentivized language 0.6).

*   **Task 2.2: Implement text processing and keyword matching engine**
    *   **Implementation Plan:** For each review, the `review_text` will be normalized (lowercase, remove punctuation, possibly basic stemming). Then, a simple string matching algorithm will check for the presence of keywords/phrases from the `content_keyword_flags` table.
    *   **Code Snippets (Pseudocode):**
        ```python
        import re

        def normalize_review_text(text):
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
            # Basic stemming/lemmatization could be added here for future, e.g., using NLTK
            return text

        def analyze_content_for_red_flags(review_text):
            normalized_text = normalize_review_text(review_text)
            flagged_content_details = []
            
            # Fetch active keywords from content_keyword_flags table
            keywords_config = fetch_active_content_keywords_from_db() 

            for keyword_data in keywords_config:
                if keyword_data['keyword'] in normalized_text:
                    flagged_content_details.append({
                        'keyword': keyword_data['keyword'],
                        'category': keyword_data['category'],
                        'score_impact': keyword_data['score_impact']
                    })
            return flagged_content_details
        ```

*   **Task 2.3: Develop scoring mechanism for content red flags**
    *   **Implementation Plan:** Based on the `score_impact` of identified keywords, a content-specific abuse score will be calculated. This can be a sum or weighted average of the impacts, normalized to a 0-1 range.
    *   **Code Snippets (Pseudocode):**
        ```python
        def calculate_content_abuse_score(flagged_content_details):
            total_impact = 0.0
            reasons = []
            for detail in flagged_content_details:
                total_impact += detail['score_impact']
                reasons.append(f"Content: {detail['category']} - '{detail['keyword']}'")
            
            # Simple normalization: cap at 1.0 or divide by a configured max possible
            content_score = min(total_impact, 1.0) 
            return content_score, reasons
        ```

*   **Task 2.4: Integrate content analysis flags into overall abuse detection**
    *   **Implementation Plan:** The calculated `content_score` and `content_reasons` will be merged with the `Review`'s existing `overall_abuse_score` and `flag_reasons`. For MVP, we can take the maximum score from all detection modules, or a simple average if multiple flags are present.
    *   **Code Snippets (Pseudocode):**
        ```python
        def integrate_content_analysis_results(review):
            flagged_content_details = analyze_content_for_red_flags(review.review_text)
            content_score, content_reasons = calculate_content_abuse_score(flagged_content_details)

            if content_score > 0:
                review.is_flagged = True
                review.overall_abuse_score = max(review.overall_abuse_score, content_score)
                review.flag_reasons.extend(content_reasons)
                # Persist review changes to database
                update_review_in_db(review)
            return review
        ```

#### User Story 3: Reviewer Behavior Anomaly Detection

*   **Task 3.1: Define reviewer behavior metrics for anomaly detection**
    *   **Implementation Plan:** Define key metrics:
        *   `review_frequency_30d`: Number of reviews in the last 30 days.
        *   `product_diversity_30d`: Number of unique products reviewed in the last 30 days.
        *   `avg_rating_deviation_30d`: Average deviation from product's average rating in the last 30 days.
        *   `review_velocity_avg_hours`: Average time between consecutive reviews.
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** Historical review data is available and queryable to calculate these metrics.
        *   **Decision:** Start with rolling 30-day windows for all metrics to capture recent behavior.

*   **Task 3.2: Develop data collection and aggregation for reviewer behavior**
    *   **Implementation Plan:** Create a scheduled batch job (e.g., daily) that iterates through all active reviewers, queries the `reviews` table for their historical data, calculates the defined metrics, and updates the `reviewers.aggregated_behavior_metrics` JSONB field.
    *   **Code Snippets (Pseudocode):**
        ```python
        import datetime

        def aggregate_reviewer_behavior_metrics():
            today = datetime.date.today()
            thirty_days_ago = today - datetime.timedelta(days=30)
            
            all_reviewer_ids = fetch_all_active_reviewer_ids_from_db()

            for reviewer_id in all_reviewer_ids:
                reviews = fetch_reviewer_reviews_in_date_range(reviewer_id, thirty_days_ago, today)
                
                metrics = {
                    'review_frequency_30d': len(reviews),
                    'product_diversity_30d': len(set([r['product_id'] for r in reviews])),
                    # Calculate other metrics like avg_rating_deviation, review_velocity
                }
                
                update_reviewer_metrics_in_db(reviewer_id, metrics)
            log_aggregation_summary()
        ```

*   **Task 3.3: Implement models for reviewer behavior anomaly detection**
    *   **Implementation Plan:** Apply rules-based detection:
        *   Flag if `review_frequency_30d` exceeds a set threshold (e.g., > 50 reviews).
        *   Flag if `product_diversity_30d` is too low for high frequency (e.g., > 20 reviews but < 5 unique products).
        *   Flag if `avg_rating_deviation_30d` is consistently very high or very low (e.g., always 1-star or always 5-star, compared to product average).
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** Simple threshold-based rules will capture obvious anomalies for MVP.
        *   **Decision:** Configure thresholds as parameters that can be easily updated without code changes.
    *   **Code Snippets (Pseudocode):**
        ```python
        def detect_behavior_anomalies_for_reviewer(reviewer_metrics):
            anomalies = []
            behavior_score_impact = 0.0

            if reviewer_metrics.get('review_frequency_30d', 0) > THRESHOLD_HIGH_FREQUENCY:
                anomalies.append("Behavior: High review frequency")
                behavior_score_impact += 0.4

            if reviewer_metrics.get('product_diversity_30d', 0) < THRESHOLD_LOW_DIVERSITY and \
               reviewer_metrics.get('review_frequency_30d', 0) > THRESHOLD_MEDIUM_FREQUENCY:
                anomalies.append("Behavior: Low product diversity with high frequency")
                behavior_score_impact += 0.5

            # More rules for rating deviation, velocity, etc.
            
            return anomalies, behavior_score_impact
        ```

*   **Task 3.4: Create mechanism to flag reviews based on anomalous behavior**
    *   **Implementation Plan:** When a new review is submitted, its `reviewer_id`'s latest aggregated behavior metrics will be retrieved. If anomalies are detected, the review will be flagged, and the `overall_abuse_score` and `flag_reasons` will be updated.
    *   **Code Snippets (Pseudocode):**
        ```python
        def flag_review_based_on_reviewer_behavior(review):
            reviewer_metrics = fetch_reviewer_metrics_from_db(review.reviewer_id)
            if reviewer_metrics:
                anomalies, behavior_score_impact = detect_behavior_anomalies_for_reviewer(reviewer_metrics)
                if anomalies:
                    review.is_flagged = True
                    review.overall_abuse_score = max(review.overall_abuse_score, behavior_score_impact)
                    review.flag_reasons.extend(anomalies)
                    # Persist review changes to database
                    update_review_in_db(review)
            return review
        ```

#### User Story 4: Manual Review & Action Interface

*   **Task 4.1: Design basic UI/UX for ARIS dashboard**
    *   **Implementation Plan:** Create wireframes and mockups for the ARIS dashboard. Key views:
        *   **Login Page:** Simple username/password.
        *   **Flagged Reviews List:** A table showing `review_id`, `product_id`, `reviewer_id`, `overall_abuse_score`, and top 1-2 `flag_reasons`. Filter/sort options.
        *   **Review Detail View:** Full `review_text`, all `flag_reasons`, historical actions (if any), and action buttons (Remove, Mark Legitimate, Suspend Reviewer).
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** A clean, intuitive interface is crucial for analyst efficiency.
        *   **Decision:** Use a modern frontend framework (e.g., React/Vue) for component-based development.

*   **Task 4.2: Develop front-end components for flagged reviews display**
    *   **Implementation Plan:** Implement the React/Vue components based on the UI/UX design. This will involve fetching data from backend APIs and rendering it into tables and detail cards. State management for review data and actions.
    *   **Code Snippets (React-like Pseudocode):**
        ```jsx
        // FlaggedReviewsList.jsx
        import React, { useState, useEffect } from 'react';

        function FlaggedReviewsList() {
            const [reviews, setReviews] = useState([]);
            const [loading, setLoading] = useState(true);

            useEffect(() => {
                const fetchFlaggedReviews = async () => {
                    try {
                        const response = await fetch('/api/flagged-reviews?status=Pending');
                        const data = await response.json();
                        setReviews(data);
                    } catch (error) {
                        console.error('Error fetching flagged reviews:', error);
                    } finally {
                        setLoading(false);
                    }
                };
                fetchFlaggedReviews();
            }, []);

            if (loading) return <div>Loading flagged reviews...</div>;

            return (
                <div>
                    <h2>Flagged Reviews ({reviews.length})</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Review ID</th>
                                <th>Product</th>
                                <th>Reviewer</th>
                                <th>Score</th>
                                <th>Primary Reason</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reviews.map(review => (
                                <tr key={review.review_id}>
                                    <td>{review.review_id}</td>
                                    <td>{review.product_id}</td>
                                    <td>{review.reviewer_id}</td>
                                    <td>{review.overall_abuse_score.toFixed(2)}</td>
                                    <td>{review.flag_reasons[0]}</td>
                                    <td>
                                        <button onClick={() => window.location.href = `/review/${review.review_id}`}>View Details</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
        }

        // ReviewDetail.jsx (simplified)
        import React, { useState, useEffect } from 'react';

        function ReviewDetail({ reviewId }) {
            const [review, setReview] = useState(null);

            useEffect(() => {
                const fetchReview = async () => {
                    const response = await fetch(`/api/reviews/${reviewId}`);
                    const data = await response.json();
                    setReview(data);
                };
                fetchReview();
            }, [reviewId]);

            if (!review) return <div>Loading review details...</div>;

            return (
                <div>
                    <h3>Review Details for {review.review_id}</h3>
                    <p><strong>Text:</strong> {review.review_text}</p>
                    <p><strong>Abuse Score:</strong> {review.overall_abuse_score.toFixed(2)}</p>
                    <p><strong>Reasons:</strong> {review.flag_reasons.join(', ')}</p>
                    {/* Action buttons will be added here */}
                </div>
            );
        }
        ```

*   **Task 4.3: Implement back-end API for fetching flagged reviews**
    *   **Implementation Plan:** Create a REST API endpoint (e.g., `/api/flagged-reviews`) in the core orchestration service. This endpoint will query the `reviews` table, filtering for `is_flagged = TRUE` and `status = 'Pending'`. It should support pagination and basic sorting.
    *   **Code Snippets (Python Flask-like Pseudocode):**
        ```python
        from flask import Flask, jsonify, request
        # from your_db_module import get_paginated_flagged_reviews, get_review_by_id

        app = Flask(__name__)

        @app.route('/api/flagged-reviews', methods=['GET'])
        def get_flagged_reviews_api():
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status_filter = request.args.get('status', 'Pending', type=str)

            # reviews_data = get_paginated_flagged_reviews(page, per_page, status_filter)
            # Mock data for demonstration
            mock_reviews = [
                {'review_id': 'r_123', 'product_id': 'p_abc', 'reviewer_id': 'rv_xyz', 'overall_abuse_score': 0.85, 'flag_reasons': ['Account Fraud', 'Profanity'], 'review_text': 'This is terrible! Absolutely the worst product ever.'},
                {'review_id': 'r_456', 'product_id': 'p_def', 'reviewer_id': 'rv_uvw', 'overall_abuse_score': 0.72, 'flag_reasons': ['Behavior: High review frequency', 'Content: Incentivized'], 'review_text': 'Got this for free and I love it!'},
            ]
            return jsonify(mock_reviews)

        @app.route('/api/reviews/<string:review_id>', methods=['GET'])
        def get_review_detail_api(review_id):
            # review_data = get_review_by_id(review_id)
            # Mock data
            mock_review = {'review_id': review_id, 'product_id': 'p_abc', 'reviewer_id': 'rv_xyz', 'overall_abuse_score': 0.85, 'flag_reasons': ['Account Fraud', 'Profanity'], 'review_text': 'This is terrible! Absolutely the worst product ever.', 'status': 'Pending'}
            return jsonify(mock_review)
        ```

*   **Task 4.4: Implement functionalities for manual review actions**
    *   **Implementation Plan:** Add API endpoints (e.g., `/api/reviews/<review_id>/action`) that accept `action` (e.g., "remove", "mark_legitimate", "suspend_reviewer") and `analyst_id`. These actions will update the `reviews.status` and `action_taken_by` fields. "Suspend Reviewer" will also update `reviewers.is_known_fraud` and potentially trigger a removal of all their pending reviews.
    *   **Code Snippets (Python Flask-like Pseudocode):**
        ```python
        # from your_db_module import update_review_status, get_reviewer_id_from_review, update_reviewer_fraud_status

        @app.route('/api/reviews/<string:review_id>/action', methods=['POST'])
        def take_review_action_api(review_id):
            data = request.get_json()
            action = data.get('action')
            analyst_id = data.get('analyst_id') # Will come from authenticated user

            if not analyst_id:
                return jsonify({"message": "Analyst ID required"}), 401

            if action == 'remove':
                # update_review_status(review_id, 'Removed', analyst_id)
                print(f"Review {review_id} marked as Removed by {analyst_id}")
            elif action == 'mark_legitimate':
                # update_review_status(review_id, 'Legitimate', analyst_id)
                print(f"Review {review_id} marked as Legitimate by {analyst_id}")
            elif action == 'suspend_reviewer':
                # reviewer_id = get_reviewer_id_from_review(review_id)
                mock_reviewer_id = 'rv_xyz' # Mock
                # update_reviewer_fraud_status(mock_reviewer_id, True, analyst_id)
                # update_review_status(review_id, 'Removed', analyst_id) # Auto-remove review if reviewer suspended
                print(f"Reviewer {mock_reviewer_id} suspended and review {review_id} removed by {analyst_id}")
            else:
                return jsonify({"message": "Invalid action"}), 400

            return jsonify({"status": "success", "review_id": review_id, "action": action}), 200
        ```

*   **Task 4.5: Implement user authentication and authorization for analysts**
    *   **Implementation Plan:** Implement a robust authentication system for `analysts` using JWT (JSON Web Tokens). Users will log in via the `/api/login` endpoint, receive a token, and send this token with subsequent requests. Middleware will validate tokens and check user roles for authorization.
    *   **Code Snippets (Python Flask-like Pseudocode with JWT concepts):**
        ```python
        # from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
        # from werkzeug.security import generate_password_hash, check_password_hash
        # from your_db_module import get_analyst_by_username

        # Setup JWT (e.g., app.config["JWT_SECRET_KEY"] = "your_secret_key")

        @app.route('/api/login', methods=['POST'])
        def login_api():
            username = request.json.get('username')
            password = request.json.get('password')

            # analyst = get_analyst_by_username(username)
            # if analyst and check_password_hash(analyst.password_hash, password):
            # Mock authentication
            if username == 'analyst1' and password == 'securepassword':
                # access_token = create_access_token(identity={'id': analyst.analyst_id, 'role': analyst.role})
                mock_access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMyIsInJvbGUiOiJhbmFseXN0In0.signature"
                return jsonify(access_token=mock_access_token), 200
            
            return jsonify({"message": "Bad username or password"}), 401

        # Example of a protected route using @jwt_required() decorator
        # @app.route('/api/analyst-profile', methods=['GET'])
        # @jwt_required()
        # def get_analyst_profile():
        #     current_analyst_identity = get_jwt_identity() # {'id': '123', 'role': 'analyst'}
        #     return jsonify(logged_in_as=current_analyst_identity), 200
        ```

#### User Story 5: Basic Reporting of Abuse Trends

*   **Task 5.1: Define key metrics for basic abuse trend reporting**
    *   **Implementation Plan:** Define the following metrics to be reported:
        *   **Total Flagged Reviews:** Daily/Weekly count.
        *   **Flag Type Distribution:** Percentage of reviews flagged by each primary reason (Account Fraud, Profanity, Behavior Anomaly).
        *   **Actions Taken Distribution:** Counts of "Removed", "Legitimate", "Suspended Reviewer" actions over time.
        *   **Average Abuse Score:** Trend of the average `overall_abuse_score` for flagged reviews.
    *   **Assumptions & Technical Decisions:**
        *   **Assumption:** The `reviews` table contains all necessary data for these reports.
        *   **Decision:** Focus on simple, aggregate numbers and distributions for MVP.

*   **Task 5.2: Develop data aggregation for reporting metrics**
    *   **Implementation Plan:** Implement API endpoints that query the `reviews` table and perform SQL aggregations (e.g., `COUNT`, `GROUP BY`, `AVG`) to generate the defined metrics for a given date range.
    *   **Code Snippets (Python Flask-like Pseudocode):**
        ```python
        # from your_db_module import get_reviews_for_reporting

        @app.route('/api/reports/abuse-trends', methods=['GET'])
        def get_abuse_trends_report_api():
            start_date_str = request.args.get('start_date') # e.g., '2023-10-01'
            end_date_str = request.args.get('end_date')   # e.g., '2023-10-31'

            # Fetch reviews within the date range, possibly pre-filtered for flagged ones
            # relevant_reviews = get_reviews_for_reporting(start_date_str, end_date_str)
            
            # Mock data for aggregation demonstration
            mock_reviews_data = [
                {'review_date': '2023-10-25', 'flag_reasons': ['Account Fraud'], 'status': 'Removed', 'overall_abuse_score': 0.9},
                {'review_date': '2023-10-25', 'flag_reasons': ['Profanity', 'Content: Excessive Sentiment'], 'status': 'Pending', 'overall_abuse_score': 0.7},
                {'review_date': '2023-10-26', 'flag_reasons': ['Behavior: High review frequency'], 'status': 'Pending', 'overall_abuse_score': 0.6},
                {'review_date': '2023-10-26', 'flag_reasons': ['Account Fraud'], 'status': 'Removed', 'overall_abuse_score': 0.95},
                {'review_date': '2023-10-26', 'flag_reasons': ['Content: Incentivized'], 'status': 'Legitimate', 'overall_abuse_score': 0.5},
            ]

            total_flagged = len(mock_reviews_data)
            flag_type_counts = {}
            action_counts = {}
            total_scores = 0.0

            for review in mock_reviews_data:
                for reason in review['flag_reasons']:
                    flag_type_counts[reason.split(':')[0].strip()] = flag_type_counts.get(reason.split(':')[0].strip(), 0) + 1 # Group by main type
                action_counts[review['status']] = action_counts.get(review['status'], 0) + 1
                total_scores += review['overall_abuse_score']

            avg_abuse_score = total_scores / total_flagged if total_flagged > 0 else 0

            report = {
                'total_flagged_reviews': total_flagged,
                'flag_type_distribution': flag_type_counts,
                'action_taken_distribution': action_counts,
                'average_flag_score': avg_abuse_score
            }
            return jsonify(report)
        ```

*   **Task 5.3: Implement simple reporting interface in ARIS dashboard**
    *   **Implementation Plan:** Create a "Reports" section in the ARIS frontend. This section will display the aggregated metrics using simple charts (e.g., bar charts for counts, pie charts for distributions). Implement date range selectors for filtering reports.
    *   **Code Snippets (React-like Pseudocode):**
        ```jsx
        // ReportingDashboard.jsx
        import React, { useState, useEffect } from 'react';
        // import { Bar, Pie } from 'react-chartjs-2'; // Example charting library

        function ReportingDashboard() {
            const [reportData, setReportData] = useState(null);
            const [startDate, setStartDate] = useState('2023-10-01');
            const [endDate, setEndDate] = useState('2023-10-31');

            useEffect(() => {
                const fetchReportData = async () => {
                    try {
                        const response = await fetch(`/api/reports/abuse-trends?start_date=${startDate}&end_date=${endDate}`);
                        const data = await response.json();
                        setReportData(data);
                    } catch (error) {
                        console.error('Error fetching report data:', error);
                    }
                };
                fetchReportData();
            }, [startDate, endDate]);

            if (!reportData) return <div>Loading reports...</div>;

            // Prepare data for charts (example structure)
            const flagTypeChartData = {
                labels: Object.keys(reportData.flag_type_distribution),
                datasets: [{
                    data: Object.values(reportData.flag_type_distribution),
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
                }],
            };

            const actionChartData = {
                labels: Object.keys(reportData.action_taken_distribution),
                datasets: [{
                    data: Object.values(reportData.action_taken_distribution),
                    backgroundColor: ['#9966FF', '#FF9933', '#66CCCC'],
                }],
            };

            return (
                <div>
                    <h2>Abuse Trends Report</h2>
                    <div>
                        Start Date: <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
                        End Date: <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
                    </div>
                    <p>Total Flagged Reviews: {reportData.total_flagged_reviews}</p>
                    <p>Average Flag Score: {reportData.average_flag_score.toFixed(2)}</p>

                    <h3>Flag Type Distribution</h3>
                    {/* <Pie data={flagTypeChartData} /> */}
                    <ul>
                        {Object.entries(reportData.flag_type_distribution).map(([type, count]) => (
                            <li key={type}>{type}: {count}</li>
                        ))}
                    </ul>

                    <h3>Actions Taken</h3>
                    {/* <Bar data={actionChartData} /> */}
                    <ul>
                        {Object.entries(reportData.action_taken_distribution).map(([action, count]) => (
                            <li key={action}>{action}: {count}</li>
                        ))}
                    </ul>
                </div>
            );
        }
        ```
