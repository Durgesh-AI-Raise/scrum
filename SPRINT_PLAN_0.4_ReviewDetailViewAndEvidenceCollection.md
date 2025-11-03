### User Story 0.4: Review Detail View & Evidence Collection

**Sprint Goal Alignment:** This user story directly contributes to the sprint goal by providing investigators with a detailed view of flagged reviews and associated evidence, enabling efficient triage and investigation.

---

#### **ARIS Sprint 1: Task 0.4.1 - Design UI for single review detail view.** (Estimate: 8 hours)

*   **Implementation Plan:**
    *   Create wireframes or mockups for a dedicated "Review Detail View" screen.
    *   This view should display all available information for a flagged review, including:
        *   Core review content (reviewer, product, seller, rating, text, date, IP).
        *   All associated `DetectionResult` details (abuse type, severity, detection-specific metadata).
        *   Links to reviewer and product pages (if applicable).
    *   Ensure the layout is clear, concise, and allows investigators to quickly grasp the context of the flagged review.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The detail view will be accessible by clicking on a flagged review in the Investigator Dashboard.
    *   **Technical Decision:** Prioritize presenting all collected evidence clearly. Use a collapsible or tabbed layout if the amount of detail becomes overwhelming.
*   **Code Snippets/Pseudocode:** N/A for a UI design task.

---

#### **ARIS Sprint 1: Task 0.4.2 - Extend backend API for full review details.** (Estimate: 18 hours)

*   **Implementation Plan:**
    *   Extend the backend API (developed in 0.3.2) with a new endpoint to fetch full details for a *single* flagged review, identified by its `flagId` or `reviewId`.
    *   This endpoint will:
        *   Query the `FlaggedReview` table using the provided ID.
        *   Retrieve the original `RawReview` and `ProcessedReview` data (if stored separately, or combine if `FlaggedReview` contains comprehensive data).
        *   Aggregates all associated detection results and any relevant `AccountProfile` or `IpAddressProfile` data (from 0.2.2).
        *   Present a comprehensive JSON object containing all details required by the frontend detail view.
    *   Implement robust error handling for cases where a `flagId` or `reviewId` is not found.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `FullReviewDetails` (API Response Model - comprehensive):
            *   `flagId: string`
            *   `reviewId: string`
            *   `reviewerId: string`
            *   `productId: string`
            *   `sellerId: string`
            *   `rating: int`
            *   `reviewText: string`
            *   `reviewDate: datetime`
            *   `ipAddress: string`
            *   `accountCreationDate: datetime`
            *   `isNewAccount: boolean`
            *   `abuseFlags: array<object>` (Each object representing a `DetectionResult` from 0.1.3/0.2.3, including `type`, `severity`, `details`)
            *   `reviewerProfileSummary: object` (e.g., `totalReviews`, `last24hReviews`, `reviewCategories`)
            *   `ipProfileSummary: object` (e.g., `reputationScore`, `associatedAccountsLast24h`)
            *   `status: string` (of the flag)
            *   `flaggedDate: datetime`
    *   **Architecture:** Backend Service (AWS Lambda/Flask/FastAPI) -> Flagged Reviews Database, Raw Review Data Store (S3/DynamoDB), Account/IP Data Service.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The `FlaggedReview` table contains foreign keys or direct references to original review data (or that original review data can be efficiently joined/fetched).
    *   **Technical Decision:** The backend service will orchestrate calls to different data sources (FlaggedReview DB, potentially Raw Review DB/S3, Account/IP Data Service) to build the `FullReviewDetails` object.
    *   **Technical Decision:** Optimize data retrieval by using appropriate database indexes and potentially caching frequently accessed `AccountProfile` and `IpAddressProfile` data.
*   **Code Snippets/Pseudocode:**
    ```python
    from flask import Flask, request, jsonify
    from datetime import datetime

    app = Flask(__name__)

    # Mock database and service calls
    def get_flagged_review_from_db(flag_id):
        # In real-world: query DynamoDB/PostgreSQL for FlaggedReview by flagId
        mock_flagged_reviews = {
            'flag-123': {
                'flagId': 'flag-123', 'reviewId': 'rev-001', 'reviewerId': 'usr-abc', 'productId': 'prod-xyz',
                'abuseType': 'Pattern: HighVolumeReviewer', 'severity': 'High', 'flaggedDate': '2023-10-26T10:00:00Z', 'status': 'Pending',
                'detectionDetails': {'threshold': 5, 'actual_count': 7}, 'ipAddress': '192.168.1.1',
                'associatedSuspiciousAccountId': 'usr-abc'
            },
            'flag-124': {
                'flagId': 'flag-124', 'reviewId': 'rev-002', 'reviewerId': 'usr-def', 'productId': 'prod-uvw',
                'abuseType': 'SuspiciousIP:BadReputation', 'severity': 'Critical', 'flaggedDate': '2023-10-26T11:30:00Z', 'status': 'Pending',
                'detectionDetails': {'threshold': 0.7, 'actual_score': 0.85}, 'ipAddress': '10.0.0.5',
                'associatedSuspiciousIpAddress': '10.0.0.5'
            },
        }
        return mock_flagged_reviews.get(flag_id)

    def get_raw_review_from_db(review_id):
        # In real-world: query RawReview storage (e.g., S3, DynamoDB)
        mock_raw_reviews = {
            'rev-001': {
                'reviewId': 'rev-001', 'reviewerId': 'usr-abc', 'productId': 'prod-xyz', 'sellerId': 'slr-1',
                'rating': 1, 'reviewText': 'This product is terrible, worst ever.', 'reviewDate': '2023-10-26T09:55:00Z', 'ipAddress': '192.168.1.1'
            },
            'rev-002': {
                'reviewId': 'rev-002', 'reviewerId': 'usr-def', 'productId': 'prod-uvw', 'sellerId': 'slr-2',
                'rating': 5, 'reviewText': 'Amazing product, highly recommend!', 'reviewDate': '2023-10-26T11:25:00Z', 'ipAddress': '10.0.0.5'
            },
        }
        return mock_raw_reviews.get(review_id)

    def get_processed_review_from_db(review_id):
        # In real-world: query ProcessedReview storage (e.g., DynamoDB)
        mock_processed_reviews = {
            'rev-001': {
                'reviewId': 'rev-001', 'reviewerId': 'usr-abc', 'productId': 'prod-xyz', 'rating': 1,
                'reviewDate': '2023-10-26T09:55:00Z', 'ipAddress': '192.168.1.1',
                'accountCreationDate': '2023-10-20T00:00:00Z', 'isNewAccount': True,
                'reviewerReviewCountLast24h': 7, 'productReviewCountLast24h': 12
            },
            'rev-002': {
                'reviewId': 'rev-002', 'reviewerId': 'usr-def', 'productId': 'prod-uvw', 'rating': 5,
                'reviewDate': '2023-10-26T11:25:00Z', 'ipAddress': '10.0.0.5',
                'accountCreationDate': '2022-05-01T00:00:00Z', 'isNewAccount': False,
                'reviewerReviewCountLast24h': 2, 'productReviewCountLast24h': 8
            },
        }
        return mock_processed_reviews.get(review_id)
    
    # Mock Account/IP Data Service (from 0.2.2)
    def get_account_profile_mock(account_id):
        if account_id == 'usr-abc':
            return {
                'accountId': 'usr-abc', 'creationDate': datetime.fromisoformat('2023-10-20T00:00:00Z'),
                'status': 'active', 'totalReviews': 15, 'last24hReviews': 7, 'reviewCategories': ['Electronics', 'Home']
            }
        return None

    def get_ip_profile_mock(ip_address):
        if ip_address == '10.0.0.5':
            return {
                'ipAddress': '10.0.0.5', 'lastSeen': datetime.utcnow(), 'reputationScore': 0.85,
                'associatedAccountsLast24h': {'acc_x', 'acc_y', 'acc_z'}
            }
        return None

    @app.route('/api/flagged-reviews/<string:flag_id>', methods=['GET'])
    def get_single_flagged_review_details(flag_id):
        flagged_review = get_flagged_review_from_db(flag_id)
        if not flagged_review:
            return jsonify({'message': 'Flagged review not found'}), 404

        review_id = flagged_review['reviewId']
        raw_review = get_raw_review_from_db(review_id)
        processed_review = get_processed_review_from_db(review_id)

        if not raw_review or not processed_review:
            # Handle cases where core review data might be missing (shouldn't happen if pipelines are robust)
            return jsonify({'message': 'Associated review data incomplete'}), 500

        reviewer_profile_summary = get_account_profile_mock(flagged_review['reviewerId'])
        ip_profile_summary = get_ip_profile_mock(flagged_review['ipAddress'])

        full_details = {
            'flagId': flagged_review['flagId'],
            'reviewId': raw_review['reviewId'],
            'reviewerId': raw_review['reviewerId'],
            'productId': raw_review['productId'],
            'sellerId': raw_review['sellerId'],
            'rating': raw_review['rating'],
            'reviewText': raw_review['reviewText'],
            'reviewDate': raw_review['reviewDate'],
            'ipAddress': raw_review['ipAddress'],
            'accountCreationDate': processed_review.get('accountCreationDate'),
            'isNewAccount': processed_review.get('isNewAccount'),
            'abuseFlags': [
                {'type': flagged_review['abuseType'], 'severity': flagged_review['severity'], 'details': flagged_review['detectionDetails']}
                # In a real system, there could be multiple flags per review, aggregated here
            ],
            'reviewerProfileSummary': {
                'totalReviews': reviewer_profile_summary.get('totalReviews'),
                'last24hReviews': reviewer_profile_summary.get('last24hReviews'),
                'reviewCategories': list(reviewer_profile_summary.get('reviewCategories', []))
            } if reviewer_profile_summary else None,
            'ipProfileSummary': {
                'reputationScore': ip_profile_summary.get('reputationScore'),
                'associatedAccountsLast24h': list(ip_profile_summary.get('associatedAccountsLast24h', []))
            } if ip_profile_summary else None,
            'status': flagged_review['status'],
            'flaggedDate': flagged_review['flaggedDate']
        }
        return jsonify(full_details)

    # To run this with Flask (for local testing):
    # if __name__ == '__main__':
    #    app.run(debug=True)
    ```

---

#### **ARIS Sprint 1: Task 0.4.3 - Implement frontend component for full review details.** (Estimate: 24 hours)

*   **Implementation Plan:**
    *   Develop a dedicated React component for the "Review Detail View".
    *   This component will accept a `flagId` or `reviewId` as a prop/URL parameter.
    *   It will make an API call to the new backend endpoint (0.4.2) to fetch all details for the specific review.
    *   Display the retrieved `FullReviewDetails` in a structured and readable format, including all core review information, detection reasons, and associated account/IP summaries.
    *   Include a way to navigate back to the dashboard.
*   **Data Models and Architecture:**
    *   **Data Models:** Uses `FullReviewDetails` (from 0.4.2) for displaying data.
    *   **Architecture:** Web Browser -> Frontend Application (React App) -> Backend API Gateway.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The frontend routing mechanism (e.g., React Router) will be set up to handle navigation to the detail view based on `flagId` or `reviewId`.
    *   **Technical Decision:** Continue using React for consistency with the dashboard frontend.
    *   **Technical Decision:** Utilize a responsive layout to ensure the detail view is usable across different screen sizes.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // Pseudocode for a React ReviewDetailView component
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';
    import { useParams, useNavigate } from 'react-router-dom'; // Assuming React Router for navigation

    function ReviewDetailView() {
        const { flagId } = useParams(); // Get flagId from URL parameters
        const navigate = useNavigate();
        const [reviewDetails, setReviewDetails] = useState(null);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);

        useEffect(() => {
            if (flagId) {
                fetchReviewDetails(flagId);
            }
        }, [flagId]);

        const fetchReviewDetails = async (id) => {
            setLoading(true);
            try {
                // Replace with your actual API endpoint
                const response = await axios.get(`/api/flagged-reviews/${id}`);
                setReviewDetails(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching review details:", err);
                setError('Failed to fetch review details.');
                setLoading(false);
            }
        };

        if (loading) return <div>Loading review details...</div>;
        if (error) return <div>Error: {error}</div>;
        if (!reviewDetails) return <div>Review not found.</div>;

        return (
            <div className="review-detail-view">
                <h2>Review Details for Flag ID: {reviewDetails.flagId}</h2>
                <button onClick={() => navigate('/dashboard')}>Back to Dashboard</button>

                <div className="review-core-info">
                    <h3>Core Review Information</h3>
                    <p><strong>Review ID:</strong> {reviewDetails.reviewId}</p>
                    <p><strong>Reviewer ID:</strong> {reviewDetails.reviewerId}</p>
                    <p><strong>Product ID:</strong> {reviewDetails.productId}</p>
                    <p><strong>Seller ID:</strong> {reviewDetails.sellerId}</p>
                    <p><strong>Rating:</strong> {reviewDetails.rating}/5</p>
                    <p><strong>Review Text:</strong> {reviewDetails.reviewText}</p>
                    <p><strong>Review Date:</strong> {new Date(reviewDetails.reviewDate).toLocaleString()}</p>
                    <p><strong>IP Address:</strong> {reviewDetails.ipAddress}</p>
                </div>

                <div className="detection-info">
                    <h3>Detection Information</h3>
                    <p><strong>Flag Status:</strong> {reviewDetails.status}</p>
                    <p><strong>Flagged Date:</strong> {new Date(reviewDetails.flaggedDate).toLocaleString()}</p>
                    {reviewDetails.abuseFlags && reviewDetails.abuseFlags.map((flag, index) => (
                        <div key={index} className="abuse-flag-item">
                            <h4>Abuse Type: {flag.type}</h4>
                            <p><strong>Severity:</strong> {flag.severity}</p>
                            <p><strong>Details:</strong> {JSON.stringify(flag.details, null, 2)}</p>
                        </div>
                    ))}
                </div>

                <div className="reviewer-info">
                    <h3>Reviewer & Account Information</h3>
                    <p><strong>Account Creation Date:</strong> {reviewDetails.accountCreationDate ? new Date(reviewDetails.accountCreationDate).toLocaleDateString() : 'N/A'}</p>
                    <p><strong>New Account:</strong> {reviewDetails.isNewAccount ? 'Yes' : 'No'}</p>
                    {reviewDetails.reviewerProfileSummary && (
                        <div>
                            <p><strong>Total Reviews by Reviewer:</strong> {reviewDetails.reviewerProfileSummary.totalReviews}</p>
                            <p><strong>Reviews in Last 24h:</strong> {reviewDetails.reviewerProfileSummary.last24hReviews}</p>
                            <p><strong>Review Categories:</strong> {reviewDetails.reviewerProfileSummary.reviewCategories.join(', ')}</p>
                        </div>
                    )}
                </div>

                <div className="ip-info">
                    <h3>IP Address Information</h3>
                    {reviewDetails.ipProfileSummary && (
                        <div>
                            <p><strong>IP Reputation Score:</strong> {reviewDetails.ipProfileSummary.reputationScore}</p>
                            <p><strong>Associated Accounts (Last 24h):</strong> {reviewDetails.ipProfileSummary.associatedAccountsLast24h.join(', ')}</p>
                        </div>
                    )}
                </div>

                {/* Add more sections for evidence collection, actions etc. */}
            </div>
        );
    }

    export default ReviewDetailView;
    ```