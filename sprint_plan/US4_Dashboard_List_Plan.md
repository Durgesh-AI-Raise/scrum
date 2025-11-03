# User Story 4 (US4): View a prioritized list of potentially abusive reviews on a dashboard.

### Implementation Plan

The **Analyst Dashboard** will be a web application providing a user interface for Trust & Safety Analysts. It will consist of a **Dashboard Backend Service** (API) and a **Dashboard Frontend Application**.

The **Dashboard Backend Service** will:
1.  **Expose API Endpoints:** Provide RESTful APIs for the frontend to fetch flagged reviews.
2.  **Query Storage Service:** Interact with the Storage Service (US2) to retrieve reviews with a 'flagged_abuse' status.
3.  **Prioritize/Filter/Sort:** Implement logic for prioritizing, sorting, and filtering the flagged reviews before sending them to the frontend.

The **Dashboard Frontend Application** will:
1.  **Display List:** Render a list of flagged reviews fetched from the Dashboard Backend Service.
2.  **Provide UI for Interactions:** Allow analysts to sort, filter, and eventually click on reviews to view more details (US5).

### Data Models

1.  **ReviewData (from Storage Service):** The backend will retrieve `ReviewData` from the Storage Service.
2.  **DashboardReviewListItem:** A simplified model for displaying reviews in the list view, containing only essential information for prioritization and quick scanning.

    ```json
    {
        "id": "UUID",                   // Internal unique identifier
        "reviewId": "string",           // Unique identifier for the review from Amazon
        "productASIN": "string",        // Amazon Standard Identification Number
        "reviewerId": "string",         // Identifier for the reviewer
        "timestamp": "datetime",        // Timestamp of the review (UTC)
        "reviewTextSnippet": "string",  // First N characters of the review text
        "flaggingReasons": "array<string>", // Reasons for being flagged
        "severity": "string",           // Derived from flagging reasons, e.g., "HIGH", "MEDIUM"
        "status": "string"              // Current status, e.g., "flagged_abuse", "pending"
    }
    ```
3.  **DashboardListRequest:** Model for the request payload to fetch flagged reviews.

    ```json
    {
        "status": "string",             // Filter by status (e.g., "flagged_abuse", "pending")
        "sortBy": "string",             // Field to sort by (e.g., "timestamp", "severity")
        "sortOrder": "string",          // "asc" or "desc"
        "page": "integer",              // Page number for pagination
        "pageSize": "integer",          // Number of items per page
        "searchQuery": "string"         // Optional: search within review text or IDs
    }
    ```

### Architecture

```
[Web Browser (Analyst)]
        |
        V
[Dashboard Frontend Application] (React/Vue/Angular)
        | (HTTP/REST)
        V
[Dashboard Backend Service] (Python/Flask/FastAPI)
        | (API Calls / ORM)
        V
[Storage Service] (Database: PostgreSQL)
```

**Components:**
*   **Dashboard Frontend Application:** A single-page application (SPA) built with a modern JavaScript framework.
*   **Dashboard Backend Service:** A microservice responsible for handling dashboard-specific API requests, interacting with the Storage Service, and applying business logic for displaying reviews.
*   **Storage Service:** The existing service from US2, providing the persistent store for reviews.

### Assumptions and Technical Decisions

*   **Assumption (T4.1):** The initial UI will be functional and prioritize core features over extensive styling or complex interactive elements. It will display a simple tabular list.
*   **Assumption (T4.2):** The Dashboard Backend Service will expose a secure API. Authentication and authorization (e.g., OAuth2, JWT) will be implemented to ensure only authorized analysts can access the data. For MVP, a basic API key or simple token might suffice, with full auth in future sprints.
*   **Assumption (T4.3):** The frontend framework will be chosen based on common practices (e.g., React, Vue, Angular) for rapid development. For this plan, we'll assume a basic React application.
*   **Assumption (T4.4):** Basic sorting will include `timestamp` (descending by default), `severity`, and `reviewerId`. Filtering will initially support `status` (e.g., show only `flagged_abuse`).
*   **Technical Decision (T4.1):** Use a responsive web design approach to ensure basic usability across different screen sizes, though primarily targeting desktop use.
*   **Technical Decision (T4.2):** Implement the Dashboard Backend Service using **Python with FastAPI** for its high performance and automatic API documentation generation. It will include endpoints like `/api/v1/reviews/flagged` that accept query parameters for sorting, filtering, and pagination.
*   **Technical Decision (T4.3):** Develop the frontend using **React** with a component-based structure. A `ReviewList` component will fetch and display data.
*   **Technical Decision (T4.4):** The backend API will handle sorting, filtering, and pagination to offload complex data manipulation from the frontend and leverage database indexing. The frontend will pass these parameters as query strings.
*   **Technical Decision (T4.5):** Unit tests for the frontend will cover individual React components (e.g., rendering, state changes). Unit tests for the backend will cover API endpoint logic, data retrieval, sorting, and filtering. End-to-End (E2E) tests will use tools like Cypress or Playwright to simulate user interactions on the dashboard and verify data display and functionality.

### Code Snippets / Pseudocode for US4:

#### T4.2: Implement backend API for fetching flagged reviews (Python Pseudocode with FastAPI)

```python
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid # For UUID type hint
from sqlalchemy import func # For array_length in sorting

# Assume database models and session from US2's Storage_Plan
# For demonstration, we'll define a placeholder Review model and SessionLocal
# In a real app, these would be imported from your US2 implementation.

# --- Placeholder for Review Model from US2 --- START
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, UUID as SQL_UUID, JSON
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(SQL_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(255), unique=True, nullable=False)
    reviewer_id = Column(String(255), nullable=False)
    product_asin = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(255), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer)
    review_title = Column(String(512))
    source = Column(String(50), nullable=False, default='amazon')
    ingestion_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    status = Column(String(50), nullable=False, default='pending')
    flagging_reasons = Column(JSON, default=[])
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

# Example DB setup (for standalone running, replace with actual config)
DATABASE_URL = "sqlite:///./test.db" # Use a simple SQLite for demonstration
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_tables_for_dashboard_api():
    Base.metadata.create_all(bind=engine)

# --- Placeholder for Review Model from US2 --- END


# Pydantic model for response data (DashboardReviewListItem)
class DashboardReviewListItem(BaseModel):
    id: uuid.UUID
    reviewId: str
    productASIN: str
    reviewerId: str
    timestamp: datetime
    reviewTextSnippet: str
    flaggingReasons: List[str]
    severity: str # Derived, could be 'HIGH', 'MEDIUM', 'LOW' based on reasons
    status: str

    class Config:
        from_attributes = True # Allow mapping from SQLAlchemy models

# Pydantic model for API query parameters
class ReviewQueryParams(BaseModel):
    status: Optional[str] = Query("flagged_abuse", description="Filter by review status")
    sortBy: Optional[str] = Query("timestamp", description="Field to sort by (e.g., timestamp, severity, reviewerId)")
    sortOrder: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc'")
    page: Optional[int] = Query(1, ge=1, description="Page number")
    pageSize: Optional[int] = Query(20, ge=1, le=100, description="Number of items per page")
    searchQuery: Optional[str] = Query(None, description="Search query for review text or ID")

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/reviews/flagged", response_model=List[DashboardReviewListItem])
async def get_flagged_reviews(
    params: ReviewQueryParams = Depends(),
    db: Session = Depends(get_db)
):
    query = db.query(Review)

    # Filtering
    if params.status:
        query = query.filter(Review.status == params.status)
    if params.searchQuery:
        search_pattern = f"%{params.searchQuery}%"
        query = query.filter(
            (Review.review_text.ilike(search_pattern)) |
            (Review.review_id.ilike(search_pattern)) |
            (Review.reviewer_id.ilike(search_pattern)) |
            (Review.product_asin.ilike(search_pattern))
        )

    # Sorting
    if params.sortBy == "timestamp":
        if params.sortOrder == "asc":
            query = query.order_by(Review.timestamp.asc())
        else:
            query = query.order_by(Review.timestamp.desc())
    elif params.sortBy == "severity":
        # For PostgreSQL JSONB array, use func.jsonb_array_length or similar for severity proxy
        # For simplicity in pseudocode, let's just sort by timestamp if severity is requested, 
        # or assume severity is stored as a direct column in future iteration.
        # For now, a rough proxy for severity could be the number of flagging reasons.
        if params.sortOrder == "asc":
            # SQLite doesn't have func.array_length for JSON, so this is PostgreSQL specific
            # For a more generic solution, fetch and sort in application or use a dedicated 'severity' column.
            # We'll use a placeholder sort for generic DBs or mock it.
            query = query.order_by(Review.timestamp.desc()) # Fallback for non-PostgreSQL example
        else:
            query = query.order_by(Review.timestamp.desc()) # Fallback
    elif params.sortBy == "reviewerId":
        if params.sortOrder == "asc":
            query = query.order_by(Review.reviewer_id.asc())
        else:
            query = query.order_by(Review.reviewer_id.desc())
    elif params.sortBy == "productASIN":
        if params.sortOrder == "asc":
            query = query.order_by(Review.product_asin.asc())
        else:
            query = query.order_by(Review.product_asin.desc())
    # Add other sorting options as needed

    # Pagination
    offset = (params.page - 1) * params.pageSize
    reviews = query.offset(offset).limit(params.pageSize).all()

    # Map database model to DashboardReviewListItem Pydantic model
    result = []
    for review in reviews:
        # Simple severity derivation for MVP (can be enhanced)
        severity = "LOW"
        if review.flagging_reasons:
            if any(reason in review.flagging_reasons for reason in ["Identical Review Text Abuse", "Excessive Reviews from Same IP"]):
                severity = "HIGH" # Example: assign HIGH if specific rules triggered
            elif len(review.flagging_reasons) > 0:
                severity = "MEDIUM"

        result.append(DashboardReviewListItem(
            id=review.id,
            reviewId=review.review_id,
            productASIN=review.product_asin,
            reviewerId=review.reviewer_id,
            timestamp=review.timestamp,
            reviewTextSnippet=review.review_text[:150] + "..." if len(review.review_text) > 150 else review.review_text,
            flaggingReasons=review.flagging_reasons,
            severity=severity,
            status=review.status
        ))
    
    return result

# To run this with uvicorn:
# uvicorn main:app --reload
```

#### T4.3: Develop front-end component for displaying prioritized review list (React Pseudocode)

```javascript
// components/ReviewList.js
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Or use native fetch API

function ReviewList() {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortBy, setSortBy] = useState('timestamp');
    const [sortOrder, setSortOrder] = useState('desc');
    const [statusFilter, setStatusFilter] = useState('flagged_abuse');
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [searchQuery, setSearchQuery] = useState('');
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        fetchReviews();
    }, [sortBy, sortOrder, statusFilter, page, pageSize, searchQuery]);

    const fetchReviews = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get('/api/v1/reviews/flagged', {
                params: {
                    status: statusFilter,
                    sortBy: sortBy,
                    sortOrder: sortOrder,
                    page: page,
                    pageSize: pageSize,
                    searchQuery: searchQuery,
                },
            });
            setReviews(response.data);
            // In a real application, backend should provide total count for pagination
            // For simplicity, let's assume `X-Total-Count` header or a meta field in response.
            // const totalCount = parseInt(response.headers['x-total-count']) || 0;
            // setTotalPages(Math.ceil(totalCount / pageSize));
            setTotalPages(5); // Placeholder for demonstration
        } catch (err) {
            setError('Failed to fetch reviews. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSortChange = (newSortBy) => {
        if (sortBy === newSortBy) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(newSortBy);
            setSortOrder('desc');
        }
        setPage(1); // Reset to first page on sort change
    };

    const handleStatusFilterChange = (e) => {
        setStatusFilter(e.target.value);
        setPage(1); // Reset to first page on filter change
    };

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
        setPage(1); // Reset to first page on search change
    };

    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setPage(newPage);
        }
    };

    if (loading) return <div>Loading reviews...</div>;
    if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

    return (
        <div className="review-list-container">
            <h2>Flagged Reviews</h2>

            <div className="controls">
                <label>Filter by Status:</label>
                <select value={statusFilter} onChange={handleStatusFilterChange}>
                    <option value="flagged_abuse">Flagged Abuse</option>
                    <option value="pending">Pending</option>
                    <option value="legitimate">Legitimate</option>
                    <option value="needs_info">Needs More Info</option>
                </select>

                <label>Search:</label>
                <input type="text" value={searchQuery} onChange={handleSearchChange} placeholder="Search reviews..." />
            </div>

            <table>
                <thead>
                    <tr>
                        <th onClick={() => handleSortChange('reviewId')}>Review ID {sortBy === 'reviewId' && (sortOrder === 'asc' ? '▲' : '▼')}</th>
                        <th onClick={() => handleSortChange('productASIN')}>Product ASIN {sortBy === 'productASIN' && (sortOrder === 'asc' ? '▲' : '▼')}</th>
                        <th onClick={() => handleSortChange('reviewerId')}>Reviewer ID {sortBy === 'reviewerId' && (sortOrder === 'asc' ? '▲' : '▼')}</th>
                        <th onClick={() => handleSortChange('timestamp')}>Timestamp {sortBy === 'timestamp' && (sortOrder === 'asc' ? '▲' : '▼')}</th>
                        <th>Review Snippet</th>
                        <th onClick={() => handleSortChange('severity')}>Severity {sortBy === 'severity' && (sortOrder === 'asc' ? '▲' : '▼')}</th>
                        <th>Flagging Reasons</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {reviews.length === 0 ? (
                        <tr><td colSpan="8">No flagged reviews found.</td></tr>
                    ) : (
                        reviews.map((review) => (
                            <tr key={review.id}>
                                <td>{review.reviewId}</td>
                                <td>{review.productASIN}</td>
                                <td>{review.reviewerId}</td>
                                <td>{new Date(review.timestamp).toLocaleString()}</td>
                                <td>{review.reviewTextSnippet}</td>
                                <td>{review.severity}</td>
                                <td>{review.flaggingReasons.join(', ')}</td>
                                <td>{review.status}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>

            <div className="pagination">
                <button onClick={() => handlePageChange(page - 1)} disabled={page === 1}>Previous</button>
                <span> Page {page} of {totalPages} </span>
                <button onClick={() => handlePageChange(page + 1)} disabled={page === totalPages}>Next</button>
            </div>
        </div>
    );
}

export default ReviewList;
```

#### T4.4: Implement basic sorting and filtering for the list (Covered in T4.2 and T4.3 pseudocode)

*   **Backend:** The `get_flagged_reviews` FastAPI endpoint handles `status`, `sortBy`, `sortOrder`, `page`, `pageSize`, and `searchQuery` parameters to filter, sort, and paginate results directly from the database.
*   **Frontend:** The `ReviewList` React component manages `sortBy`, `sortOrder`, `statusFilter`, `page`, `pageSize`, and `searchQuery` states. `useEffect` triggers `fetchReviews` whenever these parameters change, sending updated query parameters to the backend. UI elements (dropdowns, input fields, table headers) are provided for user interaction to modify these parameters. Pagination buttons update the `page` state.

#### T4.5: Unit and E2E tests for dashboard list view (Conceptual)

*   **Unit Tests (Backend - Python/FastAPI):**
    *   Test `get_flagged_reviews` endpoint with various combinations of `status`, `sortBy`, `sortOrder`, `page`, `pageSize`, and `searchQuery` parameters.
    *   Mock the `db` session to return controlled sets of `Review` objects, verifying correct filtering, sorting, and pagination logic.
    *   Test error handling for invalid parameters or database errors.
    *   Verify the mapping from `Review` model to `DashboardReviewListItem` (especially `reviewTextSnippet` and `severity` derivation).
*   **Unit Tests (Frontend - React/Jest/Testing Library):**
    *   Test `ReviewList` component rendering with different `reviews` data (empty, single, multiple).
    *   Simulate user interactions: clicking sort headers, changing filter dropdowns, typing in search box, clicking pagination buttons.
    *   Verify that component state updates correctly and `fetchReviews` is called with the expected parameters (mock `axios.get` or `fetch`).
    *   Test loading and error states.
*   **End-to-End Tests (Cypress/Playwright):**
    *   Launch the full frontend and backend application.
    *   Navigate to the dashboard URL.
    *   Verify that the initial list of flagged reviews is displayed.
    *   Perform various user actions:
        *   Click on sorting headers and verify the order of reviews changes.
        *   Select different status filters and verify the displayed reviews.
        *   Type into the search box and verify search results.
        *   Click pagination buttons and verify the displayed page changes.
    *   Assert the content of displayed reviews, especially `reviewTextSnippet`, `flaggingReasons`, and `severity`.
    *   Test for error messages if the backend is unavailable or returns an error.
