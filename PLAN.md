# Sprint Backlog Implementation Plan

**Sprint Goal:** Establish the foundational rule-based review abuse detection and provide moderators with the initial tools to identify, investigate, and take basic action on suspicious reviews and reviewers.

---

## Overall Architecture Decisions

*   **Microservices:** We will adopt a microservice architecture for modularity, scalability, and independent deployment.
    *   `RuleEngineService`: Dedicated to ingesting review data, applying configured rules, and flagging suspicious items.
    *   `ModerationService`: Provides APIs for the suspicious activity dashboard, reviewer/product investigation, and moderator actions (marking reviews/reviewers).
    *   Existing `ReviewService`, `UserService`, `ProductService` are assumed to exist and provide necessary data.
*   **Message Queue (Kafka):** For asynchronous, real-time event processing. This ensures that review submissions are not blocked by abuse detection logic and allows for scalable processing of events.
    *   `review_created` topic: Reviews are published here upon creation.
    *   `review_flagged` topic: `RuleEngineService` publishes events here when a rule violation is detected.
    *   `moderator_action_taken` topic: `ModerationService` publishes events here for audit and potential downstream effects.
*   **Database (PostgreSQL):** Chosen for its robustness, ACID compliance, and excellent support for JSONB, which is ideal for storing flexible rule configurations and metadata.
*   **Frontend:** A Single-Page Application (SPA) using a modern JavaScript framework (e.g., React/Vue) will be developed for the Moderator Dashboard and Admin interface.
*   **Authentication/Authorization:** For internal tools, we will implement a robust authentication/authorization layer (e.g., OAuth2, JWT) to ensure only authorized moderators and data scientists can access sensitive functionalities.

---

## Consolidated Data Models

1.  **`rules` table (New - for RuleEngineService)**
    *   `rule_id` (PK, UUID): Unique identifier for the rule.
    *   `rule_name` (VARCHAR): Human-readable name (e.g., "IP Velocity Check").
    *   `rule_description` (TEXT): Detailed description of what the rule detects.
    *   `rule_type` (VARCHAR - e.g., 'IP_VELOCITY', 'CONTENT_SIMILARITY', 'NEW_USER_HIGH_RATING'): Categorization of the rule's logic.
    *   `rule_config_json` (JSONB): Stores rule-specific parameters (e.g., `{"time_window_minutes": 5, "review_count_threshold": 3}`).
    *   `is_active` (BOOLEAN, default TRUE): Flag to enable/disable rules.
    *   `created_at` (TIMESTAMP): Timestamp of rule creation.
    *   `updated_at` (TIMESTAMP): Timestamp of last rule update.

2.  **`flagged_items` table (New - for RuleEngineService & ModerationService)**
    *   `flag_id` (PK, UUID): Unique identifier for the flagged instance.
    *   `item_type` (VARCHAR - 'review', 'reviewer', 'product'): Type of entity being flagged.
    *   `item_id` (UUID): ID of the flagged review, reviewer, or product.
    *   `product_id` (UUID - FK to `products.product_id`, NULLABLE): For easier querying of product-related flags.
    *   `reviewer_id` (UUID - FK to `reviewers.reviewer_id`, NULLABLE): For easier querying of reviewer-related flags.
    *   `rule_id` (FK to `rules.rule_id`, NULLABLE): Which rule triggered the flag (null if manually flagged).
    *   `flag_reason` (TEXT): A brief description of why the item was flagged.
    *   `severity` (ENUM - 'low', 'medium', 'high', default 'medium'): Indicates the criticality of the flag.
    *   `status` (ENUM - 'open', 'investigating', 'resolved_abusive', 'resolved_false_positive', default 'open'): Current status of the investigation.
    *   `flagged_at` (TIMESTAMP): When the item was flagged.
    *   `metadata_json` (JSONB): Additional context (e.g., violating IPs, similar review IDs, reason for manual flag).

3.  **`reviews` table (Existing - to be extended)**
    *   *(Existing columns: `id`, `reviewer_id`, `product_id`, `rating`, `content`, `created_at`)*
    *   `abuse_status` (ENUM - 'none', 'abusive', 'disputed', default 'none'): Current moderation status of the review.
    *   `moderated_by_id` (FK to `users.user_id`, NULLABLE): ID of the moderator who last acted on this review.
    *   `moderated_at` (TIMESTAMP, NULLABLE): When the review's status was last moderated.

4.  **`reviewers` / `users` table (Existing - to be extended)**
    *   *(Existing columns: `reviewer_id`, `username`, `email`, `registration_date`)*
    *   `abuse_status` (ENUM - 'none', 'abusive', 'fraudulent', 'suspended', default 'none'): Current moderation status of the reviewer account.
    *   `moderated_by_id` (FK to `users.user_id`, NULLABLE): ID of the moderator who last acted on this reviewer.
    *   `moderated_at` (TIMESTAMP, NULLABLE): When the reviewer's status was last moderated.
    *   `abuse_reason` (TEXT, NULLABLE): Specific reason for the reviewer's abuse status.

5.  **`reviewer_activity_log` table (New - for Reviewer Profile Investigation)**
    *   `activity_id` (PK, UUID)
    *   `reviewer_id` (FK to `reviewers.reviewer_id`)
    *   `activity_type` (ENUM - 'review_posted', 'login', 'account_update', 'ip_change', etc.)
    *   `ip_address` (INET): IP address associated with the activity.
    *   `user_agent` (TEXT): User-Agent string from the activity.
    *   `timestamp` (TIMESTAMP)
    *   `review_id` (FK to `reviews.id`, NULLABLE): If the activity is `review_posted`.
    *   `metadata_json` (JSONB): Any other relevant context for the activity.

6.  **`ip_to_reviewer_map` table (New - for Linked Accounts)**
    *   `ip_address` (INET)
    *   `reviewer_id` (FK to `reviewers.reviewer_id`)
    *   `first_seen` (TIMESTAMP): First time this IP was associated with this reviewer.
    *   `last_seen` (TIMESTAMP): Last time this IP was associated with this reviewer.
    *   *(Composite PK on `ip_address`, `reviewer_id`)*

7.  **`moderator_actions_log` table (New - for Audit Trail)**
    *   `action_id` (PK, UUID)
    *   `moderator_id` (FK to `users.user_id`)
    *   `action_type` (ENUM - 'mark_review_abusive', 'mark_reviewer_fraudulent', 'suspend_reviewer', 'resolve_flag_false_positive', etc.)
    *   `item_type` (VARCHAR - 'review', 'reviewer', 'flag')
    *   `item_id` (UUID): ID of the review, reviewer, or flag that was acted upon.
    *   `action_details` (JSONB): Specifics of the action (e.g., `{"reason": "spam", "previous_status": "none", "new_status": "abusive"}`).
    *   `timestamp` (TIMESTAMP)

---

## User Story 1.1: Basic Rule-Based Detection

*   **Task 1.1.1: Research and define initial set of suspicious behavior rules (8h)**
    *   **Implementation Plan:** This will be a collaborative effort between the development team and data scientists/product owners. We will define a set of initial rules based on common abuse patterns.
    *   **Assumptions & Technical Decisions:**
        *   Initial rules will focus on easily identifiable patterns.
        *   Rules are configurable and dynamic (can be changed without code deployment).
    *   **Example Rules (Conceptual):**
        1.  `IP_VELOCITY_CHECK`: Triggers if a single IP address posts more than `X` reviews for different products within `Y` minutes.
        2.  `CONTENT_SIMILARITY_CHECK`: Triggers if a review's content has more than `Z`% similarity (e.g., using Jaccard or Levenshtein distance) to another review by a different reviewer.
        3.  `NEW_USER_HIGH_RATING_VELOCITY`: Triggers if a reviewer account younger than `A` days posts `B` five-star reviews within `C` hours.

*   **Task 1.1.2: Design data schema for storing review rules and configurations (12h)**
    *   **Implementation Plan:** Use the `rules` table as defined above. The `rule_config_json` field will allow flexibility for different rule types without schema changes.
    *   **Assumptions & Technical Decisions:**
        *   PostgreSQL's JSONB data type is key for flexibility.
        *   Each rule type will have a defined schema for its `rule_config_json` that the `RuleEngineService` understands.

*   **Task 1.1.3: Develop service to ingest review data and apply configured rules (20h)**
    *   **Implementation Plan:** Develop the `RuleEngineService`. This service will consume `review_created` events from Kafka, fetch active rules from the `rules` table, apply them to the incoming review data, and publish `review_flagged` events if violations occur, populating the `flagged_items` table.
    *   **Architecture:** `RuleEngineService` (Python/Go) consuming Kafka messages, interacting with PostgreSQL.
    *   **Assumptions & Technical Decisions:**
        *   Near real-time processing of reviews.
        *   Database queries for rules and review history need to be optimized for performance.
        *   Error handling and dead-letter queues for Kafka processing.

*   **Task 1.1.4: Implement mechanism to flag reviews/reviewers based on rule violations (16h)**
    *   **Implementation Plan:** The `_create_flag` method within `RuleEngineService` will handle this, inserting records into the `flagged_items` table. For flagging reviewers directly (not just reviews associated with them), separate rules or a manual flagging mechanism will be needed.
    *   **Assumptions & Technical Decisions:**
        *   The `flagged_items` table is central to storing all detected abuses.
        *   Initial flags are always 'open' for moderator review.

*   **Task 1.1.5: Create admin interface for data scientists to define/update rules (24h)**
    *   **Implementation Plan:** Develop a basic web application (e.g., using Flask/Django for backend, simple HTML/JS or React/Vue for frontend) that allows CRUD operations on the `rules` table.
    *   **Architecture:** Simple Admin Frontend (React/Vue) interacting with a dedicated Admin Backend API (Python/Flask) which then interacts with the `rules` PostgreSQL table.
    *   **Key Features:** List rules, add new rule (with form for `rule_type` and `rule_config_json`), edit existing rules, activate/deactivate rules.
    *   **Assumptions & Technical Decisions:**
        *   Internal tool, so UI/UX can be functional rather than highly polished.
        *   Robust input validation for `rule_config_json` based on `rule_type`.
        *   Basic user authentication for data scientists.

---

## User Story 1.2: Suspicious Activity Dashboard

*   **Task 1.2.1: Design dashboard UI/UX for displaying flagged items (16h)**
    *   **Implementation Plan:** Create wireframes and mockups. The dashboard will provide an overview of suspicious activities and detailed lists.
    *   **Key Components:**
        *   Summary widgets: Total flagged reviews, reviewers, products.
        *   Filter/Sort bar: By item type, severity, status, date range.
        *   Paginated table: Listing flagged items with key info (ID, Type, Primary Reason, Flagged At, Status).
        *   Clickable rows: Navigate to detailed investigation pages.
    *   **Assumptions & Technical Decisions:**
        *   Prioritize clarity and quick identification of critical items.
        *   Use a consistent design system.

*   **Task 1.2.2: Develop backend API to query flagged products and reviewers (20h)**
    *   **Implementation Plan:** Create endpoints within the `ModerationService` to serve data to the dashboard. These APIs will primarily query the `flagged_items` table.
    *   **API Endpoints (example):**
        *   `GET /api/v1/moderation/dashboard/summary`: Returns counts of flagged items by type and status.
        *   `GET /api/v1/moderation/flagged_items?type={review|reviewer|product}&status={open|...}&sort={flagged_at|...}&page={x}&limit={y}`: Returns a paginated list of flagged items.
    *   **Assumptions & Technical Decisions:**
        *   RESTful API design.
        *   Pagination and robust filtering are crucial for dashboard performance and usability.

*   **Task 1.2.3: Implement frontend components to display the dashboard with high-level reasons (24h)**
    *   **Implementation Plan:** Develop React/Vue components consuming the `ModerationService` APIs.
    *   **Frontend Components:** `DashboardSummary`, `FlaggedItemsTable`, `FilterPanel`, `PaginationControls`.
    *   **Assumptions & Technical Decisions:**
        *   Client-side routing for navigating between dashboard and detail views.
        *   Good loading states and error handling.

---

## User Story 1.3: Reviewer Profile Investigation

*   **Task 1.3.1: Design data model for comprehensive reviewer profiles (history, IP, linked accounts) (16h)**
    *   **Implementation Plan:** Implement the `reviewer_activity_log` and `ip_to_reviewer_map` tables as defined in the consolidated data models. This provides a granular history for investigation.
    *   **Assumptions & Technical Decisions:**
        *   Existing `reviewers` table is the primary source for basic reviewer information.
        *   Logging all significant reviewer activities is critical for detecting sophisticated abuse.
        *   `ip_to_reviewer_map` provides a quick way to identify reviewers sharing IPs.

*   **Task 1.3.2: Develop backend API to retrieve a reviewer's full activity details (24h)**
    *   **Implementation Plan:** Create an API endpoint within the `ModerationService` that aggregates data from `reviewers`, `reviews`, `reviewer_activity_log`, `ip_to_reviewer_map`, and `flagged_items`.
    *   **API Endpoint:** `GET /api/v1/moderation/reviewer/{reviewer_id}`
    *   **Assumptions & Technical Decisions:**
        *   Complex queries will require careful indexing for performance.
        *   Data aggregation is handled server-side to simplify the frontend.

*   **Task 1.3.3: Build frontend component to display detailed reviewer profiles (20h)**
    *   **Implementation Plan:** Develop a new React/Vue page/component to display the data fetched by the `/reviewer/{reviewer_id}` API.
    *   **Frontend Components:** `ReviewerInfoCard`, `RecentReviewsList`, `IPActivityTable`, `LinkedAccountsSection`, `ReviewerFlagsHistory`.
    *   **Assumptions & Technical Decisions:**
        *   Clear, tabbed interface to organize different aspects of the reviewer profile.
        *   Links to individual review pages and other reviewer profiles (for linked accounts).

---

## User Story 1.4: Product-Level Abuse View

*   **Task 1.4.1: Design data model to associate suspicious scores with individual reviews under a product (12h)**
    *   **Implementation Plan:** This is covered by the `flagged_items` table. We ensure `product_id` is a column in `flagged_items` to simplify queries for product-level views.
    *   **Assumptions & Technical Decisions:**
        *   No new tables needed, just leveraging the existing `flagged_items` table structure.

*   **Task 1.4.2: Develop backend API to fetch all reviews for a flagged product with scores (16h)**
    *   **Implementation Plan:** Create an API endpoint in `ModerationService` that retrieves all reviews for a given product and enriches them with any associated flag data from `flagged_items`.
    *   **API Endpoint:** `GET /api/v1/moderation/product/{product_id}/reviews`
    *   **Assumptions & Technical Decisions:**
        *   Efficient database joins/sub-queries are crucial for performance when fetching all reviews and their flags.

*   **Task 1.4.3: Implement frontend view for product-level abuse details (18h)**
    *   **Implementation Plan:** Develop a new React/Vue page/component for displaying product-level abuse.
    *   **Frontend Components:** `ProductHeaderInfo`, `ProductReviewsTableWithFlags` (a table with columns for review details, and a dedicated column/icon for flag status).
    *   **Assumptions & Technical Decisions:**
        *   Clear visual cues (e.g., color-coding, icons) for flagged reviews.
        *   Ability to sort/filter reviews within the product view (e.g., show only flagged reviews).

---

## User Story 1.5: Action: Mark Review as Abusive

*   **Task 1.5.1: Design database schema to store review abuse status and moderator actions (8h)**
    *   **Implementation Plan:** Extend the `reviews` table with `abuse_status`, `moderated_by_id`, `moderated_at`. Implement the `moderator_actions_log` table for auditing.
    *   **Assumptions & Technical Decisions:**
        *   Directly updating the `reviews` table is suitable for the primary status.
        *   An immutable audit log (`moderator_actions_log`) is essential for accountability.

*   **Task 1.5.2: Develop API endpoint for moderators to mark a review as abusive (12h)**
    *   **Implementation Plan:** Create a `POST` API endpoint in `ModerationService` to update a review's `abuse_status` and record the action in `moderator_actions_log`.
    *   **API Endpoint:** `POST /api/v1/moderation/reviews/{review_id}/mark_abusive`
        *   Request Body: `{"reason": "...", "moderator_id": "...", "new_status": "abusive"}`
    *   **Assumptions & Technical Decisions:**
        *   Transactionality: Both update and log operations should succeed or fail together.
        *   Requires proper moderator authentication and authorization.

*   **Task 1.5.3: Integrate "Mark as Abusive" button/workflow into review detail view (10h)**
    *   **Implementation Plan:** Add a button/action to the frontend review detail views (from 1.3.3 or 1.4.3).
    *   **Frontend Integration:**
        *   A "Mark as Abusive" button.
        *   A confirmation modal to input a reason.
        *   Call to the `mark_review_abusive` API.
        *   UI update to reflect the new `abuse_status`.

---

## User Story 1.6: Action: Mark Reviewer as Abusive/Fraudulent

*   **Task 1.6.1: Design database schema to store reviewer abuse status (8h)**
    *   **Implementation Plan:** Extend the `reviewers` (or `users`) table with `abuse_status`, `moderated_by_id`, `moderated_at`, and `abuse_reason`.
    *   **Assumptions & Technical Decisions:**
        *   Directly updating the `reviewers` table is sufficient for the primary status.
        *   The `abuse_reason` field provides context for the status.

*   **Task 1.6.2: Develop API endpoint for moderators to mark a reviewer as fraudulent/abusive (12h)**
    *   **Implementation Plan:** Create a `POST` API endpoint in `ModerationService` to update a reviewer's `abuse_status` and log the action.
    *   **API Endpoint:** `POST /api/v1/moderation/reviewers/{reviewer_id}/mark_status`
        *   Request Body: `{"new_status": "abusive" | "fraudulent" | "suspended", "reason": "...", "moderator_id": "..."}`
    *   **Assumptions & Technical Decisions:**
        *   Same transactional and authorization considerations as marking reviews.

*   **Task 1.6.3: Integrate "Mark Reviewer" action into reviewer profile view (10h)**
    *   **Implementation Plan:** Add a button/dropdown to the reviewer profile view (from 1.3.3) to allow moderators to change a reviewer's status.
    *   **Frontend Integration:**
        *   A "Mark Reviewer Status" button or dropdown.
        *   A modal to select the new status and provide a reason.
        *   Call to the `mark_reviewer_status` API.
        *   UI update to reflect the new `abuse_status`.
