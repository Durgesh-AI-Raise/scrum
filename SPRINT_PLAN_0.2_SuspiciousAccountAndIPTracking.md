### User Story 0.2: Suspicious Account & IP Tracking

**Sprint Goal Alignment:** This user story directly supports the sprint goal by identifying and flagging reviews related to suspicious accounts and IP addresses, thus contributing to foundational review abuse detection capabilities.

---

#### **ARIS Sprint 1: Task 0.2.1 - Define criteria for suspicious accounts/IPs.** (Estimate: 6 hours)

*   **Implementation Plan:**
    *   Define initial, rule-based criteria for what constitutes a "suspicious account" and "suspicious IP address" for the MVP.
    *   For **Suspicious Accounts**, criteria might include:
        *   Account age (e.g., created less than X days ago).
        *   Number of reviews submitted by the account within a short period (e.g., Y reviews in 24 hours).
        *   Reviews across an unusually high number of unrelated product categories.
    *   For **Suspicious IPs**, criteria might include:
        *   Association with known bad IP reputation scores (e.g., from an external threat intelligence feed).
        *   Number of distinct accounts originating from a single IP address within a specific timeframe (e.g., Z distinct accounts in 24 hours).
    *   Document these criteria with clear thresholds and examples, which will serve as the basis for the flagging logic.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** Initial criteria will be simplistic and rule-based to quickly establish a baseline for detection.
    *   **Technical Decision:** Criteria values (e.g., X days, Y reviews, Z accounts, reputation score thresholds) will be externalized as configurable parameters, initially hardcoded in a configuration file but designed for future dynamic management.
*   **Code Snippets/Pseudocode:** N/A for a definition task.

---

#### **ARIS Sprint 1: Task 0.2.2 - Integrate with Amazon account/IP data sources.** (Estimate: 20 hours)

*   **Implementation Plan:**
    *   Develop an integration component or microservice (`Account/IP Data Service`) responsible for abstracting access to Amazon's internal account and IP data sources.
    *   This service will interact with existing Amazon APIs or data feeds to retrieve necessary information:
        *   **For Accounts:** `accountCreationDate`, `accountStatus`, historical review activity (to derive `totalReviews`, `last24hReviews`, `reviewCategories`).
        *   **For IPs:** IP reputation scores (from an internal or external IP threat intelligence service), and historical associations of IP addresses with accounts.
    *   Implement caching within this service to optimize performance and reduce load on source systems.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `AccountProfile` (Internal representation within ARIS):
            *   `accountId: string` (PK)
            *   `creationDate: datetime`
            *   `status: string` (e.g., 'active', 'suspended')
            *   `totalReviews: int`
            *   `last24hReviews: int` (derived from ARIS ingestion or Amazon data)
            *   `reviewCategories: set<string>` (distinct product categories reviewed by this account)
        *   `IpAddressProfile` (Internal representation within ARIS):
            *   `ipAddress: string` (PK)
            *   `lastSeen: datetime`
            *   `associatedAccountsLast24h: set<string>` (set of unique `accountId`s seen from this IP in the last 24h)
            *   `reputationScore: float` (e.g., 0-1, higher is worse)
    *   **Architecture:**
        *   `Account/IP Data Service` (e.g., AWS Lambda/Fargate with Python) acting as a proxy.
        *   Internal Amazon Account Service APIs / Data Feeds.
        *   Internal/External IP Reputation Service APIs.
        *   Caching Layer (e.g., Redis or DynamoDB with TTL) for `AccountProfile` and `IpAddressProfile`.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** Amazon's internal services provide reliable and performant APIs or data streams for account and IP information.
    *   **Assumption:** The data ingestion pipeline (0.1.2) can provide sufficient raw review data to derive aggregate metrics for accounts/IPs if not directly available from Amazon services.
    *   **Technical Decision:** Use Python and Boto3 for developing the `Account/IP Data Service` given its integration with AWS and developer familiarity.
    *   **Technical Decision:** Implement a short-lived cache (e.g., 1-4 hours TTL) for `AccountProfile` and `IpAddressProfile` to balance data freshness with performance.
*   **Code Snippets/Pseudocode:**
    ```python
    from datetime import datetime, timedelta

    # Pseudocode for Account/IP Data Service functions
    def get_account_profile(account_id):
        # Try to retrieve from cache first
        cached_profile = get_from_cache(f"account_profile:{account_id}")
        if cached_profile:
            return cached_profile

        # Call Amazon Account Service API (mocked here)
        raw_data = mock_amazon_account_service_call(account_id)
        if not raw_data: return None

        profile = {
            'accountId': account_id,
            'creationDate': datetime.fromisoformat(raw_data.get('creationDate')),
            'status': raw_data.get('status', 'active'),
            # Assume these are derived or fetched from other ARIS components
            'totalReviews': get_total_reviews_for_account(account_id), # From ARIS review data
            'last24hReviews': get_reviews_by_account_in_timeframe(account_id, timedelta(hours=24)), # From ARIS review data
            'reviewCategories': get_distinct_categories_by_account(account_id) # From ARIS review data
        }
        set_in_cache(f"account_profile:{account_id}", profile, ttl=3600) # Cache for 1 hour
        return profile

    def get_ip_profile(ip_address):
        # Try to retrieve from cache first
        cached_profile = get_from_cache(f"ip_profile:{ip_address}")
        if cached_profile:
            return cached_profile

        # Call Amazon IP Reputation Service API (mocked here)
        raw_data = mock_amazon_ip_service_call(ip_address)
        if not raw_data: return None

        profile = {
            'ipAddress': ip_address,
            'lastSeen': datetime.utcnow(),
            'reputationScore': raw_data.get('reputationScore', 0.0),
            # Assume this is derived from ARIS review data or internal logs
            'associatedAccountsLast24h': get_distinct_accounts_from_ip_in_timeframe(ip_address, timedelta(hours=24))
        }
        set_in_cache(f"ip_profile:{ip_address}", profile, ttl=3600) # Cache for 1 hour
        return profile

    # Mock functions for illustration
    def mock_amazon_account_service_call(account_id):
        # Simulate API call
        return {'creationDate': '2023-01-15T10:00:00Z', 'status': 'active'}

    def mock_amazon_ip_service_call(ip_address):
        # Simulate API call
        return {'reputationScore': 0.15}

    def get_from_cache(key): return None # Mock cache
    def set_in_cache(key, value, ttl): pass # Mock cache
    def get_total_reviews_for_account(account_id): return 100 # Mock
    def get_reviews_by_account_in_timeframe(account_id, timeframe): return 8 # Mock
    def get_distinct_categories_by_account(account_id): return {'Electronics', 'Books'} # Mock
    def get_distinct_accounts_from_ip_in_timeframe(ip_address, timeframe): return {'acc1', 'acc2'} # Mock
    ```

---

#### **ARIS Sprint 1: Task 0.2.3 - Implement suspicious account/IP flagging logic.** (Estimate: 18 hours)

*   **Implementation Plan:**
    *   Develop a `SuspiciousDetectionService` (e.g., an AWS Lambda function) that subscribes to the `ProcessedReview` stream (output of 0.1.2).
    *   For each `ProcessedReview`, the service will:
        *   Call the `Account/IP Data Service` (0.2.2) to retrieve the `AccountProfile` of the reviewer and the `IpAddressProfile` of the review's origin IP.
        *   Apply the defined criteria (from 0.2.1) to these profiles and the `ProcessedReview` data.
        *   Generate `DetectionResult` objects if any suspicious patterns are found for accounts or IPs.
    *   The `DetectionResult` will specify the `abuseType` (e.g., "Suspicious Account: High Volume", "Suspicious IP: Bad Reputation"), `severity`, and relevant `details`.
*   **Data Models and Architecture:**
    *   **Data Models:** Reuses `ProcessedReview` from 0.1.2 and `DetectionResult` from 0.1.3.
        *   `DetectionResult` will have new `detectionType` values related to suspicious accounts/IPs.
    *   **Architecture:**
        *   Processed Review Stream (Kinesis/DynamoDB Stream) -> `SuspiciousDetectionService` (AWS Lambda) -> Detection Results Stream (Kinesis/Kafka) for further processing or direct storage.
        *   `SuspiciousDetectionService` will interact with `Account/IP Data Service`.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The `ProcessedReview` object contains enough information (reviewer ID, IP address) to query the `Account/IP Data Service`.
    *   **Technical Decision:** Implement the detection logic using Python for consistency and ease of maintenance within the ARIS ecosystem.
    *   **Technical Decision:** Leverage a serverless function (AWS Lambda) for scalable, event-driven processing of new `ProcessedReview` events.
*   **Code Snippets/Pseudocode:**
    ```python
    # Pseudocode for Suspicious Account/IP Detection Logic
    # (Thresholds would come from configuration, but hardcoded here for illustration)
    SUSPICIOUS_ACCOUNT_MIN_REVIEWS_24H = 10 # More than 10 reviews in 24 hours
    SUSPICIOUS_ACCOUNT_MIN_CATEGORIES = 5 # Reviews across 5+ distinct categories
    SUSPICIOUS_IP_MIN_ACCOUNTS_24H = 5 # More than 5 distinct accounts from same IP in 24 hours
    SUSPICIOUS_IP_REPUTATION_THRESHOLD = 0.7 # IP reputation score above 0.7 (higher is worse)
    NEW_ACCOUNT_AGE_DAYS_THRESHOLD = 30 # Account less than 30 days old for new account related flags

    def detect_suspicious_account_ip_patterns(processed_review):
        flags = []

        # --- Account-based Detections ---
        account_profile = get_account_profile(processed_review.reviewerId) # Call Account/IP Data Service
        if account_profile:
            # Pattern: Sudden flurry of reviews from account
            if account_profile['last24hReviews'] > SUSPICIOUS_ACCOUNT_MIN_REVIEWS_24H:
                flags.append({
                    'type': 'SuspiciousAccount:HighVolume',
                    'severity': 'High',
                    'details': {
                        'threshold': SUSPICIOUS_ACCOUNT_MIN_REVIEWS_24H,
                        'actual_count': account_profile['last24hReviews']
                    }
                })

            # Pattern: Reviews across unrelated product categories
            if len(account_profile['reviewCategories']) >= SUSPICIOUS_ACCOUNT_MIN_CATEGORIES:
                flags.append({
                    'type': 'SuspiciousAccount:BroadCategories',
                    'severity': 'Medium',
                    'details': {
                        'threshold': SUSPICIOUS_ACCOUNT_MIN_CATEGORIES,
                        'actual_categories': list(account_profile['reviewCategories'])
                    }
                })
            
            # Pattern: Account is newly created and reviewing (can combine with volume)
            if (datetime.utcnow() - account_profile['creationDate']).days < NEW_ACCOUNT_AGE_DAYS_THRESHOLD:
                # This is already covered by 0.1.3's isNewAccount, but could be a more specific flag here
                flags.append({
                    'type': 'SuspiciousAccount:NewAccount',
                    'severity': 'Low',
                    'details': {
                        'accountAgeDays': (datetime.utcnow() - account_profile['creationDate']).days
                    }
                })

            # Add other account-related criteria here

        # --- IP-based Detections ---
        ip_profile = get_ip_profile(processed_review.ipAddress) # Call Account/IP Data Service
        if ip_profile:
            # Pattern: High volume of distinct accounts from a single IP
            if len(ip_profile['associatedAccountsLast24h']) > SUSPICIOUS_IP_MIN_ACCOUNTS_24H:
                flags.append({
                    'type': 'SuspiciousIP:HighAccountVolume',
                    'severity': 'High',
                    'details': {
                        'threshold': SUSPICIOUS_IP_MIN_ACCOUNTS_24H,
                        'actual_accounts_count': len(ip_profile['associatedAccountsLast24h']),
                        'accounts': list(ip_profile['associatedAccountsLast24h'])
                    }
                })

            # Pattern: IP address with a known bad reputation
            if ip_profile['reputationScore'] > SUSPICIOUS_IP_REPUTATION_THRESHOLD:
                flags.append({
                    'type': 'SuspiciousIP:BadReputation',
                    'severity': 'Critical',
                    'details': {
                        'threshold': SUSPICIOUS_IP_REPUTATION_THRESHOLD,
                        'actual_score': ip_profile['reputationScore']
                    }
                })

            # Add other IP-related criteria here

        return flags
    ```

---

#### **ARIS Sprint 1: Task 0.2.4 - Store flagged account/IP associations.** (Estimate: 10 hours)

*   **Implementation Plan:**
    *   Modify the `FlaggedReview` data model to explicitly store the `reviewerId` and `ipAddress` associated with the flagged review.
    *   Extend the storage mechanism (from 0.1.4) to ensure that when a detection for a suspicious account or IP occurs, the relevant account ID and/or IP address are stored directly as part of the `FlaggedReview` record.
    *   This will allow the Investigator Dashboard and detail view to easily retrieve and display the associated suspicious entity.
*   **Data Models and Architecture:**
    *   **Data Models:** Update `FlaggedReview` (from 0.1.4 and extending it):
        *   `flagId: string` (PK, UUID)
        *   `reviewId: string` (FK to `RawReview` and `ProcessedReview`)
        *   `reviewerId: string` (Always stored for context)
        *   `productId: string`
        *   `ipAddress: string` (Always stored for context)
        *   `flaggedDate: datetime`
        *   `abuseType: string` (e.g., "Pattern: High Volume Reviewer", "Suspicious Account: High Volume", "Suspicious IP: Bad Reputation")
        *   `severity: string`
        *   `status: string`
        *   `detectionDetails: json` (Contains specific details of the detection)
        *   `associatedSuspiciousAccountId: string` (Optional, directly points to the `reviewerId` if it was flagged as suspicious)
        *   `associatedSuspiciousIpAddress: string` (Optional, directly points to the `ipAddress` if it was flagged as suspicious)
    *   **Architecture:**
        *   `SuspiciousDetectionService` (and `PatternDetectionService`) -> Flagged Reviews Database (DynamoDB/PostgreSQL).
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** Storing direct references within the `FlaggedReview` record is sufficient for initial investigation and dashboard display.
    *   **Technical Decision:** Continue using DynamoDB due to its flexible schema, allowing for the addition of optional attributes like `associatedSuspiciousAccountId` and `associatedSuspiciousIpAddress` without requiring schema migrations.
    *   **Technical Decision:** Ensure efficient indexing on `reviewerId` and `ipAddress` in the `FlaggedReview` table to support lookups and filtering by investigators.
*   **Code Snippets/Pseudocode:**
    ```python
    import uuid
    from datetime import datetime

    # Pseudocode for storing detection results including account/IP associations
    def store_flagged_review_with_all_associations(review_id, reviewer_id, product_id, ip_address, detection_flags):
        for flag in detection_flags:
            flagged_review_record = {
                'flagId': str(uuid.uuid4()),
                'reviewId': review_id,
                'reviewerId': reviewer_id,
                'productId': product_id,
                'ipAddress': ip_address, # Storing IP directly for easier access
                'flaggedDate': datetime.utcnow().isoformat(),
                'abuseType': flag['type'],
                'severity': flag['severity'],
                'status': 'Pending',
                'detectionDetails': flag['details']
            }

            # Explicitly associate the account/IP if the flag is related to them
            if 'SuspiciousAccount' in flag['type']:
                flagged_review_record['associatedSuspiciousAccountId'] = reviewer_id
            if 'SuspiciousIP' in flag['type']:
                flagged_review_record['associatedSuspiciousIpAddress'] = ip_address

            # Save this record to your FlaggedReviews database (e.g., DynamoDB)
            save_to_flagged_reviews_db(flagged_review_record)
            print(f"Stored flag for review {review_id}: {flagged_review_record['abuseType']} (Account: {reviewer_id}, IP: {ip_address})")

    # Example usage (assuming processed_review has all necessary fields):
    # flags_detected = detect_suspicious_account_ip_patterns(example_processed_review)
    # store_flagged_review_with_all_associations(
    #    example_processed_review.reviewId, 
    #    example_processed_review.reviewerId, 
    #    example_processed_review.productId, 
    #    example_processed_review.ipAddress, 
    #    flags_detected
    # )
    ```