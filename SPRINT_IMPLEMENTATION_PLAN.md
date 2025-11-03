## Sprint Implementation Plan: Amazon Review Integrity System (ARIS)

---

### 1. Overall System Architecture

The Amazon Review Integrity System (ARIS) will adopt a **microservices architecture** to ensure scalability, maintainability, and clear separation of concerns.

*   **Frontend (UI):** A Single Page Application (SPA) built with a modern JavaScript framework (e.g., React, Angular, Vue.js) will serve as the primary interface for Trust & Safety Analysts and Managers.
*   **Backend Services:**
    *   **Review Service:** Manages review data, including storage, retrieval, and status updates (flagging, triage).
    *   **Abuse Detection Service:** Consumes new review data, applies statistical outlier detection algorithms, and signals the Review Service to flag reviews/accounts.
    *   **Reporting Service:** Aggregates data from the Review Service for dashboard visualizations.
    *   **User Service (Authentication & Authorization):** Integrates with an Identity Provider (IdP) for secure user authentication and manages role-based authorization.
*   **Data Ingestion:** An event-driven pipeline (e.g., Kafka, AWS Kinesis) for real-time processing of new review data.
*   **Database:** A relational database (e.g., PostgreSQL) will serve as the primary data store for all system data.
*   **Identity Provider (IdP):** An external service (e.g., AWS Cognito, Okta) for managing ARIS system users, authentication, and token issuance.

```
+----------------+     +--------------------+
|                |     |                    |
|    Frontend    |---->|  API Gateway/LB    |
|   (SPA/UI)     |     |                    |
+----------------+     +--------+-----------+
                              |
                              | REST APIs
                              V
+-------------------------------------------------------------------------------------------------------------------------------------+
|                                                  Backend Microservices                                                              |
|                                                                                                                                     |
|  +---------------------+   +-----------------------+   +---------------------+   +-------------------------------------+          |
|  |    User Service     |<--|  Authentication/Auth  |-->|    Review Service   |   |   Abuse Detection Service           |          |
|  | (AuthN/AuthZ, Roles)|   |                       |   | (Review CRUD, Flags)|<--| (Statistical Outlier Detection)     |          |
|  +----------^----------+   +----------^------------+   +----------^----------+   +----------^--------------------------+          |
|             |                       |                     |          |                     |                                        |
|             |                       |                     |          |                     |                                        |
|             |                       |                     |          |                     | Events (e.g., New Review)              |
|             |                       |                     |          |                     V                                        |
|             |                       |                     |          |             +--------------------------+                     |
|             |                       |                     |          |             |   Message Queue/Stream   |                     |
|             |                       |                     |          |             |  (e.g., Kafka/Kinesis)   |                     |
|             |                       |                     |          |             +------------^-------------+                     |
|             |                       |                     |          |                          |                                   |
|             |                       |                     |          |                          | Review Data Ingestion             |
|             |                       |                     |          |                          V                                   |
|             |                       |                     |          |             +---------------------------+                    |
|             |                       |                     |          |             | External Review Data Source |                    |
|             |                       |                     |          |             | (e.g., Amazon Review DB)  |                    |
|             |                       |                     |          |             +---------------------------+                    |
|             |                       |                     |          |                                                            |
|             V                       V                     V          V                                                            |
|  +---------------------------------------------------------------------------------------------------------------------------------+ |
|  |                                                        Database (PostgreSQL)                                                  | |
|  | +----------+  +-----------+  +----------+  +----------+  +------------+  +-----------------+  +------------------+          | |
|  | |  Users   |  | Reviewers |  | Products |  |  Reviews |  | FlaggedLog |  | TriageHistory  |  | Auth Audit Log |          | |
|  | +----------+  +-----------+  +----------+  +----------+  +------------+  +-----------------+  +------------------+          | |
|  +---------------------------------------------------------------------------------------------------------------------------------+ |
|                                                                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------------------+
```

---

### 2. Data Models (High-Level)

*   **`Review` Table:**
    *   `review_id` (PK, UUID)
    *   `product_id` (FK to Product, UUID)
    *   `reviewer_id` (FK to Reviewer, UUID)
    *   `rating` (INT, 1-5)
    *   `review_text` (TEXT)
    *   `review_date` (TIMESTAMP)
    *   `ip_address` (TEXT, hashed/anonymized if needed)
    *   `device_id` (TEXT, hashed/anonymized if needed)
    *   `order_id` (TEXT, optional)
    *   `is_flagged` (BOOLEAN, default FALSE) - Indicates if any detection mechanism has flagged it.
    *   `flag_reason` (TEXT, e.g., "Statistical Outlier", "Manual Flag")
    *   `flag_timestamp` (TIMESTAMP)
    *   `triage_status` (TEXT, ENUM: "Pending", "Investigating", "Confirmed Abuse", "False Positive", default "Pending")
    *   `triage_analyst_id` (FK to ARIS User, UUID, nullable)
    *   `triage_timestamp` (TIMESTAMP, nullable)
    *   `triage_comment` (TEXT, nullable)
*   **`Reviewer` Table:**
    *   `reviewer_id` (PK, UUID)
    *   `username` (TEXT)
    *   `email` (TEXT)
    *   `registration_date` (TIMESTAMP)
    *   `total_reviews` (INT, calculated)
    *   `avg_rating` (FLOAT, calculated)
    *   `is_flagged` (BOOLEAN, default FALSE) - For reviewer account-level flags.
    *   `flag_reason` (TEXT)
    *   `flag_timestamp` (TIMESTAMP)
*   **`Product` Table:**
    *   `product_id` (PK, UUID)
    *   `product_name` (TEXT)
    *   `category` (TEXT)
    *   `avg_rating` (FLOAT, calculated)
    *   `total_reviews` (INT, calculated)
*   **`ARIS_User` Table (for ARIS system users):**
    *   `user_id` (PK, UUID, maps to IdP user ID)
    *   `username` (TEXT)
    *   `email` (TEXT)
    *   `role` (TEXT, ENUM: "Analyst", "Manager")

---

### 3. Assumptions and Technical Decisions

*   **Cloud Platform:** AWS for managed services (RDS for PostgreSQL, Kinesis for streaming, Cognito for IdP).
*   **Backend Language/Framework:** Python with FastAPI for microservices (chosen for performance and ease of development).
*   **Frontend Framework:** React for the SPA.
*   **Database:** PostgreSQL, due to its robustness, ACID compliance, and strong community support.
*   **Authentication/Authorization:** OAuth2/OIDC standards, managed by AWS Cognito for ARIS system users. JWTs will be used for API authentication.
*   **Data Ingestion:** AWS Kinesis Streams for handling high-throughput review data.
*   **Statistical Outlier Detection:** Initial implementation will use rule-based logic and simple statistical thresholds (e.g., Z-score, IQR for rating deviations, review frequency). This is designed to be extensible for future machine learning models.
*   **API Design:** RESTful APIs using JSON for data exchange.
*   **Error Handling:** Consistent error response formats (e.g., JSON with `code`, `message`).
*   **Logging & Monitoring:** Standardized logging (e.g., CloudWatch Logs) and monitoring (e.g., CloudWatch Metrics, Prometheus/Grafana).
*   **Security:** Input validation, parameterized queries to prevent SQL injection, secure handling of sensitive data (IP/Device IDs to be hashed/anonymized).

---

### 4. Implementation Plan per Sprint Backlog Item

#### **User Story 1: Core Abuse Detection - Statistical Outliers**

**Goal:** Automatically flag reviews or reviewer accounts exhibiting statistically unusual behavior.

*   **Task 1.1: Design statistical outlier detection algorithm.**
    *   **Plan:** Define initial statistical rules based on common abuse patterns.
        *   **Review-level:**
            *   **Rapid Burst:** Number of reviews by a single reviewer within a short timeframe (e.g., 5 reviews in 1 hour) exceeds N standard deviations from the reviewer's average or global average.
            *   **Extreme Rating Skew:** A new reviewer (e.g., < 30 days old, < 5 total reviews) gives a 5-star rating, especially if their account exhibits minimal other activity.
        *   **Reviewer-level:**
            *   **New Account Activity:** Accounts less than X days old with a disproportionately high number of reviews or only 5-star reviews.
            *   **IP/Device Co-occurrence:** Multiple distinct reviewer accounts sharing the same IP address or device ID (will require data for IP/Device).
    *   **Data Model Impact:** `Review.is_flagged`, `Review.flag_reason`, `Review.flag_timestamp`. `Reviewer.is_flagged`, `Reviewer.flag_reason`, `Reviewer.flag_timestamp`.
    *   **Assumptions:** Historical data available to calculate baselines (average review rates, etc.).
    *   **Pseudocode (Algorithm Logic - within `AbuseDetectionService`):**
        ```python
        def detect_outliers(review_data, reviewer_history, global_stats):
            is_flagged = False
            reasons = []

            # Rule 1: Rapid burst of 5-star reviews (Review-level)
            if review_data['rating'] == 5 and reviewer_history['recent_review_count'] > global_stats['avg_recent_reviews_std_dev'] * 2:
                is_flagged = True
                reasons.append("Rapid 5-star burst")

            # Rule 2: New account, single high-rating review (Review-level)
            if reviewer_history['account_age_days'] < 7 and reviewer_history['total_reviews'] == 1 and review_data['rating'] >= 4:
                is_flagged = True
                reasons.append("New account, single high-rating review")

            # Rule 3: Reviewer account with suspicious average rating
            # (Example: Z-score on average rating compared to all reviewers)
            if reviewer_history['avg_rating_z_score'] > 3: # 3 standard deviations above mean
                 is_flagged = True
                 reasons.append("Reviewer high avg rating outlier")

            return is_flagged, ", ".join(reasons) if reasons else None
        ```

*   **Task 1.2: Implement initial statistical outlier detection logic.**
    *   **Plan:** Develop the `AbuseDetectionService` microservice. This service will contain the logic defined in Task 1.1. It will expose an internal API or be a Kinesis consumer.
    *   **Architecture:** `AbuseDetectionService` (Python/FastAPI).
    *   **Code Snippet (Python class `StatisticalOutlierDetector`):**
        ```python
        import datetime

        class StatisticalOutlierDetector:
            def __init__(self, config):
                # Configuration for thresholds (e.g., {'burst_threshold': 5, 'new_account_days': 7, ...})
                self.config = config

            def _get_reviewer_history(self, reviewer_id):
                # Placeholder: In a real system, this would query the ReviewService/ReviewerService
                # or a materialized view of reviewer history.
                # For now, simulate fetching data.
                return {
                    'account_age_days': 10,  # e.g., (now - registration_date).days
                    'total_reviews': 5,
                    'recent_review_count': 3, # reviews in last 24h
                    'avg_rating_z_score': 1.5 # example z-score
                }

            def _get_global_stats(self):
                # Placeholder: In a real system, this would fetch pre-calculated global statistics
                return {
                    'avg_recent_reviews_std_dev': 1.5
                }

            def analyze_review(self, review_payload):
                reviewer_id = review_payload.get('reviewer_id')
                if not reviewer_id:
                    return {'is_flagged': False, 'flag_reason': None}

                reviewer_history = self._get_reviewer_history(reviewer_id)
                global_stats = self._get_global_stats()

                is_flagged, flag_reason = self.detect_outliers(review_payload, reviewer_history, global_stats)
                return {'is_flagged': is_flagged, 'flag_reason': flag_reason}

            def detect_outliers(self, review_data, reviewer_history, global_stats):
                # Implementation of rules from Task 1.1 pseudocode
                # ... (as above)
                is_flagged = False
                reasons = []

                if review_data['rating'] == 5 and reviewer_history['recent_review_count'] > self.config['burst_threshold']:
                    is_flagged = True
                    reasons.append("Rapid 5-star burst")

                if reviewer_history['account_age_days'] < self.config['new_account_days'] and \
                   reviewer_history['total_reviews'] == 1 and review_data['rating'] >= 4:
                    is_flagged = True
                    reasons.append("New account, single high-rating review")

                return is_flagged, ", ".join(reasons) if reasons else None
        ```

*   **Task 1.3: Integrate detection with review data ingestion.**
    *   **Plan:** The Kinesis consumer (e.g., a Lambda function or a dedicated service) will:
        1.  Receive new review data.
        2.  Store the raw review data in the `Review` table.
        3.  Invoke the `AbuseDetectionService.analyze_review` method (either directly or by publishing to another internal queue).
        4.  Update the `Review` table with `is_flagged` and `flag_reason` based on the detection result.
    *   **Architecture:** Kinesis Stream -> Lambda/Consumer -> `AbuseDetectionService` -> `ReviewService` (DB Update).
    *   **Pseudocode (Kinesis Consumer Lambda/Service):**
        ```python
        # Ingestion Consumer (e.g., AWS Lambda, or a dedicated Python service)
        def handle_new_review_event(review_event):
            review_data = review_event['data'] # Extract review details

            # 1. Store initial review
            # Assuming a ReviewRepository or ORM model exists
            ReviewRepository.create_review(review_data)

            # 2. Invoke Abuse Detection Service
            detector = StatisticalOutlierDetector(config={'burst_threshold': 5, 'new_account_days': 7})
            detection_result = detector.analyze_review(review_data)

            # 3. Update Review with flag status
            if detection_result['is_flagged']:
                ReviewRepository.update_review_flag_status(
                    review_data['review_id'],
                    detection_result['is_flagged'],
                    detection_result['flag_reason']
                )
            # Log successful processing
            print(f"Processed review {review_data['review_id']}. Flagged: {detection_result['is_flagged']}")
        ```

*   **Task 1.4: Develop mechanism to flag reviews/accounts.**
    *   **Plan:** Implement the `ReviewRepository.update_review_flag_status` method (as referenced in Task 1.3) which performs the database update. This mechanism will be called by the `AbuseDetectionService` or its integration component.
    *   **Technical Decisions:** Use an ORM (e.g., SQLAlchemy) for database interactions to abstract SQL.
    *   **Code Snippet (Python `ReviewRepository`):**
        ```python
        import psycopg2 # Example for PostgreSQL connection

        class ReviewRepository:
            def __init__(self, db_conn_string):
                self.conn = psycopg2.connect(db_conn_string)

            def create_review(self, review_data):
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO reviews (review_id, product_id, reviewer_id, rating, review_text, review_date, ip_address, device_id, order_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (review_data['review_id'], review_data['product_id'], review_data['reviewer_id'],
                     review_data['rating'], review_data['review_text'], review_data['review_date'],
                     review_data.get('ip_address'), review_data.get('device_id'), review_data.get('order_id'))
                )
                self.conn.commit()
                cursor.close()

            def update_review_flag_status(self, review_id, is_flagged, flag_reason):
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE reviews
                    SET is_flagged = %s, flag_reason = %s, flag_timestamp = NOW()
                    WHERE review_id = %s
                    """,
                    (is_flagged, flag_reason, review_id)
                )
                self.conn.commit()
                cursor.close()

            def close(self):
                self.conn.close()
        ```

*   **Task 1.5: Unit/Integration testing for statistical detection.**
    *   **Plan:**
        *   **Unit Tests:** For `StatisticalOutlierDetector` with mock `reviewer_history` and `global_stats`. Test various scenarios: normal review, rapid burst, new account with high rating, etc.
        *   **Integration Tests:** Set up a local Kinesis/Kafka mock, simulate a review ingestion event, and verify that the `Review` table is correctly updated with flagging status.

#### **User Story 2: Review Detail View**

**Goal:** Provide detailed information for any flagged review.

*   **Task 2.1: Design Review Detail View UI/UX.**
    *   **Plan:** Create wireframes and mockups for a web page displaying:
        *   **Review Info:** Text, rating, date, product name (linked to product page).
        *   **Reviewer Info:** Reviewer ID, username, registration date, total reviews, avg rating.
        *   **Technical Data:** IP addresses, device IDs, associated order ID.
        *   **Flagging Info:** `is_flagged`, `flag_reason`, `flag_timestamp`.
        *   **Triage Status:** Current `triage_status`, `triage_analyst_id`, `triage_timestamp`, `triage_comment` (if available).
    *   **Assumptions:** Responsive design, intuitive layout.

*   **Task 2.2: Implement backend API for fetching review details.**
    *   **Plan:** Develop a FastAPI endpoint in the `ReviewService` to handle GET requests for `/api/reviews/{review_id}`. This endpoint will query the database, joining `reviews`, `reviewers`, and `products` tables to aggregate all necessary data.
    *   **Architecture:** `ReviewService` (FastAPI).
    *   **Code Snippet (Python FastAPI endpoint):**
        ```python
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        import psycopg2 # Example for PostgreSQL
        import datetime # Import datetime

        app = FastAPI()

        # Database connection (in a real app, use a connection pool and dependency injection)
        def get_db_connection():
            conn = psycopg2.connect("dbname=aris user=admin password=secret host=db")
            return conn

        class ReviewDetailResponse(BaseModel):
            review_id: str
            review_text: str
            rating: int
            review_date: datetime.datetime
            ip_address: str | None
            device_id: str | None
            order_id: str | None
            is_flagged: bool
            flag_reason: str | None
            flag_timestamp: datetime.datetime | None
            triage_status: str
            triage_analyst_id: str | None
            triage_timestamp: datetime.datetime | None
            triage_comment: str | None
            reviewer: dict
            product: dict

        @app.get("/api/reviews/{review_id}", response_model=ReviewDetailResponse)
        async def get_review_details(review_id: str):
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        r.review_id, r.review_text, r.rating, r.review_date, r.ip_address, r.device_id, r.order_id,
                        r.is_flagged, r.flag_reason, r.flag_timestamp,
                        r.triage_status, r.triage_analyst_id, r.triage_timestamp, r.triage_comment,
                        rev.reviewer_id, rev.username AS reviewer_username, rev.registration_date, rev.total_reviews, rev.avg_rating AS reviewer_avg_rating,
                        p.product_id, p.product_name, p.category, p.avg_rating AS product_avg_rating, p.total_reviews AS product_total_reviews
                    FROM reviews r
                    JOIN reviewers rev ON r.reviewer_id = rev.reviewer_id
                    JOIN products p ON r.product_id = p.product_id
                    WHERE r.review_id = %s
                    """,
                    (review_id,)
                )
                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail="Review not found")

                columns = [col.name for col in cursor.description]
                review_data = dict(zip(columns, result))

                # Structure the response
                response_data = {
                    "review_id": review_data['review_id'],
                    "review_text": review_data['review_text'],
                    "rating": review_data['rating'],
                    "review_date": review_data['review_date'],
                    "ip_address": review_data['ip_address'],
                    "device_id": review_data['device_id'],
                    "order_id": review_data['order_id'],
                    "is_flagged": review_data['is_flagged'],
                    "flag_reason": review_data['flag_reason'],
                    "flag_timestamp": review_data['flag_timestamp'],
                    "triage_status": review_data['triage_status'],
                    "triage_analyst_id": review_data['triage_analyst_id'],
                    "triage_timestamp": review_data['triage_timestamp'],
                    "triage_comment": review_data['triage_comment'],
                    "reviewer": {
                        "reviewer_id": review_data['reviewer_id'],
                        "username": review_data['reviewer_username'],
                        "registration_date": review_data['registration_date'],
                        "total_reviews": review_data['total_reviews'],
                        "avg_rating": review_data['reviewer_avg_rating'],
                    },
                    "product": {
                        "product_id": review_data['product_id'],
                        "product_name": review_data['product_name'],
                        "category": review_data['category'],
                        "avg_rating": review_data['product_avg_rating'],
                        "total_reviews": review_data['product_total_reviews'],
                    },
                }
                return ReviewDetailResponse(**response_data)
            finally:
                cursor.close()
                conn.close()
        ```

*   **Task 2.3: Data mapping and aggregation for detail view.**
    *   **Plan:** Ensure the SQL query efficiently joins all required tables. The FastAPI endpoint's response model (`ReviewDetailResponse`) explicitly defines the JSON structure, acting as a contract for the frontend.
    *   **Technical Decisions:** Use database indexing on FKs for optimal join performance.

*   **Task 2.4: Develop frontend for Review Detail View.**
    *   **Plan:** Create a React component that fetches data from `/api/reviews/{review_id}` using `useEffect` and `fetch` or Axios. Render the detailed information using UI components following the design from Task 2.1.
    *   **Assumptions:** Basic routing in the frontend framework.

*   **Task 2.5: Unit/Integration testing for detail view.**
    *   **Plan:**
        *   **Unit Tests:** For the FastAPI endpoint, mock database calls and verify correct data aggregation and response formatting. Test edge cases (review not found).
        *   **Integration Tests:** Use a tool like Cypress or Playwright to simulate a user navigating to a review detail page and verify that the data is correctly displayed.

#### **User Story 3: Manual Review & Triage Workflow**

**Goal:** Allow Trust & Safety Analysts to manage the status of flagged reviews.

*   **Task 3.1: Design Triage Workflow UI/UX.**
    *   **Plan:** On the Review Detail View, add a section with:
        *   Dropdown or radio buttons for `triage_status` options ("Investigating", "Confirmed Abuse", "False Positive").
        *   A text area for optional `triage_comment`.
        *   A "Save" button to apply changes.
    *   **Assumptions:** Clear visual indication of current status.

*   **Task 3.2: Implement backend API for updating review status.**
    *   **Plan:** Create a FastAPI PUT endpoint in the `ReviewService`: `/api/reviews/{review_id}/triage`. This endpoint will accept the `triage_status` and `triage_comment` from the request body. It will update the `Review` table, including `triage_status`, `triage_analyst_id` (from authenticated user context), and `triage_timestamp`.
    *   **Architecture:** `ReviewService` (FastAPI).
    *   **Code Snippet (Python FastAPI endpoint):**
        ```python
        from fastapi import Depends, HTTPException, FastAPI
        from pydantic import BaseModel
        import datetime
        import psycopg2 # Example for PostgreSQL

        app = FastAPI() # Assuming this is part of the ReviewService app

        # Mock current_user for demonstration. In reality, use an Auth Dependency.
        class CurrentUser:
            def __init__(self, user_id: str, role: str):
                self.id = user_id
                self.role = role

        def get_current_user():
            # In a real app, this would parse JWT and return user info
            return CurrentUser(user_id="analyst_123", role="Analyst")

        # Database connection (in a real app, use a connection pool and dependency injection)
        def get_db_connection():
            conn = psycopg2.connect("dbname=aris user=admin password=secret host=db")
            return conn

        class TriageUpdateRequest(BaseModel):
            status: str # "Investigating", "Confirmed Abuse", "False Positive"
            comment: str | None = None

        @app.put("/api/reviews/{review_id}/triage")
        async def update_review_triage_status(
            review_id: str,
            request_body: TriageUpdateRequest,
            current_user: CurrentUser = Depends(get_current_user)
        ):
            if request_body.status not in ["Investigating", "Confirmed Abuse", "False Positive"]:
                raise HTTPException(status_code=400, detail="Invalid triage status provided")

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE reviews
                    SET
                        triage_status = %s,
                        triage_analyst_id = %s,
                        triage_timestamp = NOW(),
                        triage_comment = %s
                    WHERE review_id = %s
                    RETURNING review_id;
                    """,
                    (request_body.status, current_user.id, request_body.comment, review_id)
                )
                updated_id = cursor.fetchone()
                if not updated_id:
                    raise HTTPException(status_code=404, detail="Review not found")
                conn.commit()
            finally:
                cursor.close()
                conn.close()

            return {"message": f"Review {review_id} status updated to {request_body.status}"}
        ```

*   **Task 3.3: Integrate triage status with flagging mechanism.**
    *   **Plan:** The `triage_status` will be the definitive state of a review.
        *   If `triage_status` becomes "Confirmed Abuse," `is_flagged` remains `TRUE`.
        *   If `triage_status` becomes "False Positive," `is_flagged` could be set to `FALSE` (or a specific `flag_reason` indicating false positive) to remove it from the active flagged list.
        *   If `triage_status` is "Investigating" or "Pending", `is_flagged` remains `TRUE`.
    *   **Technical Decisions:** The `UPDATE` query in Task 3.2 can also conditionally update `is_flagged` based on `triage_status`.

*   **Task 3.4: Develop frontend for triage actions (Investigating, Confirmed Abuse, False Positive).**
    *   **Plan:** Implement the UI from Task 3.1. When a user selects a status and clicks save, send a PUT request to the `/api/reviews/{review_id}/triage` endpoint. Update the frontend UI to reflect the new status.

*   **Task 3.5: Unit/Integration testing for triage workflow.**
    *   **Plan:**
        *   **Unit Tests:** For the FastAPI endpoint, test valid/invalid status updates, review not found, and ensure correct database update calls (mock DB).
        *   **Integration Tests:** Simulate a user updating a review status in the UI, then verify the change is reflected in the database and UI.

#### **User Story 4: Basic Reporting Dashboard**

**Goal:** Display overall scale of detected abuse (flagged reviews, types, status).

*   **Task 4.1: Design Basic Reporting Dashboard UI/UX.**
    *   **Plan:** Design a dashboard with:
        *   **Key Metrics:** Total flagged reviews, total reviews under investigation, total confirmed abuse, total false positives (summary cards).
        *   **Charts:**
            *   Pie chart: Distribution of `triage_status`.
            *   Bar chart: Number of flagged reviews by `flag_reason`.
            *   Trend line (optional, for future): Flagged reviews over time.
    *   **Assumptions:** Basic, clear visualizations suitable for managers.

*   **Task 4.2: Implement backend API for fetching dashboard metrics.**
    *   **Plan:** Create a FastAPI GET endpoint in the `ReportingService` (or `ReviewService` if simple enough) at `/api/dashboard/metrics`. This endpoint will execute aggregate SQL queries to retrieve the required counts and groupings.
    *   **Architecture:** `ReportingService` (FastAPI).
    *   **Code Snippet (Python FastAPI endpoint):**
        ```python
        from fastapi import FastAPI, Depends, HTTPException
        from pydantic import BaseModel
        import datetime
        import psycopg2 # Example for PostgreSQL

        app = FastAPI() # Assuming this is part of a ReportingService app

        # Mock CurrentUser and get_current_user from Auth system
        class CurrentUser:
            def __init__(self, user_id: str, role: str):
                self.id = user_id
                self.role = role

        def get_current_user():
            return CurrentUser(user_id="manager_456", role="Manager") # Example

        # Database connection (in a real app, use a connection pool and dependency injection)
        def get_db_connection():
            conn = psycopg2.connect("dbname=aris user=admin password=secret host=db")
            return conn

        class DashboardMetricsResponse(BaseModel):
            total_flagged_reviews: int
            flagged_by_reason: dict[str, int]
            reviews_by_triage_status: dict[str, int]

        @app.get("/api/dashboard/metrics", response_model=DashboardMetricsResponse)
        async def get_dashboard_metrics(current_user: CurrentUser = Depends(get_current_user)):
            # Ensure only managers or authorized roles can access this
            if current_user.role not in ["Manager"]: # Example role check
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                # Total flagged reviews
                cursor.execute("SELECT COUNT(*) FROM reviews WHERE is_flagged = TRUE")
                total_flagged = cursor.fetchone()[0]

                # Flags by reason
                cursor.execute("""
                    SELECT flag_reason, COUNT(*) FROM reviews WHERE is_flagged = TRUE GROUP BY flag_reason
                """)
                flags_by_reason_results = cursor.fetchall()
                flags_by_reason_dict = {row[0]: row[1] for row in flags_by_reason_results}

                # Reviews by triage status
                cursor.execute("""
                    SELECT triage_status, COUNT(*) FROM reviews GROUP BY triage_status
                """)
                reviews_by_triage_results = cursor.fetchall()
                reviews_by_triage_dict = {row[0]: row[1] for row in reviews_by_triage_results}

                return DashboardMetricsResponse(
                    total_flagged_reviews=total_flagged,
                    flagged_by_reason=flags_by_reason_dict,
                    reviews_by_triage_status=reviews_by_triage_dict
                )
            finally:
                cursor.close()
                conn.close()
        ```

*   **Task 4.3: Data aggregation for dashboard metrics.**
    *   **Plan:** Implement the SQL queries within the endpoint. Ensure these queries are optimized (e.g., proper indexing on `is_flagged`, `flag_reason`, `triage_status`).
    *   **Technical Decisions:** For very large datasets, consider pre-calculating metrics in a data warehouse or using materialized views if real-time exactness isn't critical. For now, direct SQL queries are sufficient.

*   **Task 4.4: Develop frontend for basic reporting dashboard.**
    *   **Plan:** Create a React component for the dashboard. Fetch data from `/api/dashboard/metrics` and render it using a charting library (e.g., Chart.js, Recharts).

*   **Task 4.5: Unit/Integration testing for basic reporting.**
    *   **Plan:**
        *   **Unit Tests:** For the FastAPI endpoint, mock DB calls and verify correct aggregation and response. Test unauthorized access.
        *   **Integration Tests:** Simulate a user viewing the dashboard and verify that charts and summary numbers are correctly populated.

#### **User Story 5: System User Authentication & Authorization**

**Goal:** Securely log into the system with appropriate permissions.

*   **Task 5.1: Design Authentication/Authorization flow.**
    *   **Plan:**
        1.  **Login:** User enters credentials on frontend -> Frontend sends to AWS Cognito User Pool.
        2.  **Token Issuance:** Cognito authenticates, issues ID Token (for user info) and Access Token (for API authorization) (JWTs).
        3.  **Token Storage:** Frontend securely stores tokens (e.g., HttpOnly cookies, or local storage with refresh token flow).
        4.  **API Calls:** Frontend includes Access Token in `Authorization: Bearer <token>` header for all backend API requests.
        5.  **Backend Validation:** Each backend microservice validates the JWT (signature, expiry, issuer, audience) using Cognito's public keys.
        6.  **Role-Based Authorization:** Extract `role` claim from JWT (or fetch from `ARIS_User` table based on `sub` claim) to enforce endpoint-specific access.
    *   **Technical Decisions:** Standard OAuth2/OIDC.

*   **Task 5.2: Integrate with identity provider (e.g., AWS Cognito, Okta).**
    *   **Plan:**
        *   **AWS Cognito Setup:** Create a User Pool in AWS Cognito. Configure app clients, user attributes (e.g., `email`, `preferred_username`, custom `role` attribute).
        *   **Backend JWT Validation:** Implement a middleware/dependency in each FastAPI microservice to intercept requests, extract JWT, and validate it against Cognito's JWKS endpoint.
        *   **Frontend Integration:** Use AWS Amplify library or a generic OAuth2 library to handle login, token retrieval, and refresh.
    *   **Code Snippet (Python FastAPI - JWT Validation Dependency):**
        ```python
        import httpx
        from jose import jwt, JWTError
        from fastapi import Header, HTTPException, Depends, FastAPI # Import FastAPI
        import os # For environment variables
        import datetime # Import datetime

        app = FastAPI() # Assuming this is part of a User Service or shared auth module

        # Configuration (should come from environment variables)
        COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
        COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_xxxxxxxxx")
        COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "your_client_id")
        JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

        # Cache for JWKS (can be improved with async cache)
        _jwks_client = None

        async def get_jwks_client():
            global _jwks_client
            if _jwks_client is None:
                async with httpx.AsyncClient() as client:
                    response = await client.get(JWKS_URL)
                    response.raise_for_status()
                    _jwks_client = response.json()
            return _jwks_client

        # CurrentUser class definition from previous tasks
        class CurrentUser:
            def __init__(self, user_id: str, role: str):
                self.id = user_id
                self.role = role

        async def get_current_user(authorization: str = Header(...), jwks: dict = Depends(get_jwks_client)):
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Authorization header missing or malformed")

            token = authorization.split(" ")[1]
            try:
                # Find the correct key from JWKS to verify signature
                header = jwt.get_unverified_header(token)
                key_id = header.get("kid")
                rsa_key = {}
                for key in jwks["keys"]:
                    if key["kid"] == key_id:
                        rsa_key = {
                            "kty": key["kty"],
                            "kid": key["kid"],
                            "use": key["use"],
                            "n": key["n"],
                            "e": key["e"]
                        }
                        break
                if not rsa_key:
                    raise JWTError("Public key not found in JWKS")

                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=COGNITO_CLIENT_ID,
                    issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
                )

                # Fetch user's role from ARIS_User table based on payload['sub']
                # Or assume 'custom:role' claim is present and validated by Cognito
                # For this sprint, let's assume 'role' comes directly from custom claims in the ID token
                # In a real scenario, for access tokens, you'd usually fetch from a local user store
                user_role = payload.get('custom:role', 'Analyst') # Default to Analyst if not specified

                return CurrentUser(user_id=payload['sub'], role=user_role) # 'sub' is user ID
            except JWTError as e:
                raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Authentication error: {e}")

        # Example usage in an endpoint:
        # @app.get("/protected-resource")
        # async def protected_resource(current_user: CurrentUser = Depends(get_current_user)):
        #     return {"message": f"Hello {current_user.id}, your role is {current_user.role}"}
        ```

*   **Task 5.3: Implement basic role-based authorization.**
    *   **Plan:** Create a FastAPI `Depends` function (`requires_roles`) that checks the `current_user.role` against a list of allowed roles for a given endpoint.
    *   **Data Model Impact:** `ARIS_User` table will store the `role` for each system user. This role can also be embedded as a custom claim in the Cognito ID Token.
    *   **Code Snippet (Python FastAPI - Role-based authorization dependency):**
        ```python
        from functools import wraps

        def requires_roles(allowed_roles: list[str]):
            def role_checker(current_user: CurrentUser = Depends(get_current_user)):
                if current_user.role not in allowed_roles:
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
                return current_user # Pass user along if authorized
            return role_checker

        # Example usage:
        # @app.get("/manager-dashboard")
        # async def manager_dashboard(current_user: CurrentUser = Depends(requires_roles(["Manager"]))):
        #     return {"message": "Welcome to the Manager Dashboard!"}

        # @app.put("/api/reviews/{review_id}/triage")
        # async def update_review_triage_status(... , current_user: CurrentUser = Depends(requires_roles(["Analyst", "Manager"]))):
        #     # ... triage logic
        #     pass
        ```

*   **Task 5.4: Implement user login (frontend & backend).**
    *   **Plan:**
        *   **Frontend:** Create a login page that interacts with the Cognito Hosted UI or directly with the Amplify SDK to authenticate users. Upon successful login, the frontend will receive and store the JWTs.
        *   **Backend:** No specific "login" endpoint needed on the backend beyond token validation. The backend relies on the `get_current_user` dependency to protect all relevant APIs.
    *   **Assumptions:** Cognito Hosted UI provides a ready-to-use login page, simplifying frontend efforts.

*   **Task 5.5: Unit/Integration testing for auth/auth.**
    *   **Plan:**
        *   **Unit Tests:** For JWT validation logic (mock valid/invalid tokens, expired tokens). Test `requires_roles` with different user roles.
        *   **Integration Tests:**
            *   Simulate a successful login flow (frontend to Cognito).
            *   Test accessing protected endpoints with a valid token, an expired token, and a token with insufficient roles.
            *   Verify that unauthorized access attempts return 401/403 errors.
