# Amazon Review Integrity System - Sprint 1 Implementation Plan

## Sprint Goal:
**Establish the foundational 'Review Integrity System' by implementing core rule-based detection, a basic moderator dashboard, initial metadata analysis, and essential moderation actions (mark abusive/legitimate) with audit logging capabilities.**

---

## Implementation Plan

### User Story 1: As a System Administrator, I want to define and configure rule-based detection parameters.

#### Task 1.1: Design schema for rule definitions (database/JSON structure).
*   **Implementation Plan:** Define a flexible schema that can accommodate various rule types (e.g., keyword-based, velocity-based). This will be stored in a NoSQL database (e.g., MongoDB) or a relational database with a JSONB column for flexibility.
*   **Data Model:**
    ```json
    {
      "rule_id": "UUID",
      "rule_name": "String",
      "rule_type": "String" // e.g., "KEYWORD_BLACKLIST", "REVIEW_VELOCITY"
      "status": "String" // e.g., "ACTIVE", "INACTIVE"
      "priority": "Integer" // 1-5, higher means more critical
      "configuration": {
        // Varies based on rule_type
        // Example for KEYWORD_BLACKLIST:
        "keywords": ["bad_word_1", "bad_word_2"],
        "match_type": "EXACT" // or "FUZZY"
        "case_sensitive": "Boolean"
        // Example for REVIEW_VELOCITY:
        "time_window_minutes": "Integer", // e.g., 60 minutes
        "max_reviews_per_user": "Integer", // e.g., 5 reviews
        "min_review_length": "Integer" // e.g., 10 characters
      },
      "created_at": "DateTime",
      "updated_at": "DateTime"
    }
    ```
*   **Architecture:** Rules will be stored in a dedicated `rules` collection/table. The backend API will interact with this storage.
*   **Assumptions:**
    *   Rules can be defined with varying levels of complexity.
    *   We will start with a few basic rule types and expand as needed.
    *   A NoSQL database (like MongoDB) is suitable for flexible schema.
*   **Technical Decisions:** Use MongoDB for rule storage due to its flexible document model, which accommodates diverse rule configurations without schema migrations for every new rule type.

#### Task 1.2: Implement backend API for creating, reading, updating, and deleting detection rules.
*   **Implementation Plan:** Develop RESTful API endpoints using a framework like Flask or FastAPI.
*   **Pseudocode (Python/Flask-like):**
    ```python
    @app.route('/api/rules', methods=['POST'])
    def create_rule():
        data = request.json
        # Validate data against schema
        # Save rule to database
        # Return new rule ID and status 201

    @app.route('/api/rules/<rule_id>', methods=['GET'])
    def get_rule(rule_id):
        # Retrieve rule from database by rule_id
        # Return rule data or 404

    @app.route('/api/rules/<rule_id>', methods=['PUT'])
    def update_rule(rule_id):
        data = request.json
        # Validate data
        # Update rule in database
        # Return updated rule data or 404

    @app.route('/api/rules/<rule_id>', methods=['DELETE'])
    def delete_rule(rule_id):
        # Delete rule from database
        # Return 204 or 404
    ```
*   **Architecture:** A dedicated microservice (Rule Management Service) will handle these API calls.
*   **Assumptions:**
    *   Standard CRUD operations are sufficient for rule management.
    *   Authentication and authorization for admin access will be handled by an API gateway or middleware (not in scope for this task).
*   **Technical Decisions:** Use a lightweight Python web framework (e.g., FastAPI) for its speed and Pydantic for data validation.

#### Task 1.3: Develop basic UI for administrators to input and manage rules.
*   **Implementation Plan:** Create a simple web interface with forms for creating/editing rules and a table for listing existing rules. Use a basic frontend framework or vanilla JavaScript.
*   **Code Snippet (HTML/JavaScript - simplified):**
    ```html
    <!-- rules.html -->
    <form id="ruleForm">
        <label for="ruleName">Rule Name:</label>
        <input type="text" id="ruleName" required><br>
        <label for="ruleType">Rule Type:</label>
        <select id="ruleType">
            <option value="KEYWORD_BLACKLIST">Keyword Blacklist</option>
            <option value="REVIEW_VELOCITY">Review Velocity</option>
        </select><br>
        <div id="configFields">
            <!-- Dynamic fields based on ruleType -->
        </div>
        <button type="submit">Save Rule</button>
    </form>

    <div id="rulesList">
        <!-- Rules will be loaded here -->
    </div>

    <script>
        document.getElementById('ruleForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const ruleData = {
                rule_name: document.getElementById('ruleName').value,
                rule_type: document.getElementById('ruleType').value,
                configuration: { /* build dynamically */ }
            };
            const response = await fetch('/api/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(ruleData)
            });
            if (response.ok) {
                alert('Rule saved!');
                // Reload rules list
            } else {
                alert('Error saving rule.');
            }
        });

        // Function to fetch and display rules
        async function loadRules() {
            const response = await fetch('/api/rules');
            const rules = await response.json();
            // Render rules in #rulesList
        }
        loadRules();
    </script>
    ```
*   **Architecture:** Frontend application hosted separately, consuming the Rule Management Service API.
*   **Assumptions:**
    *   A simple single-page application is sufficient for the MVP.
    *   Focus on functionality over elaborate UI/UX for the initial sprint.
*   **Technical Decisions:** Use a minimal frontend setup (e.g., plain HTML/CSS/JS) to quickly deliver the functionality, avoiding complex frameworks for this initial administrative UI.

#### Task 1.4: Implement rule engine to apply configured rules to incoming reviews.
*   **Implementation Plan:** Develop a service that consumes new reviews, fetches active rules, and applies them. Each rule will have a corresponding evaluation logic. The engine will output flags for suspicious reviews.
*   **Data Model (Flagged Review):**
    ```json
    {
      "flag_id": "UUID",
      "review_id": "UUID",
      "flagged_at": "DateTime",
      "status": "String", // PENDING, INVESTIGATING, ABUSIVE, LEGITIMATE
      "flags": [
        {
          "rule_id": "UUID",
          "rule_name": "String",
          "reason": "String", // e.g., "Keyword 'bad_word_1' detected", "High review velocity"
          "severity": "Integer", // Inherited from rule priority
          "evidence": { /* specific data points that triggered the flag */ }
        }
      ],
      "moderation_actions": [] // Link to User Story 7
    }
    ```
*   **Pseudocode (Python):**
    ```python
    class RuleEngine:
        def __init__(self, rule_service):
            self.rule_service = rule_service # Service to fetch active rules

        def evaluate_review(self, review_data):
            active_rules = self.rule_service.get_active_rules()
            flags = []
            for rule in active_rules:
                if rule['rule_type'] == 'KEYWORD_BLACKLIST':
                    if self._check_keyword_blacklist(review_data, rule['configuration']):
                        flags.append(self._create_flag(rule, "Keyword detected"))
                elif rule['rule_type'] == 'REVIEW_VELOCITY':
                    if self._check_review_velocity(review_data, rule['configuration']):
                        flags.append(self._create_flag(rule, "High review velocity"))
                # Add more rule type evaluations

            if flags:
                return {
                    "review_id": review_data['review_id'],
                    "flagged_at": datetime.now(),
                    "status": "PENDING",
                    "flags": flags
                }
            return None # Not flagged

        def _check_keyword_blacklist(self, review_data, config):
            review_text = review_data.get('review_text', '').lower()
            for keyword in config['keywords']:
                if config.get('case_sensitive', False):
                    if keyword in review_data.get('review_text', ''): return True
                elif keyword.lower() in review_text: return True
            return False

        def _check_review_velocity(self, review_data, config):
            # Placeholder: In a real system, this would query historical reviews
            # from the same user within the time window.
            # For MVP, assume a mock function or simple check.
            user_id = review_data.get('user_id')
            recent_reviews = self.review_history_service.get_recent_reviews(user_id, config['time_window_minutes'])
            return len(recent_reviews) > config['max_reviews_per_user']

        def _create_flag(self, rule, reason):
            return {
                "rule_id": rule['rule_id'],
                "rule_name": rule['rule_name'],
                "reason": reason,
                "severity": rule['priority'],
                "evidence": {} # Populate with actual evidence, e.g., detected keyword
            }

    # Integration point:
    # new_review = # incoming review data
    # flagged_review_data = rule_engine.evaluate_review(new_review)
    # if flagged_review_data:
    #    save_flagged_review(flagged_review_data) # To a 'flagged_reviews' collection/table
    ```
*   **Architecture:** A separate Rule Engine Service will be implemented. It will subscribe to a message queue (e.g., Kafka, SQS) for new review events.
*   **Assumptions:**
    *   Reviews are ingested into the system via a message queue or an API endpoint.
    *   The rule engine needs to efficiently fetch active rules.
    *   Historical review data for velocity checks is accessible (even if mocked for MVP).
*   **Technical Decisions:**
    *   Utilize a message queue for decoupling review ingestion from rule evaluation, enabling asynchronous processing and scalability.
    *   Use a dedicated Rule Engine microservice to encapsulate rule evaluation logic.

### User Story 2: As a Review Moderator, I want to see a consolidated, prioritized dashboard of potentially abusive reviews.

#### Task 2.1: Design dashboard UI layout and information architecture.
*   **Implementation Plan:** Sketch out wireframes for the dashboard. It should include a list of flagged reviews, filters (status, rule type, severity), and a summary section.
*   **Architecture:** The UI will be a web application, consuming the `Flagged Reviews API`.
*   **Assumptions:**
    *   A simple tabular layout with basic filtering is sufficient for the MVP.
    *   The focus is on providing a functional view rather than a highly polished one.
*   **Technical Decisions:** Focus on clear presentation of critical information: review ID, flagging reasons, priority, and actions.

#### Task 2.2: Implement backend API to retrieve flagged reviews and their priority.
*   **Implementation Plan:** Create a RESTful API endpoint that queries the `flagged_reviews` collection/table, applies sorting/filtering based on request parameters, and returns a paginated list of flagged reviews.
*   **Pseudocode (Python/Flask-like):**
    ```python
    @app.route('/api/moderator/flagged-reviews', methods=['GET'])
    def get_flagged_reviews():
        # Get query parameters: page, limit, status, sort_by, sort_order
        # Query 'flagged_reviews' collection/table
        # Apply filters (e.g., status='PENDING')
        # Apply sorting (e.g., by highest severity/priority first, then by flagged_at)
        # Implement pagination
        # Return a list of flagged reviews
    ```
*   **Architecture:** A dedicated `Moderator Dashboard Service` will provide this API. It will query the `flagged_reviews` data store.
*   **Assumptions:**
    *   Prioritization will be based on aggregated rule severities or a specific priority field.
    *   Basic filtering and pagination are required.
*   **Technical Decisions:** Use the same backend framework (FastAPI) for consistency. Implement server-side pagination to manage data transfer efficiently.

#### Task 2.3: Develop frontend dashboard to display flagged reviews.
*   **Implementation Plan:** Build a web page that calls the `/api/moderator/flagged-reviews` endpoint and renders the data in a sortable, filterable table.
*   **Code Snippet (HTML/JavaScript - simplified):**
    ```html
    <!-- dashboard.html -->
    <div class="filters">
        <label for="statusFilter">Status:</label>
        <select id="statusFilter">
            <option value="PENDING">Pending</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="ABUSIVE">Abusive</option>
            <option value="LEGITIMATE">Legitimate</option>
        </select>
        <button onclick="loadFlaggedReviews()">Apply Filters</button>
    </div>

    <table id="flaggedReviewsTable">
        <thead>
            <tr>
                <th>Review ID</th>
                <th>Flagging Reasons</th>
                <th>Severity</th>
                <th>Flagged At</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <!-- Flagged reviews will be inserted here -->
        </tbody>
    </table>

    <script>
        async function loadFlaggedReviews() {
            const status = document.getElementById('statusFilter').value;
            const response = await fetch(`/api/moderator/flagged-reviews?status=${status}`);
            const reviews = await response.json();
            const tbody = document.querySelector('#flaggedReviewsTable tbody');
            tbody.innerHTML = ''; // Clear previous entries

            reviews.forEach(review => {
                const row = tbody.insertRow();
                row.insertCell().textContent = review.review_id;
                row.insertCell().textContent = review.flags.map(f => f.reason).join(', ');
                row.insertCell().textContent = Math.max(...review.flags.map(f => f.severity)); // Max severity
                row.insertCell().textContent = new Date(review.flagged_at).toLocaleString();
                row.insertCell().textContent = review.status;
                const actionCell = row.insertCell();
                actionCell.innerHTML = `
                    <button onclick="viewReview('${review.review_id}')">View Details</button>
                    <!-- Add Mark Abusive/Legitimate buttons later -->
                `;
            });
        }
        loadFlaggedReviews(); // Initial load
    </script>
    ```
*   **Architecture:** Frontend web application.
*   **Assumptions:**
    *   Moderators will have appropriate access to this UI.
    *   The UI needs to be responsive enough to display a moderate number of flagged reviews.
*   **Technical Decisions:** Similar to Task 1.3, use vanilla JS for rapid development and focus on functionality.

#### Task 2.4: Implement basic prioritization logic for flagged reviews (e.g., based on number of flags, severity).
*   **Implementation Plan:** When retrieving flagged reviews, calculate a priority score. For MVP, this can be the highest `severity` among all flags, or the sum of severities, or a simple count of flags.
*   **Pseudocode (within `get_flagged_reviews` API):**
    ```python
    def calculate_priority(flags):
        if not flags:
            return 0
        # Option 1: Max severity
        # return max(f['severity'] for f in flags)
        # Option 2: Sum of severities
        return sum(f['severity'] for f in flags)
        # Option 3: Number of flags (implicit if sorting by count)

    # In get_flagged_reviews:
    for review in flagged_reviews_from_db:
        review['priority_score'] = calculate_priority(review['flags'])
    # Sort the results by 'priority_score' in descending order
    ```
*   **Architecture:** This logic will reside in the `Moderator Dashboard Service`'s API.
*   **Assumptions:**
    *   Initial prioritization can be heuristic.
    *   Moderators need to see the most critical reviews first.
*   **Technical Decisions:** Start with a simple prioritization algorithm (e.g., sum of flag severities) and iterate based on moderator feedback.

### User Story 3: As a System, I want to analyze review metadata.

#### Task 3.1: Identify key metadata fields for analysis.
*   **Implementation Plan:** Review typical Amazon review metadata and select fields relevant to abuse detection.
*   **Key Metadata Fields:**
    *   `review_id`
    *   `user_id` (reviewer ID)
    *   `product_id`
    *   `timestamp` (review submission time)
    *   `ip_address` (reviewer IP)
    *   `user_agent` (browser/device info)
    *   `review_text_length`
    *   `rating`
    *   `is_verified_purchase`
    *   `user_history`:
        *   `total_reviews_by_user`
        *   `avg_rating_by_user`
        *   `time_since_first_review_by_user`
        *   `recent_review_count` (e.g., last 24h/7d)
        *   `product_categories_reviewed`
*   **Architecture:** This is an input for the `Data Ingestion Pipeline` and `Metadata Analysis Algorithms`.
*   **Assumptions:**
    *   These metadata fields are available from the source system.
    *   Access to historical user review data is feasible.
*   **Technical Decisions:** Prioritize readily available metadata for the MVP, and consider additional fields for future iterations.

#### Task 3.2: Implement data ingestion pipeline for review metadata.
*   **Implementation Plan:** Design a pipeline that ingests new reviews along with their metadata. This could be a message queue (Kafka/SQS) consumer that stores the data in a dedicated data store optimized for analytics.
*   **Architecture:**
    *   **Source:** Amazon Review System (publishes reviews to a message queue).
    *   **Message Queue:** Kafka/SQS for reliable, scalable ingestion.
    *   **Ingestion Service:** Consumer of the message queue.
    *   **Data Store:** Analytical database (e.g., Cassandra, DynamoDB, or a data lake like S3 with Spark for processing) for raw and aggregated metadata.
*   **Assumptions:**
    *   An existing mechanism to push new review data to a message queue is available.
    *   The volume of reviews can be high, requiring a scalable ingestion solution.
*   **Technical Decisions:** Use AWS SQS/Kinesis for simplicity and integration with other AWS services. Store raw review data in S3 and use a simple lambda function to trigger analysis on new files.

#### Task 3.3: Develop initial algorithms to detect patterns in metadata indicative of abuse.
*   **Implementation Plan:** Implement simple detection algorithms based on identified metadata fields. These algorithms will generate flags similar to rule-based detection but might focus more on statistical anomalies.
*   **Pseudocode (Python):**
    ```python
    class MetadataAnalyzer:
        def __init__(self, data_store):
            self.data_store = data_store # Access to review and user history data

        def analyze(self, review_metadata):
            flags = []

            # 1. Review Velocity Anomaly (User-specific)
            user_id = review_metadata.get('user_id')
            timestamp = review_metadata.get('timestamp')
            recent_reviews = self.data_store.get_user_recent_reviews(user_id, timestamp, window_minutes=60)
            if len(recent_reviews) > 10: # Threshold for high velocity
                flags.append(self._create_metadata_flag("High Review Velocity", "User submitted too many reviews recently"))

            # 2. IP Address Patterns (e.g., multiple users from same IP in short time)
            ip_address = review_metadata.get('ip_address')
            reviews_from_ip = self.data_store.get_recent_reviews_by_ip(ip_address, timestamp, window_minutes=30)
            unique_users = len(set(r['user_id'] for r in reviews_from_ip))
            if unique_users > 5 and len(reviews_from_ip) > 10: # Multiple users/reviews from same IP
                flags.append(self._create_metadata_flag("Suspicious IP Activity", "Multiple users/reviews from same IP"))

            # 3. New User, High Volume, Short Reviews
            is_new_user = self.data_store.is_new_user(user_id) # e.g., < 5 total reviews
            review_text_length = review_metadata.get('review_text_length')
            if is_new_user and len(recent_reviews) > 3 and review_text_length < 50:
                flags.append(self._create_metadata_flag("New User Spam Pattern", "New user, many short reviews"))

            return flags

        def _create_metadata_flag(self, reason, evidence_summary):
            return {
                "rule_id": "METADATA_ANALYSIS_GENERATED",
                "rule_name": "Metadata Anomaly Detection",
                "reason": reason,
                "severity": 3, # Default severity for metadata flags
                "evidence": {"summary": evidence_summary}
            }
    ```
*   **Architecture:** A `Metadata Analysis Service` will consume review metadata, run these algorithms, and potentially add flags to the `flagged_reviews` data store or send them to the `Rule Engine Service` for consolidation.
*   **Assumptions:**
    *   Access to a historical data store of reviews and user activity is available.
    *   Simple heuristic algorithms will be effective enough for MVP.
*   **Technical Decisions:** Implement algorithms as a separate service that runs asynchronously. Integrate the results with the existing flagging mechanism.

### User Story 4: As a Review Moderator, I want to view the flagged review alongside the reasons/evidence for its suspicious rating.

#### Task 4.1: Extend flagged review data model to include flagging reasons/evidence.
*   **Implementation Plan:** The `Flagged Review` data model defined in Task 1.4 already includes `flags` with `reason` and `evidence`. This task confirms that the existing model is suitable.
*   **Data Model:** (As defined in Task 1.4)
    ```json
    {
      "flag_id": "UUID",
      "review_id": "UUID",
      "flagged_at": "DateTime",
      "status": "String",
      "flags": [
        {
          "rule_id": "UUID",
          "rule_name": "String",
          "reason": "String",
          "severity": "Integer",
          "evidence": { /* specific data points that triggered the flag */ }
        }
      ],
      "moderation_actions": []
    }
    ```
*   **Architecture:** No changes needed to overall architecture, just ensuring consistency in data storage.
*   **Assumptions:**
    *   The `flags` array within the `Flagged Review` document is sufficient to store all reasons and evidence.
*   **Technical Decisions:** Stick to the existing `Flagged Review` data model as it already accommodates reasons and evidence.

#### Task 4.2: Modify API to retrieve flagged review details with evidence.
*   **Implementation Plan:** The API endpoint developed in Task 2.2 (`/api/moderator/flagged-reviews`) should already return the full `Flagged Review` object, including the `flags` array with reasons and evidence. If a specific "detail" endpoint is needed, create `/api/moderator/flagged-reviews/<flag_id>`.
*   **Pseudocode (within existing `get_flagged_reviews` or new `get_flagged_review_details`):**
    ```python
    @app.route('/api/moderator/flagged-reviews/<flag_id>', methods=['GET'])
    def get_flagged_review_details(flag_id):
        # Retrieve the specific flagged review from database using flag_id
        # Ensure the full 'flags' array with 'reason' and 'evidence' is returned
        # Include original review content as well (fetch from Review Service)
        flagged_review = db.flagged_reviews.find_one({"flag_id": flag_id})
        if not flagged_review:
            return jsonify({"message": "Review not found"}), 404

        # Fetch original review content (assuming a Review Content Service exists)
        # original_review = review_content_service.get_review_by_id(flagged_review['review_id'])
        # flagged_review['original_content'] = original_review

        return jsonify(flagged_review)
    ```
*   **Architecture:** The `Moderator Dashboard Service` API. It might need to call a `Review Content Service` to fetch the actual review text.
*   **Assumptions:**
    *   The original review content is accessible via another service or data store.
*   **Technical Decisions:** Introduce a new endpoint `GET /api/moderator/flagged-reviews/{flag_id}` for detailed viewing, which aggregates data from `flagged_reviews` and the original `reviews` data store.

#### Task 4.3: Update dashboard UI to display flagging reasons/evidence.
*   **Implementation Plan:** Enhance the dashboard UI (from Task 2.3) to, upon clicking a review, show a detailed view that displays the original review text, and for each flag, its `rule_name`, `reason`, and `evidence`.
*   **Code Snippet (HTML/JavaScript - simplified for detail view):**
    ```html
    <!-- Add a modal or detail pane to dashboard.html -->
    <div id="reviewDetailModal" class="modal">
        <div class="modal-content">
            <span class="close-button" onclick="closeDetailModal()">&times;</span>
            <h2>Review Details: <span id="detailReviewId"></span></h2>
            <h3>Original Review Content:</h3>
            <p id="detailReviewContent"></p>
            <h3>Flagging Reasons and Evidence:</h3>
            <ul id="detailFlagsList">
                <!-- Details will be loaded here -->
            </ul>
        </div>
    </div>

    <script>
        async function viewReview(flag_id) {
            const response = await fetch(`/api/moderator/flagged-reviews/${flag_id}`);
            const reviewDetails = await response.json();

            document.getElementById('detailReviewId').textContent = reviewDetails.review_id;
            // document.getElementById('detailReviewContent').textContent = reviewDetails.original_content; // If fetched

            const flagsList = document.getElementById('detailFlagsList');
            flagsList.innerHTML = '';
            reviewDetails.flags.forEach(flag => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>Rule:</strong> ${flag.rule_name}<br>
                    <strong>Reason:</strong> ${flag.reason}<br>
                    <strong>Evidence:</strong> ${JSON.stringify(flag.evidence)}
                `;
                flagsList.appendChild(li);
            });

            document.getElementById('reviewDetailModal').style.display = 'block';
        }

        function closeDetailModal() {
            document.getElementById('reviewDetailModal').style.display = 'none';
        }
    </script>
    ```
*   **Architecture:** Frontend web application.
*   **Assumptions:**
    *   Moderators need to quickly grasp why a review was flagged.
    *   The evidence might be structured (JSON) and needs to be presented clearly.
*   **Technical Decisions:** Use a modal or a dedicated detail view within the dashboard for displaying comprehensive information, avoiding navigation away from the main list.

### User Story 5: As a Review Moderator, I want to be able to mark a review as abusive and trigger its removal from the platform.

#### Task 5.1: Implement backend API for marking a review as abusive.
*   **Implementation Plan:** Create an API endpoint that updates the status of a `flagged_review` to "ABUSIVE" and triggers a separate action for removal. This action will also record the moderation action in an audit log.
*   **Pseudocode (Python/Flask-like):**
    ```python
    @app.route('/api/moderator/flagged-reviews/<flag_id>/mark-abusive', methods=['POST'])
    def mark_review_abusive(flag_id):
        # Authenticate and authorize moderator
        # Update status in 'flagged_reviews' collection/table
        # flagged_review = db.flagged_reviews.find_one_and_update(
        #     {"flag_id": flag_id},
        #     {"$set": {"status": "ABUSIVE", "moderated_at": datetime.now()}}
        # )
        # if not flagged_review: return 404

        # Trigger review removal (e.g., send message to a queue)
        # removal_service.trigger_removal(flagged_review['review_id'], moderator_id, reason="Abusive")

        # Log moderation action (User Story 7)
        # audit_log_service.log_action("MARK_ABUSIVE", flag_id, moderator_id, {"review_id": flagged_review['review_id']})

        # Return success
    ```
*   **Architecture:** The `Moderator Action Service` will provide this API. It will interact with the `flagged_reviews` data store, a `Review Removal Service` (placeholder), and an `Audit Log Service`.
*   **Assumptions:**
    *   Moderator authentication and authorization are handled.
    *   The actual removal from the Amazon platform is an asynchronous process initiated by this API.
*   **Technical Decisions:** Use an idempotent POST request. The API should trigger the removal process via a message queue to ensure decoupled and reliable execution.

#### Task 5.2: Develop a UI button/action for moderators to mark abusive.
*   **Implementation Plan:** Add a "Mark Abusive" button to the review detail view on the moderator dashboard.
*   **Code Snippet (HTML/JavaScript - simplified):**
    ```html
    <!-- In the reviewDetailModal content -->
    <button onclick="markAbusive('${reviewDetails.flag_id}')">Mark as Abusive</button>

    <script>
        async function markAbusive(flag_id) {
            if (confirm('Are you sure you want to mark this review as abusive and trigger removal?')) {
                const response = await fetch(`/api/moderator/flagged-reviews/${flag_id}/mark-abusive`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ moderator_id: 'current_moderator_id' }) // Placeholder
                });
                if (response.ok) {
                    alert('Review marked as abusive and removal triggered!');
                    closeDetailModal();
                    loadFlaggedReviews(); // Reload dashboard
                } else {
                    alert('Error marking review as abusive.');
                }
            }
        }
    </script>
    ```
*   **Architecture:** Frontend web application.
*   **Assumptions:**
    *   The UI should provide clear confirmation before executing a destructive action.
*   **Technical Decisions:** Implement a simple button with a confirmation dialog for safety.

#### Task 5.3: Integrate with existing Amazon system for review removal (placeholder for now, focusing on API call).
*   **Implementation Plan:** Define a clear interface for the "review removal" process. For the MVP, this will be a simulated API call or a message sent to a queue that a placeholder "Removal Service" will acknowledge.
*   **Architecture:**
    *   `Moderator Action Service` (calls/sends message to) -> `Review Removal Service` (placeholder).
    *   The `Review Removal Service` would ideally integrate with Amazon's internal systems.
*   **Assumptions:**
    *   A dedicated service or API exists within Amazon for review removal.
    *   The `Review Removal Service` will handle the complexities of integration.
*   **Technical Decisions:** For the MVP, the `Review Removal Service` will simply log the removal request. Future iterations will involve actual integration.

### User Story 6: As a Review Moderator, I want to mark a review as legitimate (false positive).

#### Task 6.1: Implement backend API for marking a review as legitimate.
*   **Implementation Plan:** Create an API endpoint that updates the status of a `flagged_review` to "LEGITIMATE" and records the moderation action. This also provides feedback for the system learning.
*   **Pseudocode (Python/Flask-like):**
    ```python
    @app.route('/api/moderator/flagged-reviews/<flag_id>/mark-legitimate', methods=['POST'])
    def mark_review_legitimate(flag_id):
        # Authenticate and authorize moderator
        # Update status in 'flagged_reviews' collection/table
        # flagged_review = db.flagged_reviews.find_one_and_update(
        #     {"flag_id": flag_id},
        #     {"$set": {"status": "LEGITIMATE", "moderated_at": datetime.now()}}
        # )
        # if not flagged_review: return 404

        # Provide feedback for system learning (User Story 6.3)
        # feedback_service.record_false_positive(flagged_review['review_id'], flagged_review['flags'])

        # Log moderation action (User Story 7)
        # audit_log_service.log_action("MARK_LEGITIMATE", flag_id, moderator_id, {"review_id": flagged_review['review_id']})

        # Return success
    ```
*   **Architecture:** `Moderator Action Service` interacts with `flagged_reviews` data store and an `Audit Log Service`.
*   **Assumptions:**
    *   Moderator authentication and authorization are handled.
    *   Marking as legitimate does not trigger any destructive actions but rather provides feedback.
*   **Technical Decisions:** Similar to marking abusive, use an idempotent POST. The API will update the status and trigger feedback for learning.

#### Task 6.2: Develop a UI button/action for moderators to mark legitimate.
*   **Implementation Plan:** Add a "Mark Legitimate" button to the review detail view on the moderator dashboard.
*   **Code Snippet (HTML/JavaScript - simplified):**
    ```html
    <!-- In the reviewDetailModal content -->
    <button onclick="markLegitimate('${reviewDetails.flag_id}')">Mark as Legitimate</button>

    <script>
        async function markLegitimate(flag_id) {
            if (confirm('Are you sure you want to mark this review as legitimate (false positive)?')) {
                const response = await fetch(`/api/moderator/flagged-reviews/${flag_id}/mark-legitimate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ moderator_id: 'current_moderator_id' }) // Placeholder
                });
                if (response.ok) {
                    alert('Review marked as legitimate!');
                    closeDetailModal();
                    loadFlaggedReviews(); // Reload dashboard
                } else {
                    alert('Error marking review as legitimate.');
                }
            }
        }
    </script>
    ```
*   **Architecture:** Frontend web application.
*   **Assumptions:**
    *   The UI should clearly distinguish between marking abusive and legitimate.
*   **Technical Decisions:** A dedicated button with a confirmation dialog.

#### Task 6.3: Implement basic feedback loop for system learning from false positives.
*   **Implementation Plan:** When a review is marked legitimate, the system should record which rules flagged it. This data can be used to analyze false positive rates per rule or to adjust rule parameters. For MVP, simply log this feedback.
*   **Architecture:** The `Moderator Action Service` (or a dedicated `Feedback Service`) will capture this information.
*   **Assumptions:**
    *   The initial learning mechanism can be simple logging for later analysis.
    *   Automated rule tuning is out of scope for MVP.
*   **Technical Decisions:** Log the `rule_id` and `review_id` for all flags associated with a legitimately marked review. This data can be used later for rule refinement.

### User Story 7: As a System, I want to log all moderation actions.

#### Task 7.1: Design logging schema for moderation actions.
*   **Implementation Plan:** Define a schema to capture essential details of each moderation action.
*   **Data Model (Audit Log Entry):**
    ```json
    {
      "log_id": "UUID",
      "action_type": "String", // e.g., "MARK_ABUSIVE", "MARK_LEGITIMATE", "RULE_CREATED"
      "action_timestamp": "DateTime",
      "moderator_id": "String", // ID of the moderator who took the action (if applicable)
      "target_entity_type": "String", // e.g., "REVIEW", "RULE"
      "target_entity_id": "UUID", // ID of the entity that was acted upon (e.g., review_id, rule_id)
      "details": {
        // Contextual information specific to the action
        "previous_status": "String",
        "new_status": "String",
        "reason_for_action": "String", // e.g., "Moderator confirmed abuse"
        "flags_at_time_of_action": [] // Snapshot of flags when action was taken
      }
    }
    ```
*   **Architecture:** A dedicated `Audit Log Service` and a `audit_logs` data store.
*   **Assumptions:**
    *   All significant moderation and administrative actions need to be logged.
    *   The log should be immutable and provide enough detail for auditing.
*   **Technical Decisions:** Use a NoSQL database for flexible logging schema. Ensure the timestamp and `moderator_id` are always captured.

#### Task 7.2: Implement logging mechanism for "remove" action.
*   **Implementation Plan:** Integrate logging into the `mark_review_abusive` API endpoint (Task 5.1).
*   **Pseudocode (within `mark_review_abusive` function, referring to `audit_log_service`):**
    ```python
    # After updating review status and triggering removal:
    audit_log_service.log_action(
        action_type="MARK_ABUSIVE",
        action_timestamp=datetime.now(),
        moderator_id=moderator_id, # From request context
        target_entity_type="REVIEW",
        target_entity_id=flagged_review['review_id'],
        details={
            "previous_status": "PENDING", # Or current status before update
            "new_status": "ABUSIVE",
            "reason_for_action": "Moderator confirmed abuse",
            "flags_at_time_of_action": flagged_review['flags'] # Snapshot
        }
    )
    ```
*   **Architecture:** `Moderator Action Service` calls `Audit Log Service`.
*   **Assumptions:**
    *   The `Audit Log Service` provides a simple method to log events.
*   **Technical Decisions:** Implement logging as an atomic operation with the status update to ensure consistency.

#### Task 7.3: Implement logging mechanism for "mark legitimate" action.
*   **Implementation Plan:** Integrate logging into the `mark_review_legitimate` API endpoint (Task 6.1).
*   **Pseudocode (within `mark_review_legitimate` function):**
    ```python
    # After updating review status and providing feedback:
    audit_log_service.log_action(
        action_type="MARK_LEGITIMATE",
        action_timestamp=datetime.now(),
        moderator_id=moderator_id, # From request context
        target_entity_type="REVIEW",
        target_entity_id=flagged_review['review_id'],
        details={
            "previous_status": "PENDING",
            "new_status": "LEGITIMATE",
            "reason_for_action": "Moderator identified false positive",
            "flags_at_time_of_action": flagged_review['flags'] # Snapshot
        }
    )
    ```
*   **Architecture:** `Moderator Action Service` calls `Audit Log Service`.
*   **Assumptions:**
    *   Consistent logging mechanism for all moderation actions.
*   **Technical Decisions:** Reuse the `log_action` method of the `Audit Log Service`.

#### Task 7.4: Develop a basic log viewer for system administrators.
*   **Implementation Plan:** Create a simple UI page for administrators to view audit logs, with basic filtering capabilities (by action type, moderator ID, date range).
*   **Architecture:** A separate `Admin Dashboard` or an extension to the `Rule Management UI`. It will consume an API from the `Audit Log Service`.
*   **Assumptions:**
    *   A simple tabular display is sufficient for the MVP.
    *   Administrators need to verify moderation activities.
*   **Technical Decisions:** Build a simple frontend using vanilla JS, similar to the rule management UI, to query the `Audit Log Service`'s API.
