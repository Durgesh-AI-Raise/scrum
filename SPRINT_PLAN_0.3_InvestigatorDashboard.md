### User Story 0.3: Investigator Dashboard

**Sprint Goal Alignment:** This user story directly contributes to the sprint goal by providing investigators with a basic dashboard to view and understand flagged reviews.

---

#### **ARIS Sprint 1: Task 0.3.1 - Design basic dashboard UI layout.** (Estimate: 10 hours)

*   **Implementation Plan:**
    *   Create wireframes or mockups for the dashboard. This will involve defining the key sections: a list of flagged reviews, filtering options (by abuse type, severity, date), and a summary of flagged reviews.
    *   Focus on a clean and intuitive layout that prioritizes crucial information for investigators.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The dashboard will initially be a web-based application.
    *   **Technical Decision:** For the MVP, a simple, responsive design focusing on functionality over elaborate aesthetics will be prioritized. Tools like Figma or Balsamiq can be used for mockups.
*   **Code Snippets/Pseudocode:** N/A for a UI design task.

---

#### **ARIS Sprint 1: Task 0.3.2 - Develop backend API to fetch flagged reviews.** (Estimate: 16 hours)

*   **Implementation Plan:**
    *   Develop a RESTful API endpoint that allows the dashboard frontend to retrieve flagged reviews.
    *   The API should support filtering by `abuseType`, `severity`, and `dateRange`, and pagination for efficient data loading.
    *   It will query the `FlaggedReview` database table (from Task 0.1.4 and 0.2.4).
    *   Implement input validation and error handling for robust API operation.
*   **Data Models and Architecture:**
    *   **Data Models:**
        *   `FlaggedReview` (as defined in 0.1.4 and 0.2.4).
        *   `DashboardReviewSummary` (API Response Model - subset of `FlaggedReview` fields):
            *   `flagId: string`
            *   `reviewId: string`
            *   `reviewerId: string`
            *   `productId: string`
            *   `abuseType: string`
            *   `severity: string`
            *   `flaggedDate: datetime`
            *   `status: string`
    *   **Architecture:**
        *   API Gateway (e.g., AWS API Gateway) -> Backend Service (e.g., AWS Lambda with Python/Flask or FastAPI) -> Flagged Reviews Database (DynamoDB/PostgreSQL).
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The `FlaggedReview` table will be sufficiently indexed to support efficient queries for the dashboard.
    *   **Technical Decision:** Use Python with Flask or FastAPI for the backend API for rapid development and maintainability, leveraging AWS Lambda for serverless deployment.
    *   **Technical Decision:** Initially, simple string matching for `abuseType` and `severity` filters, and range queries for `dateRange`.
*   **Code Snippets/Pseudocode:**
    ```python
    from flask import Flask, request, jsonify
    from datetime import datetime, timedelta

    app = Flask(__name__)

    # Mock database interaction for FlaggedReview
    # In a real scenario, this would interact with DynamoDB or PostgreSQL
    def get_flagged_reviews_from_db(filters, pagination):
        all_flagged_reviews = [
            {
                'flagId': 'flag-123', 'reviewId': 'rev-001', 'reviewerId': 'usr-abc', 'productId': 'prod-xyz',
                'abuseType': 'Pattern: HighVolumeReviewer', 'severity': 'High', 'flaggedDate': '2023-10-26T10:00:00Z', 'status': 'Pending',
                'detectionDetails': {'threshold': 5, 'actual_count': 7}, 'ipAddress': '192.168.1.1'
            },
            {
                'flagId': 'flag-124', 'reviewId': 'rev-002', 'reviewerId': 'usr-def', 'productId': 'prod-uvw',
                'abuseType': 'SuspiciousIP:BadReputation', 'severity': 'Critical', 'flaggedDate': '2023-10-26T11:30:00Z', 'status': 'Pending',
                'detectionDetails': {'threshold': 0.7, 'actual_score': 0.85}, 'ipAddress': '10.0.0.5'
            },
            {
                'flagId': 'flag-125', 'reviewId': 'rev-003', 'reviewerId': 'usr-ghi', 'productId': 'prod-lmn',
                'abuseType': 'Pattern: NewAccountReview', 'severity': 'Medium', 'flaggedDate': '2023-10-25T14:00:00Z', 'status': 'Pending',
                'detectionDetails': {'accountAgeThresholdDays': 30, 'accountAgeDays': 5}, 'ipAddress': '172.16.0.10'
            }
        ]

        filtered_reviews = []
        for review in all_flagged_reviews:
            match = True
            if 'abuseType' in filters and filters['abuseType'].lower() not in review['abuseType'].lower():
                match = False
            if 'severity' in filters and filters['severity'].lower() != review['severity'].lower():
                match = False
            # Convert review flaggedDate to datetime for comparison
            review_date = datetime.fromisoformat(review['flaggedDate'].replace('Z', '+00:00'))
            if 'startDate' in filters and review_date < filters['startDate']:
                match = False
            if 'endDate' in filters and review_date > filters['endDate']:
                match = False
            
            if match:
                filtered_reviews.append(review)
        
        # Simple pagination
        start_index = (pagination['page'] - 1) * pagination['pageSize']
        end_index = start_index + pagination['pageSize']
        paginated_reviews = filtered_reviews[start_index:end_index]

        return paginated_reviews, len(filtered_reviews)

    @app.route('/api/flagged-reviews', methods=['GET'])
    def get_flagged_reviews():
        abuse_type = request.args.get('abuseType')
        severity = request.args.get('severity')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))

        filters = {}
        if abuse_type:
            filters['abuseType'] = abuse_type
        if severity:
            filters['severity'] = severity
        if start_date_str:
            filters['startDate'] = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            filters['endDate'] = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

        pagination = {'page': page, 'pageSize': page_size}

        reviews, total_count = get_flagged_reviews_from_db(filters, pagination)

        response_reviews = []
        for review in reviews:
            response_reviews.append({
                'flagId': review['flagId'],
                'reviewId': review['reviewId'],
                'reviewerId': review['reviewerId'],
                'productId': review['productId'],
                'abuseType': review['abuseType'],
                'severity': review['severity'],
                'flaggedDate': review['flaggedDate'],
                'status': review['status']
            })

        return jsonify({
            'data': response_reviews,
            'totalCount': total_count,
            'page': page,
            'pageSize': page_size
        })

    # To run this with Flask (for local testing):
    # if __name__ == '__main__':
    #    app.run(debug=True)
    ```

---

#### **ARIS Sprint 1: Task 0.3.3 - Implement frontend component for flagged reviews list.** (Estimate: 20 hours)

*   **Implementation Plan:**
    *   Develop a frontend component (e.g., using React) that displays a list of flagged reviews.
    *   This component will consume data from the backend API (0.3.2).
    *   It will feature a table-like view with columns for `reviewId`, `abuseType`, `severity`, `flaggedDate`, and `status`.
    *   Implement basic pagination controls and client-side filtering options (that interact with the backend API).
    *   Ensure the UI is user-friendly and clearly presents the information.
*   **Data Models and Architecture:**
    *   **Data Models:** Uses `DashboardReviewSummary` (from 0.3.2) for displaying data.
    *   **Architecture:** Web Browser -> Frontend Application (e.g., React App hosted on AWS S3/CloudFront) -> Backend API Gateway.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A modern JavaScript framework (React, Vue, or Angular) will be used for rapid frontend development. React is chosen for this plan.
    *   **Technical Decision:** React will be used for the frontend component due to its component-based architecture and widespread adoption.
    *   **Technical Decision:** A simple UI library (e.g., Material-UI, Ant Design, or Tailwind CSS) will be considered to accelerate development of consistent UI elements.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // Pseudocode for a React FlaggedReviewsList component
    import React, { useState, useEffect } from 'react';
    import axios from 'axios'; // For API calls, install via npm/yarn install axios

    function FlaggedReviewsList() {
        const [flaggedReviews, setFlaggedReviews] = useState([]);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);
        const [page, setPage] = useState(1);
        const [pageSize, setPageSize] = useState(10);
        const [totalCount, setTotalCount] = useState(0);
        const [filters, setFilters] = useState({
            abuseType: '',
            severity: '',
            startDate: '',
            endDate: ''
        });

        useEffect(() => {
            fetchFlaggedReviews();
        }, [page, pageSize, filters]); // Re-fetch when page, page size, or filters change

        const fetchFlaggedReviews = async () => {
            setLoading(true);
            try {
                const params = {
                    page: page,
                    pageSize: pageSize,
                    ...filters
                };
                // Replace with your actual API endpoint
                const response = await axios.get('/api/flagged-reviews', { params });
                setFlaggedReviews(response.data.data);
                setTotalCount(response.data.totalCount);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching flagged reviews:", err);
                setError('Failed to fetch flagged reviews.');
                setLoading(false);
            }
        };

        const handleFilterChange = (e) => {
            setFilters({ ...filters, [e.target.name]: e.target.value });
            setPage(1); // Reset to first page on filter change
        };

        const handlePageChange = (newPage) => {
            if (newPage > 0 && newPage <= Math.ceil(totalCount / pageSize)) {
                setPage(newPage);
            }
        };

        if (loading) return <div>Loading flagged reviews...</div>;
        if (error) return <div>Error: {error}</div>;

        return (
            <div className="flagged-reviews-dashboard">
                <h2>Flagged Reviews Dashboard</h2>

                <div className="filters">
                    <label>
                        Abuse Type:
                        <input type="text" name="abuseType" value={filters.abuseType} onChange={handleFilterChange} placeholder="e.g., HighVolumeReviewer"/>
                    </label>
                    <label>
                        Severity:
                        <select name="severity" value={filters.severity} onChange={handleFilterChange}>
                            <option value="">All</option>
                            <option value="High">High</option>
                            <option value="Medium">Medium</option>
                            <option value="Low">Low</option>
                            <option value="Critical">Critical</option>
                        </select>
                    </label>
                    <label>
                        Start Date:
                        <input type="date" name="startDate" value={filters.startDate} onChange={handleFilterChange} />
                    </label>
                    <label>
                        End Date:
                        <input type="date" name="endDate" value={filters.endDate} onChange={handleFilterChange} />
                    </label>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Review ID</th>
                            <th>Abuse Type</th>
                            <th>Severity</th>
                            <th>Flagged Date</th>
                            <th>Status</th>
                            {/* Add more columns as needed, e.g., Actions */}
                        </tr>
                    </thead>
                    <tbody>
                        {flaggedReviews.length > 0 ? (
                            flaggedReviews.map((review) => (
                                <tr key={review.flagId}>
                                    <td>{review.reviewId}</td>
                                    <td>{review.abuseType}</td>
                                    <td>{review.severity}</td>
                                    <td>{new Date(review.flaggedDate).toLocaleDateString()}</td>
                                    <td>{review.status}</td>
                                </tr>
                            ))
                        ) : (
                            <tr><td colSpan="5">No flagged reviews found.</td></tr>
                        )}
                    </tbody>
                </table>

                <div className="pagination">
                    <button onClick={() => handlePageChange(page - 1)} disabled={page === 1}>Previous</button>
                    <span>Page {page} of {Math.ceil(totalCount / pageSize)}</span>
                    <button onClick={() => handlePageChange(page + 1)} disabled={page * pageSize >= totalCount}>Next</button>
                </div>
            </div>
        );
    }

    export default FlaggedReviewsList;
    ```

---

#### **ARIS Sprint 1: Task 0.3.4 - Add basic categorization to dashboard.** (Estimate: 12 hours)

*   **Implementation Plan:**
    *   Enhance the frontend (0.3.3) to display a summary or count of flagged reviews categorized by `abuseType` and `severity`.
    *   This could be a small widget or section on the dashboard showing "Total High Severity Flags," "New Account Flags," etc.
    *   The backend API (0.3.2) will need a new endpoint or modifications to provide these aggregate counts efficiently.
*   **Data Models and Architecture:**
    *   **Data Models:** A new API response model for summary statistics:
        *   `DashboardSummaryStats`:
            *   `totalFlaggedReviews: int`
            *   `countsByAbuseType: { [key: string]: int }`
            *   `countsBySeverity: { [key: string]: int }`
    *   **Architecture:** Backend API (modified or new endpoint for summary) -> Frontend Application.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The aggregation for categorization can be done efficiently at the database level or through cached results for performance.
    *   **Technical Decision:** The initial categorization will be simple counts, avoiding complex real-time analytics for the MVP. Aggregations will be performed on the `FlaggedReview` table.
    *   **Technical Decision:** The backend API will be extended to provide these summary statistics, reducing the need for the frontend to perform complex aggregations.
*   **Code Snippets/Pseudocode:**
    ```python
    # Pseudocode for extending backend API for categorization
    # This would typically be a separate endpoint or part of the main API response
    @app.route('/api/flagged-reviews/summary', methods=['GET'])
    def get_flagged_reviews_summary():
        # In a real scenario, this would query the database for aggregate counts
        # Example: Query FlaggedReview table, group by abuseType and severity, and count
        
        # Mock summary data for illustration
        mock_summary_data = {
            'totalFlaggedReviews': 3,
            'countsByAbuseType': {
                'Pattern: HighVolumeReviewer': 1,
                'SuspiciousIP:BadReputation': 1,
                'Pattern: NewAccountReview': 1
            },
            'countsBySeverity': {
                'High': 1,
                'Critical': 1,
                'Medium': 1
            }
        }
        return jsonify(mock_summary_data)

    # Pseudocode for a React component to display summary
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';

    function DashboardSummary() {
        const [summary, setSummary] = useState(null);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);

        useEffect(() => {
            fetchSummary();
        }, []);

        const fetchSummary = async () => {
            setLoading(true);
            try {
                // Replace with your actual API endpoint
                const response = await axios.get('/api/flagged-reviews/summary');
                setSummary(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching dashboard summary:", err);
                setError('Failed to fetch dashboard summary.');
                setLoading(false);
            }
        };

        if (loading) return <div>Loading summary...</div>;
        if (error) return <div>Error: {error}</div>;
        if (!summary) return null;

        return (
            <div className="dashboard-summary">
                <h3>Dashboard Summary</h3>
                <p>Total Flagged Reviews: {summary.totalFlaggedReviews}</p>
                <div>
                    <h4>By Abuse Type:</h4>
                    <ul>
                        {Object.entries(summary.countsByAbuseType).map(([type, count]) => (
                            <li key={type}>{type}: {count}</li>
                        ))}
                    </ul>
                </div>
                <div>
                    <h4>By Severity:</h4>
                    <ul>
                        {Object.entries(summary.countsBySeverity).map(([severity, count]) => (
                            <li key={severity}>{severity}: {count}</li>
                        ))}
                    </ul>
                </div>
            </div>
        );
    }

    export default DashboardSummary;
    ```