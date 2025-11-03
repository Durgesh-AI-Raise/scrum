# Sprint Implementation Plan: Moderator Review System

## 1) Sprint Goal

**Establish the foundational capabilities for moderators to view and identify potentially abusive reviews, supported by initial rule-based detection.**

## 2) Selected Product Backlog Items for the Sprint

*   **US1: As an Amazon Moderator, I want to see a dashboard of potentially abusive reviews, so I can quickly identify and prioritize investigation tasks.**
*   **US2: As an Amazon Moderator, I want to view detailed information about a flagged review (reviewer history, product history, suspicious attributes), so I can make an informed decision about its authenticity.**
*   **US3: As an Amazon Moderator, I want to mark a review as "Abusive" or "Legitimate", so I can initiate the appropriate follow-up actions (e.g., review removal, account suspension workflow).**
*   **US4: As an Amazon Data Analyst, I want the system to apply basic rule-based detection (e.g., multiple reviews from same IP in short time, identical review text across products), so it can flag obvious abuse patterns automatically.**

---

## 3) Architecture, Data Models, Assumptions & Technical Decisions

### Overall Architecture

A microservices-based architecture is proposed for this system, offering scalability and modularity.

*   **Frontend (Moderator Dashboard & Detailed View):** A single-page application (SPA) built with React.
*   **Backend Services:**
    *   **Review Service:** Manages core review data. (Future scope to provide reviews to the Rule Engine)
    *   **Moderation Service:** Handles flagging, detailed review data retrieval, and moderator actions. This service will expose the APIs for the frontend.
    *   **Rule Engine Service:** Applies rule-based detection logic to incoming reviews.
*   **Database:** PostgreSQL will be used as the primary relational database for structured data.
*   **Message Queue (Future Consideration):** For asynchronous communication (e.g., new reviews to Rule Engine Service), Kafka or RabbitMQ could be integrated in future sprints to enhance scalability and decoupling. For this sprint, direct API calls or database interaction will serve as integration points.

### Data Models

Below are the core data models that will be implemented using an ORM (e.g., SQLAlchemy for Python backend).

*   **`Review` Model:**
    *   `review_id` (PK, UUID)
    *   `product_id` (FK to Product, UUID)
    *   `reviewer_id` (FK to Reviewer, UUID)
    *   `review_text` (TEXT)
    *   `rating` (INT)
    *   `submission_date` (TIMESTAMP WITH TIME ZONE)
    *   `ip_address` (VARCHAR)
    *   `status` (ENUM: 'pending', 'approved', 'rejected') - Updated by moderation.

*   **`Product` Model:**
    *   `product_id` (PK, UUID)
    *   `product_name` (VARCHAR)
    *   `product_category` (VARCHAR)

*   **`Reviewer` Model:**
    *   `reviewer_id` (PK, UUID)
    *   `username` (VARCHAR)
    *   `email` (VARCHAR)
    *   `registration_date` (TIMESTAMP WITH TIME ZONE)

*   **`Flag` Model:**
    *   `flag_id` (PK, UUID)
    *   `review_id` (FK to Review, UUID)
    *   `flag_reason` (ENUM: 'suspicious_ip', 'duplicate_text', 'keyword_blacklist', 'other')
    *   `flag_details` (JSONB) - Stores specific, structured details for each flag reason.
    *   `flagged_by` (ENUM: 'system', 'manual')
    *   `flagged_date` (TIMESTAMP WITH TIME ZONE)
    *   `status` (ENUM: 'pending', 'abusive', 'legitimate') - After moderator action.
    *   `moderator_id` (FK to Moderator, UUID, NULLABLE)
    *   `action_date` (TIMESTAMP WITH TIME ZONE, NULLABLE)

*   **`Moderator` Model:**
    *   `moderator_id` (PK, UUID)
    *   `username` (VARCHAR)
    *   `email` (VARCHAR)

### Assumptions & Technical Decisions (General)

*   **Frontend Framework:** React will be used for the SPA.
*   **Backend Framework:** Python with Flask/FastAPI is assumed for backend services.
*   **Database:** PostgreSQL is chosen for its robustness and JSONB support.
*   **API Style:** RESTful API for communication between frontend and backend.
*   **Authentication/Authorization:** Not in scope for this sprint, but assumed to be handled by an external system for moderators.
*   **Error Handling:** Basic error handling will be implemented, with more robust logging and alerting in future iterations.
*   **IDs:** UUIDs will be used for primary keys across all models to ensure uniqueness and simplify distributed system design.

---

## 4) Sprint Backlog - Detailed Implementation Plan

---

#### **Tasks for US1: Moderator Dashboard**

**US1.1: Design Dashboard UI/UX Wireframes**
*   **Implementation Plan:** Create visual wireframes and mockups using design tools (e.g., Figma) to define the layout, content display (Review ID, Product, Flag Reason, Date Flagged, Status), and navigation paths.
*   **Data Models & Architecture:** N/A (Design phase).
*   **Assumptions & Technical Decisions:** Standard web application UI/UX principles. Focus on a clear, information-dense, and actionable dashboard.
*   **Code Snippets/Pseudocode:** N/A

**US1.2: Develop Front-end Dashboard Component**
*   **Implementation Plan:** Develop a React component (`ModeratorDashboard.js`). This component will:
    1.  Fetch a list of flagged reviews from the `/api/flagged-reviews` endpoint (US1.3).
    2.  Display the reviews in a sortable/filterable table.
    3.  Provide a link to the detailed view for each review (US2.4).
*   **Data Models & Architecture:** Integrates with the `Moderation Service` via `GET /api/flagged-reviews`. Displays data from `FlaggedReviewDTO`.
*   **Assumptions & Technical Decisions:** Uses React Hooks for state management and `axios` for API calls. Initial display will be a simple HTML table.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // ModeratorDashboard.js (React Component)
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';
    import { Link } from 'react-router-dom'; // For navigation to detailed view (US2.4)

    function ModeratorDashboard() {
        const [flaggedReviews, setFlaggedReviews] = useState([]);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);
        const [filterReason, setFilterReason] = useState('');
        const [sortBy, setSortBy] = useState('flagged_date_desc');

        useEffect(() => {
            const fetchFlaggedReviews = async () => {
                try {
                    setLoading(true);
                    const params = {};
                    if (filterReason) params.reason = filterReason;
                    if (sortBy) params.sort_by = sortBy;

                    const response = await axios.get('/api/flagged-reviews', { params });
                    setFlaggedReviews(response.data);
                } catch (err) {
                    setError('Failed to fetch flagged reviews.');
                    console.error(err);
                } finally {
                    setLoading(false);
                }
            };
            fetchFlaggedReviews();
        }, [filterReason, sortBy]); // Re-fetch when filters/sort change

        if (loading) return <div>Loading flagged reviews...</div>;
        if (error) return <div>Error: {error}</div>;

        return (
            <div className="moderator-dashboard">
                <h1>Flagged Reviews Dashboard</h1>
                <div className="controls">
                    <label>
                        Filter by Reason:
                        <select onChange={(e) => setFilterReason(e.target.value)} value={filterReason}>
                            <option value="">All</option>
                            <option value="duplicate_text">Duplicate Text</option>
                            <option value="suspicious_ip">Suspicious IP</option>
                            <option value="keyword_blacklist">Keyword Blacklist</option>
                        </select>
                    </label>
                    <label>
                        Sort by:
                        <select onChange={(e) => setSortBy(e.target.value)} value={sortBy}>
                            <option value="flagged_date_desc">Date (Newest First)</option>
                            <option value="flagged_date_asc">Date (Oldest First)</option>
                        </select>
                    </label>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Review ID</th>
                            <th>Product</th>
                            <th>Flag Reason</th>
                            <th>Flagged Date</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {flaggedReviews.map(review => (
                            <tr key={review.review_id}>
                                <td>{review.review_id}</td>
                                <td>{review.product_name}</td>
                                <td>{review.flag_reason}</td>
                                <td>{new Date(review.flagged_date).toLocaleDateString()}</td>
                                <td>{review.status}</td>
                                <td><Link to={`/review/${review.review_id}`}>View Details</Link></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    export default ModeratorDashboard;
    ```

**US1.3: Implement API Endpoint for Flagged Reviews**
*   **Implementation Plan:** Implement `GET /api/flagged-reviews` in the `Moderation Service`. This endpoint will query the `Flag`, `Review`, and `Product` tables to retrieve reviews that have `pending` flags, and return a paginated list of `FlaggedReviewDTO`s.
*   **Data Models & Architecture:** `Moderation Service` interacts with PostgreSQL. Returns `FlaggedReviewDTO`.
*   **Assumptions & Technical Decisions:** Uses an ORM for database queries. Initial implementation will return all pending flags, with US1.4 adding filtering/sorting.
*   **Code Snippets/Pseudocode:**
    ```python
    # Moderation Service (Python/Flask or FastAPI pseudocode)
    from flask import Flask, jsonify, request
    from datetime import datetime
    import uuid

    app = Flask(__name__)

    # Mock database to simulate interactions (similar to previous thought process)
    # ... mock_data for flags, reviews, products for testing ...

    class FlaggedReviewDTO:
        def __init__(self, review_id, product_name, flag_reason, flagged_date, status):
            self.review_id = str(review_id)
            self.product_name = product_name
            self.flag_reason = flag_reason
            self.flagged_date = flagged_date.isoformat()
            self.status = status

        def to_dict(self):
            return {
                "review_id": self.review_id,
                "product_name": self.product_name,
                "flag_reason": self.flag_reason,
                "flagged_date": self.flagged_date,
                "status": self.status
            }

    @app.route('/api/flagged-reviews', methods=['GET'])
    def get_flagged_reviews():
        reason_filter = request.args.get('reason')
        sort_by = request.args.get('sort_by', 'flagged_date_desc')

        # Pseudocode for DB query:
        # query = db_session.query(Flag, Review, Product).join(Review).join(Product).filter(Flag.status == 'pending')
        # if reason_filter:
        #     query = query.filter(Flag.flag_reason == reason_filter)
        # if sort_by == 'flagged_date_asc':
        #     query = query.order_by(Flag.flagged_date.asc())
        # else:
        #     query = query.order_by(Flag.flagged_date.desc())
        # results = query.all() # Fetch combined results

        # For demonstration with mock data (replace with actual DB query):
        mock_db_data = [
            # Example combined data that would come from joins
            {"review_id": "r1", "product_name": "Product A", "flag_reason": "duplicate_text", "flagged_date": datetime(2023, 10, 26, 10, 0, 0), "status": "pending"},
            {"review_id": "r2", "product_name": "Product B", "flag_reason": "suspicious_ip", "flagged_date": datetime(2023, 10, 25, 14, 30, 0), "status": "pending"},
            {"review_id": "r3", "product_name": "Product C", "flag_reason": "keyword_blacklist", "flagged_date": datetime(2023, 10, 27, 9, 0, 0), "status": "pending"},
            {"review_id": "r4", "product_name": "Product A", "flag_reason": "suspicious_ip", "flagged_date": datetime(2023, 10, 26, 11, 0, 0), "status": "pending"},
            {"review_id": "r5", "product_name": "Product D", "flag_reason": "duplicate_text", "flagged_date": datetime(2023, 10, 24, 12, 0, 0), "status": "legitimate"}, # Should not appear
        ]

        filtered_data = [item for item in mock_db_data if item['status'] == 'pending']

        if reason_filter:
            filtered_data = [item for item in filtered_data if item["flag_reason"] == reason_filter]

        if sort_by == 'flagged_date_asc':
            filtered_data.sort(key=lambda x: x['flagged_date'])
        else: # default desc
            filtered_data.sort(key=lambda x: x['flagged_date'], reverse=True)

        flagged_review_dtos = [
            FlaggedReviewDTO(
                review_id=item["review_id"],
                product_name=item["product_name"],
                flag_reason=item["flag_reason"],
                flagged_date=item["flagged_date"],
                status=item["status"]
            ).to_dict() for item in filtered_data
        ]

        return jsonify(flagged_review_dtos), 200
    ```

**US1.4: Implement Dashboard Filtering and Sorting**
*   **Implementation Plan:** This is an enhancement to US1.2 (frontend) and US1.3 (backend). The frontend `ModeratorDashboard.js` will add dropdowns/controls for `flag_reason` and `flagged_date` sorting. The backend `GET /api/flagged-reviews` endpoint will be updated to accept `reason` and `sort_by` query parameters and apply the corresponding filters and sorting to the database query results.
*   **Data Models & Architecture:** No new models; modifications to existing components and API.
*   **Assumptions & Technical Decisions:** Simple filtering (exact match) and basic chronological sorting.
*   **Code Snippets/Pseudocode:** Included in US1.2 and US1.3 code snippets above.

---

#### **Tasks for US4: Basic Rule-Based Detection**

**US4.1: Define Basic Abuse Detection Rules**
*   **Implementation Plan:** Document the initial set of rules, including thresholds and detection logic.
    *   **Rule 1: Multiple Reviews from Same IP in Short Time:** If > `N` reviews from the same `ip_address` within `X` minutes/hours. (`N=3`, `X=60` minutes initially).
    *   **Rule 2: Identical Review Text Across Products:** If `review_text` for a new review exactly matches an existing review for a *different* `product_id`.
    *   **Rule 3: Keyword Blacklist:** If `review_text` contains any defined abusive/spam keywords (e.g., "scam", "fraud", "free promo code").
*   **Data Models & Architecture:** N/A (Documentation/Definition).
*   **Assumptions & Technical Decisions:** Rules are initially hardcoded in the `Rule Engine Service` but designed to be configurable.
*   **Code Snippets/Pseudocode:** N/A

**US4.2: Develop Rule-Based Detection Service**
*   **Implementation Plan:** Develop the `Rule Engine Service`. This service will expose an API endpoint (e.g., `POST /api/detect-abuse`) that the `Review Service` calls upon new review submissions. It will apply the defined rules (US4.1) to the incoming review. If a rule is triggered, it will create one or more `Flag` records in the database, marking them as `flagged_by: 'system'` and `status: 'pending'`.
*   **Data Models & Architecture:** `Rule Engine Service` (Python). Interacts with `Review` (read) and `Flag` (write) tables in PostgreSQL.
*   **Assumptions & Technical Decisions:** The `Review Service` will directly call this service. This service will need read access to the `Review` table for historical checks (e.g., same IP, duplicate text).
*   **Code Snippets/Pseudocode:**
    ```python
    # Rule Engine Service (Python/Flask or FastAPI pseudocode)
    from flask import Flask, request, jsonify
    from datetime import datetime, timedelta
    import uuid

    app = Flask(__name__)

    # Mock database to simulate interactions (for existing reviews and new flags)
    mock_reviews_for_rules = [
        {"review_id": "rev_001", "reviewer_id": "usr_001", "product_id": "prod_A", "review_text": "This is a great product!", "ip_address": "192.168.1.10", "submission_date": datetime(2023, 10, 20, 10, 0, 0)},
        {"review_id": "rev_002", "reviewer_id": "usr_002", "product_id": "prod_B", "review_text": "Good value for money.", "ip_address": "192.168.1.11", "submission_date": datetime(2023, 10, 21, 11, 0, 0)},
        {"review_id": "rev_003", "reviewer_id": "usr_001", "product_id": "prod_C", "review_text": "This is a great product!", "ip_address": "192.168.1.12", "submission_date": datetime(2023, 10, 22, 12, 0, 0)}, # Duplicate text
        {"review_id": "rev_004", "reviewer_id": "usr_003", "product_id": "prod_D", "review_text": "Very happy with the purchase.", "ip_address": "192.168.1.13", "submission_date": datetime(2023, 10, 23, 13, 0, 0)},
        {"review_id": "rev_005", "reviewer_id": "usr_004", "product_id": "prod_E", "review_text": "This product is a scam!", "ip_address": "192.168.1.14", "submission_date": datetime(2023, 10, 24, 14, 0, 0)}, # Keyword
        {"review_id": "rev_006", "reviewer_id": "usr_005", "product_id": "prod_F", "review_text": "Highly recommend this product!", "ip_address": "192.168.1.15", "submission_date": datetime(2023, 10, 25, 15, 0, 0)},
        {"review_id": "rev_007", "reviewer_id": "usr_006", "product_id": "prod_G", "review_text": "Fantastic value.", "ip_address": "10.0.0.1", "submission_date": datetime(2023, 10, 26, 16, 0, 0)},
        {"review_id": "rev_008", "reviewer_id": "usr_007", "product_id": "prod_H", "review_text": "Amazing quality.", "ip_address": "10.0.0.1", "submission_date": datetime(2023, 10, 26, 16, 10, 0)},
    ]
    mock_flags_created_by_rule_engine = [] # This would be inserted into the main flags table

    # Rule Configurations
    IP_REVIEW_THRESHOLD = 2 # reviews
    IP_TIME_WINDOW_MINUTES = 30
    BLACKLIST_KEYWORDS = ["scam", "fraud", "spam", "free promo"]

    @app.route('/api/detect-abuse', methods=['POST'])
    def detect_abuse():
        review_data = request.get_json()
        new_review_id = review_data.get('review_id')
        new_review_text = review_data.get('review_text', '').lower()
        new_ip_address = review_data.get('ip_address')
        new_submission_date_str = review_data.get('submission_date')
        new_product_id = review_data.get('product_id')

        if not all([new_review_id, new_review_text, new_ip_address, new_submission_date_str, new_product_id]):
            return jsonify({"message": "Missing required review data"}), 400

        new_submission_date = datetime.fromisoformat(new_submission_date_str)

        # Add the new review to our 'database' for subsequent rule checks
        mock_reviews_for_rules.append({
            "review_id": new_review_id,
            "reviewer_id": review_data.get('reviewer_id'),
            "product_id": new_product_id,
            "review_text": new_review_text,
            "ip_address": new_ip_address,
            "submission_date": new_submission_date
        })

        triggered_flags = []

        # Rule 1: Multiple Reviews from Same IP in Short Time
        time_window_start = new_submission_date - timedelta(minutes=IP_TIME_WINDOW_MINUTES)
        reviews_from_same_ip = [
            r for r in mock_reviews_for_rules
            if r['ip_address'] == new_ip_address and r['submission_date'] >= time_window_start
            and r['review_id'] != new_review_id # Exclude the current review itself from the count if it's new
        ]
        if len(reviews_from_same_ip) >= IP_REVIEW_THRESHOLD:
            triggered_flags.append({
                "flag_reason": "suspicious_ip",
                "flag_details": {"ip": new_ip_address, "count": len(reviews_from_same_ip) + 1, "time_window_minutes": IP_TIME_WINDOW_MINUTES}
            })

        # Rule 2: Identical Review Text Across Products
        for existing_review in mock_reviews_for_rules:
            if (existing_review['review_id'] != new_review_id and
                existing_review['product_id'] != new_product_id and
                existing_review['review_text'] == new_review_text):
                triggered_flags.append({
                    "flag_reason": "duplicate_text",
                    "flag_details": {"original_review_id": existing_review['review_id'], "duplicate_review_text": new_review_text}
                })
                break # Flag once for this reason

        # Rule 3: Keyword Blacklist
        for keyword in BLACKLIST_KEYWORDS:
            if keyword in new_review_text:
                triggered_flags.append({
                    "flag_reason": "keyword_blacklist",
                    "flag_details": {"detected_keyword": keyword}
                })
                break # Flag once for this reason

        # Persist triggered flags (simulated - in real app, save to PostgreSQL Flags table)
        for flag_info in triggered_flags:
            new_flag_record = {
                "flag_id": str(uuid.uuid4()),
                "review_id": new_review_id,
                "flag_reason": flag_info["flag_reason"],
                "flag_details": flag_info["flag_details"],
                "flagged_by": "system",
                "flagged_date": datetime.now(),
                "status": "pending"
            }
            mock_flags_created_by_rule_engine.append(new_flag_record)
            # In real system: db_session.add(Flag(**new_flag_record)); db_session.commit()

        if triggered_flags:
            return jsonify({"status": "flagged", "flags": [f["flag_reason"] for f in triggered_flags]}), 200
        else:
            return jsonify({"status": "clean"}), 200
    ```

**US4.3: Implement Data Storage for Flags**
*   **Implementation Plan:** Define and implement the `Flag` table schema in PostgreSQL, including the `flag_reason_enum`, `flag_status_enum`, and `flagged_by_enum`. Implement the ORM model for `Flag`. Create database migrations to apply these schema changes.
*   **Data Models & Architecture:** PostgreSQL. `Flag` model definition.
*   **Assumptions & Technical Decisions:** Using database enums for categorical data to ensure data integrity. `JSONB` for `flag_details` offers flexibility for rule-specific metadata.
*   **Code Snippets/Pseudocode:**
    ```sql
    -- SQL Schema for 'flags' table (PostgreSQL example)
    -- Ensure 'reviews', 'products', 'reviewers', 'moderators' tables exist for FKs
    -- (Simplified definitions for context)

    CREATE TYPE flag_reason_enum AS ENUM ('suspicious_ip', 'duplicate_text', 'keyword_blacklist', 'other');
    CREATE TYPE flag_status_enum AS ENUM ('pending', 'abusive', 'legitimate');
    CREATE TYPE flagged_by_enum AS ENUM ('system', 'manual');

    -- Table definitions (ensure they exist or create if needed)
    -- CREATE TABLE reviews (...)
    -- CREATE TABLE products (...)
    -- CREATE TABLE reviewers (...)
    -- CREATE TABLE moderators (...)

    CREATE TABLE IF NOT EXISTS flags (
        flag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        review_id UUID NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
        flag_reason flag_reason_enum NOT NULL,
        flag_details JSONB, -- Stores specific data like IP, list of duplicate review_ids, keywords
        flagged_by flagged_by_enum NOT NULL,
        flagged_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        status flag_status_enum DEFAULT 'pending',
        moderator_id UUID REFERENCES moderators(moderator_id) ON DELETE SET NULL,
        action_date TIMESTAMP WITH TIME ZONE,
        CONSTRAINT unique_review_flag_reason UNIQUE (review_id, flag_reason) -- Prevent duplicate flags for same reason
    );
    ```

**US4.4: Integrate Rule Detection with Dashboard API**
*   **Implementation Plan:** This is an integration task. The `Rule Engine Service` (US4.2) will write new `Flag` records to the database (US4.3). The `Moderation Service`'s `GET /api/flagged-reviews` endpoint (US1.3) already queries this `Flag` table. Therefore, no additional code changes are explicitly required beyond ensuring correct database access and consistent data models between services.
*   **Data Models & Architecture:** Integration via shared PostgreSQL database.
*   **Assumptions & Technical Decisions:** Consistent schema across services. Database connection pooling is handled.
*   **Code Snippets/Pseudocode:** N/A (Integration is implicit through shared data store).

---

#### **Tasks for US2: Detailed Review View**

**US2.1: Design Detailed Review View UI/UX**
*   **Implementation Plan:** Design wireframes for a comprehensive single-review view. This includes sections for:
    *   Full review content (text, rating, product, reviewer, submission details).
    *   All associated flag details and their current status.
    *   Reviewer's past activity (total reviews, average rating, recent reviews).
    *   Product's historical data (total reviews, average rating, other flagged reviews for the product).
*   **Data Models & Architecture:** N/A (Design phase).
*   **Assumptions & Technical Decisions:** Prioritize readability and easy access to all contextual information required for a moderator's decision.
*   **Code Snippets/Pseudocode:** N/A

**US2.2: Develop Front-end Detailed Review Component**
*   **Implementation Plan:** Develop a React component (`DetailedReviewView.js`) that is rendered when a user navigates to `/review/:reviewId`. This component will:
    1.  Extract `reviewId` from the URL.
    2.  Call `GET /api/reviews/{review_id}/details` to fetch all relevant information.
    3.  Render the detailed review, flag information, reviewer history, and product history.
*   **Data Models & Architecture:** Integrates with `Moderation Service`'s `GET /api/reviews/{review_id}/details` endpoint. Displays `DetailedReviewDTO` data.
*   **Assumptions & Technical Decisions:** Uses React Router's `useParams` hook. Frontend will handle data loading and error states gracefully.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // DetailedReviewView.js (React Component)
    import React, { useState, useEffect } from 'react';
    import { useParams } from 'react-router-dom';
    import axios from 'axios';

    function DetailedReviewView() {
        const { reviewId } = useParams();
        const [reviewDetails, setReviewDetails] = useState(null);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);

        useEffect(() => {
            const fetchReviewDetails = async () => {
                try {
                    setLoading(true);
                    const response = await axios.get(`/api/reviews/${reviewId}/details`);
                    setReviewDetails(response.data);
                } catch (err) {
                    setError(`Failed to fetch details for review ${reviewId}.`);
                    console.error(err);
                } finally {
                    setLoading(false);
                }
            };
            fetchReviewDetails();
        }, [reviewId]);

        if (loading) return <div>Loading review details...</div>;
        if (error) return <div>Error: {error}</div>;
        if (!reviewDetails) return <div>No review details found.</div>;

        return (
            <div className="detailed-review-view">
                <h1>Detailed Review: {reviewDetails.review.review_id}</h1>

                <section className="review-content">
                    <h2>Review Content</h2>
                    <p><strong>Product:</strong> {reviewDetails.product.product_name}</p>
                    <p><strong>Rating:</strong> {reviewDetails.review.rating}/5</p>
                    <p><strong>Submitted By:</strong> {reviewDetails.reviewer.username} on {new Date(reviewDetails.review.submission_date).toLocaleDateString()}</p>
                    <p>{reviewDetails.review.review_text}</p>
                    <p><em>IP Address: {reviewDetails.review.ip_address}</em></p>
                </section>

                <section className="flag-details">
                    <h2>Flag Information</h2>
                    {reviewDetails.flags && reviewDetails.flags.length > 0 ? (
                        <ul>
                            {reviewDetails.flags.map((flag) => (
                                <li key={flag.flag_id}>
                                    <strong>Reason:</strong> {flag.flag_reason} <br/>
                                    <strong>Details:</strong> {JSON.stringify(flag.flag_details)} <br/>
                                    <strong>Status:</strong> {flag.status} <br/>
                                    <strong>Flagged By:</strong> {flag.flagged_by} on {new Date(flag.flagged_date).toLocaleDateString()}
                                    {flag.moderator_id && ` (Actioned by ${flag.moderator_id} on ${new Date(flag.action_date).toLocaleDateString()})`}
                                </li>
                            ))}
                        </ul>
                    ) : <p>No active flags for this review.</p>}
                </section>

                <section className="reviewer-history">
                    <h2>Reviewer History ({reviewDetails.reviewer.username})</h2>
                    <p>Total Reviews: {reviewDetails.reviewer_stats.total_reviews}</p>
                    <p>Average Rating: {reviewDetails.reviewer_stats.avg_rating}</p>
                    {/* Placeholder for list of reviewer's other reviews */}
                </section>

                <section className="product-history">
                    <h2>Product History ({reviewDetails.product.product_name})</h2>
                    <p>Total Product Reviews: {reviewDetails.product_stats.total_product_reviews}</p>
                    <p>Product Average Rating: {reviewDetails.product_stats.avg_product_rating}</p>
                    {/* Placeholder for list of product's other reviews */}
                </section>

                {/* Moderator action buttons will be added here (US3.2) */}
            </div>
        );
    }

    export default DetailedReviewView;
    ```

**US2.3: Implement API Endpoint for Detailed Review**
*   **Implementation Plan:** Implement `GET /api/reviews/{review_id}/details` in the `Moderation Service`. This endpoint will perform multiple database queries to aggregate data from the `Review`, `Product`, `Reviewer`, and `Flag` tables for the specified `review_id`. It will also calculate basic statistics for the reviewer and product.
*   **Data Models & Architecture:** `Moderation Service` interacts with PostgreSQL. Returns a `DetailedReviewDTO` (complex JSON object).
*   **Assumptions & Technical Decisions:** All necessary data is available in the database. Multiple joins/queries are acceptable for a single detailed view, but performance will be monitored for potential optimizations (e.g., specific indexes, denormalization, caching).
*   **Code Snippets/Pseudocode:**
    ```python
    # Moderation Service (Python/Flask or FastAPI pseudocode)
    from flask import Flask, jsonify, request
    from datetime import datetime, timedelta
    import uuid

    # Assume app = Flask(__name__)
    # Assume mock_reviews_db_details, mock_products_db_details, mock_reviewers_db_details, mock_flags_db_details are defined
    # (as in previous thought block, containing rich mock data for all entities)

    @app.route('/api/reviews/<uuid:review_id>/details', methods=['GET'])
    def get_detailed_review(review_id):
        review_id_str = str(review_id)
        # In a real system: Query database for review, product, reviewer, and flags
        # review_data = db_session.query(Review).get(review_id_str)
        # product_data = db_session.query(Product).get(review_data.product_id)
        # reviewer_data = db_session.query(Reviewer).get(review_data.reviewer_id)
        # flags_data = db_session.query(Flag).filter_by(review_id=review_id_str).all()

        # Mock data lookup (replace with actual DB queries)
        # Using a more comprehensive mock setup for this endpoint:
        mock_reviews_full_data = {
            "r1": {
                "review_id": "r1", "reviewer_id": "u1", "product_id": "p1",
                "review_text": "This product is amazing! I bought 5 of them.",
                "rating": 5, "submission_date": datetime(2023, 10, 26, 10, 0, 0), "ip_address": "192.168.1.1"
            },
            "r1_2": {
                "review_id": "r1_2", "reviewer_id": "u1", "product_id": "p3",
                "review_text": "Another great product from this brand!",
                "rating": 4, "submission_date": datetime(2023, 10, 20, 9, 0, 0), "ip_address": "192.168.1.1"
            },
            "r_p1_2": {
                "review_id": "r_p1_2", "reviewer_id": "u4", "product_id": "p1",
                "review_text": "Good purchase, very satisfied.",
                "rating": 4, "submission_date": datetime(2023, 10, 24, 16, 0, 0), "ip_address": "192.168.1.4"
            }
        }
        mock_products_full_data = {
            "p1": {"product_id": "p1", "product_name": "EcoSmart Water Bottle", "category": "Kitchen"},
            "p3": {"product_id": "p3", "product_name": "Zen Garden Kit", "category": "Gardening"}
        }
        mock_reviewers_full_data = {
            "u1": {"reviewer_id": "u1", "username": "HappyCustomer", "email": "happy@example.com", "registration_date": datetime(2022, 1, 1)},
            "u4": {"reviewer_id": "u4", "username": "AnotherReviewer", "email": "another@example.com", "registration_date": datetime(2022, 5, 20)},
        }
        mock_flags_full_data = [
            {"flag_id": str(uuid.uuid4()), "review_id": "r1", "flag_reason": "suspicious_ip",
             "flag_details": {"ip": "192.168.1.1", "count": 3}, "flagged_by": "system",
             "flagged_date": datetime(2023, 10, 26, 10, 5, 0), "status": "pending", "moderator_id": None, "action_date": None},
            {"flag_id": str(uuid.uuid4()), "review_id": "r1", "flag_reason": "duplicate_text",
             "flag_details": {"duplicate_of": ["r1_dup"]}, "flagged_by": "system",
             "flagged_date": datetime(2023, 10, 26, 10, 10, 0), "status": "pending", "moderator_id": None, "action_date": None},
        ]


        review = mock_reviews_full_data.get(review_id_str)
        if not review:
            return jsonify({"message": "Review not found"}), 404

        product = mock_products_full_data.get(review['product_id'])
        reviewer = mock_reviewers_full_data.get(review['reviewer_id'])
        flags = [f for f in mock_flags_full_data if f['review_id'] == review_id_str]

        # Calculate reviewer stats
        reviewer_reviews = [r for r in mock_reviews_full_data.values() if r['reviewer_id'] == reviewer['reviewer_id']]
        total_reviewer_reviews = len(reviewer_reviews)
        avg_reviewer_rating = sum(r['rating'] for r in reviewer_reviews) / total_reviewer_reviews if total_reviewer_reviews else 0

        # Calculate product stats
        product_reviews = [r for r in mock_reviews_full_data.values() if r['product_id'] == product['product_id']]
        total_product_reviews = len(product_reviews)
        avg_product_rating = sum(r['rating'] for r in product_reviews) / total_product_reviews if total_product_reviews else 0


        response_data = {
            "review": {
                "review_id": str(review["review_id"]),
                "review_text": review["review_text"],
                "rating": review["rating"],
                "submission_date": review["submission_date"].isoformat(),
                "ip_address": review["ip_address"]
            },
            "product": {
                "product_id": str(product["product_id"]),
                "product_name": product["product_name"]
            },
            "reviewer": {
                "reviewer_id": str(reviewer["reviewer_id"]),
                "username": reviewer["username"],
                "email": reviewer["email"]
            },
            "flags": [
                {
                    "flag_id": str(f["flag_id"]),
                    "flag_reason": f["flag_reason"],
                    "flag_details": f["flag_details"],
                    "flagged_by": f["flagged_by"],
                    "flagged_date": f["flagged_date"].isoformat(),
                    "status": f["status"],
                    "moderator_id": f["moderator_id"],
                    "action_date": f["action_date"].isoformat() if f["action_date"] else None
                } for f in flags
            ],
            "reviewer_stats": {
                "total_reviews": total_reviewer_reviews,
                "avg_rating": round(avg_reviewer_rating, 2)
            },
            "product_stats": {
                "total_product_reviews": total_product_reviews,
                "avg_product_rating": round(avg_product_rating, 2)
            }
        }
        return jsonify(response_data), 200
    ```

**US2.4: Integrate Dashboard with Detailed View**
*   **Implementation Plan:** This is a frontend integration. The `ModeratorDashboard.js` component will be updated to include `Link` components (from React Router) on each flagged review row, allowing navigation to the `/review/:reviewId` path where `DetailedReviewView.js` is rendered.
*   **Data Models & Architecture:** Frontend routing.
*   **Assumptions & Technical Decisions:** React Router is properly configured in the main application.
*   **Code Snippets/Pseudocode:** Included in US1.2 code snippet.

---

#### **Tasks for US3: Mark Review as Abusive/Legitimate**

**US3.1: Design Review Action UI/UX**
*   **Implementation Plan:** Design UI elements within the `DetailedReviewView` (US2.1) to allow moderators to mark a review as 'Abusive' or 'Legitimate'. This includes:
    *   Prominent buttons for "Mark as Abusive" and "Mark as Legitimate".
    *   A confirmation dialog before committing the action.
    *   Visual feedback after an action is taken.
*   **Data Models & Architecture:** N/A (Design phase).
*   **Assumptions & Technical Decisions:** Focus on clear, unambiguous action buttons and a crucial confirmation step.
*   **Code Snippets/Pseudocode:** N/A

**US3.2: Develop Review Action Front-end**
*   **Implementation Plan:** Implement the action buttons and confirmation logic within the `DetailedReviewView.js` component. On click, these buttons will trigger an API call to the `POST /api/reviews/{review_id}/action` endpoint (US3.3) with the chosen action and the moderator's ID.
*   **Data Models & Architecture:** Integrates with `Moderation Service`'s `POST /api/reviews/{review_id}/action` endpoint.
*   **Assumptions & Technical Decisions:** Moderator ID will be retrieved from a client-side authentication context (placeholder for now). The UI will optimistically update or re-fetch data after a successful action.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // DetailedReviewView.js (Frontend - additions)
    // ... inside DetailedReviewView component, after loading/error checks

    const handleModeratorAction = async (actionType) => {
        if (window.confirm(`Are you sure you want to mark this review as ${actionType}? This action will update all pending flags for this review.`)) {
            try {
                // In a real app, moderator_id would come from authenticated user context
                const moderatorId = "moderator_alpha"; // Placeholder
                const response = await axios.post(`/api/reviews/${reviewId}/action`, {
                    action: actionType, // 'abusive' or 'legitimate'
                    moderator_id: moderatorId,
                });
                if (response.status === 200) {
                    alert(`Review and its pending flags successfully marked as ${actionType}.`);
                    // Re-fetch details to show updated status
                    // This is simpler than complex state management for this sprint
                    window.location.reload(); // Or more gracefully: fetchReviewDetails();
                }
            } catch (err) {
                alert(`Failed to mark review as ${actionType}. Error: ${err.response?.data?.message || err.message}`);
                console.error(err);
            }
        }
    };

    return (
        <div className="detailed-review-view">
            {/* ... existing review, flag, reviewer, product details */}

            <section className="moderator-actions">
                <h2>Moderator Actions</h2>
                <button onClick={() => handleModeratorAction('abusive')} disabled={loading}>Mark as Abusive</button>
                <button onClick={() => handleModeratorAction('legitimate')} disabled={loading}>Mark as Legitimate</button>
            </section>
            {/* ... rest of the component */}
        </div>
    );
    ```

**US3.3: Implement API for Review Action**
*   **Implementation Plan:** Implement `POST /api/reviews/{review_id}/action` in the `Moderation Service`. This endpoint will receive the `review_id`, `action` ('abusive' or 'legitimate'), and `moderator_id`. It will:
    1.  Validate input parameters.
    2.  Find all `Flag` records associated with the `review_id` that are currently `pending`.
    3.  Update the `status` of these flags to the `action_type` (e.g., 'abusive' or 'legitimate').
    4.  Set the `moderator_id` and `action_date` for these flags.
    5.  Potentially update the overall `Review.status` based on the moderator's decision.
*   **Data Models & Architecture:** `Moderation Service` interacts with PostgreSQL, specifically updating the `Flag` table and potentially the `Review` table.
*   **Assumptions & Technical Decisions:** A single action on the detailed view will apply to *all* currently `pending` flags for that review for simplicity in this sprint. Proper transaction management will be used for database updates.
*   **Code Snippets/Pseudocode:**
    ```python
    # Moderation Service (Python/Flask or FastAPI pseudocode)
    from flask import Flask, jsonify, request
    from datetime import datetime
    import uuid

    # Assume app = Flask(__name__)
    # Assume mock_flags_full_data is available and mutable for this mock endpoint
    # (as in previous thought block, containing rich mock data for flags)

    @app.route('/api/reviews/<uuid:review_id>/action', methods=['POST'])
    def review_action(review_id):
        data = request.get_json()
        action_type = data.get('action') # 'abusive' or 'legitimate'
        moderator_id = data.get('moderator_id') # UUID of the moderator taking action

        if action_type not in ['abusive', 'legitimate']:
            return jsonify({"message": "Invalid action type. Must be 'abusive' or 'legitimate'."}), 400
        if not moderator_id:
            return jsonify({"message": "Moderator ID is required."}), 400

        review_id_str = str(review_id)
        updated_flags_count = 0

        # In a real system, this would involve a database transaction:
        # with db_session.begin():
        #     flags_to_update = db_session.query(Flag).filter(
        #         Flag.review_id == review_id_str,
        #         Flag.status == 'pending'
        #     ).all()
        #     for flag in flags_to_update:
        #         flag.status = action_type
        #         flag.moderator_id = moderator_id
        #         flag.action_date = datetime.now()
        #         updated_flags_count += 1
        #     # Optional: Update the overall review status if needed
        #     # review = db_session.query(Review).get(review_id_str)
        #     # if review:
        #     #     review.status = 'rejected' if action_type == 'abusive' else 'approved'

        # For mock data:
        for flag in mock_flags_full_data: # Iterate through the globally available mock flags
            if flag['review_id'] == review_id_str and flag['status'] == 'pending':
                flag['status'] = action_type
                flag['moderator_id'] = moderator_id
                flag['action_date'] = datetime.now()
                updated_flags_count += 1
                # Here, we'd also update the corresponding review's status in mock_reviews_full_data if applicable.

        if updated_flags_count > 0:
            return jsonify({"message": f"Review and its {updated_flags_count} pending flags updated to '{action_type}'.", "updated_flags": updated_flags_count}), 200
        else:
            # Could also mean the review_id itself doesn't exist, or no pending flags for it
            return jsonify({"message": "No pending flags found for this review or review not found."}), 404
    ```
