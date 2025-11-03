# User Story 5 (US5): View the full context of a flagged review.

### Implementation Plan

The **Analyst Dashboard** will be extended to allow analysts to click on a flagged review from the list view (US4) and see its full context. This involves:

*   **Dashboard Backend Service Enhancement:**
    *   Add a new API endpoint to fetch the complete details of a single review, including all its metadata, reviewer history summary, product details, and all flagging reasons.
    *   This endpoint will query the Storage Service (US2) to retrieve the full `ReviewData` object.
    *   It will also need to aggregate reviewer history (e.g., count of reviews, average rating by the reviewer) and product details (e.g., product title, category).
*   **Dashboard Frontend Application Enhancement:**
    *   Develop a new component to display the detailed view of a single review.
    *   Integrate this detail view with the existing list view, so clicking on a list item navigates to the detail view.

### Data Models

1.  **ReviewData (from Storage Service):** The full model as defined in US2 (id, reviewId, reviewerId, productASIN, timestamp, ipAddress, reviewText, rating, reviewTitle, source, ingestionTimestamp, status, flaggingReasons, lastUpdated).
2.  **ReviewContext (New Model - for API response):** This model aggregates all information needed for the full context view.

    ```json
    {
        "id": "UUID",
        "reviewId": "string",
        "reviewerId": "string",
        "productASIN": "string",
        "timestamp": "datetime",
        "ipAddress": "string",
        "reviewText": "string",
        "rating": "integer",
        "reviewTitle": "string/null",
        "source": "string",
        "ingestionTimestamp": "datetime",
        "status": "string",
        "flaggingReasons": "array<string>",
        "lastUpdated": "datetime",
        "reviewerHistorySummary": {  // Aggregated data from Storage Service
            "totalReviews": "integer",
            "averageRating": "float",
            "firstReviewDate": "datetime",
            "lastReviewDate": "datetime",
            "uniqueProductsReviewed": "integer"
        },
        "productDetails": { // Can be a lookup or fetched from an external product catalog if available
            "title": "string",
            "category": "string/null",
            "brand": "string/null",
            "averageRating": "float" // Average rating for this product across all reviews
        }
    }
    ```

### Architecture

```
[Web Browser (Analyst)]
        |
        V
[Dashboard Frontend Application] (React/Vue/Angular)
        | (HTTP/REST: /api/v1/reviews/{review_id}/context)
        V
[Dashboard Backend Service] (Python/FastAPI)
        | (API Calls / ORM)
        V
[Storage Service] (Database: PostgreSQL) <-- Queries for ReviewData, ReviewerHistory, ProductDetails
```

**Components:**

*   **Dashboard Frontend Application:** Extends the existing SPA to include a `ReviewDetail` component.
*   **Dashboard Backend Service:** Extends its API to include a new endpoint for fetching full review context. It aggregates data from the Storage Service.
*   **Storage Service:** Provides efficient querying capabilities for single reviews, reviewer history, and product details.

### Assumptions and Technical Decisions

*   **Assumption (T5.1):** The Storage Service (US2) will be able to efficiently provide not just the main review data, but also aggregated reviewer history (e.g., total reviews by a reviewer, average rating) and product details based on the `reviewerId` and `productASIN`. This might require additional queries or optimized views in the database. For MVP, basic aggregations from the `reviews` table will suffice.
*   **Assumption (T5.2):** The frontend framework (React) will be used consistently for the detail view. The detail view will present all available data in a readable format.
*   **Assumption (T5.3):** Navigation between the list view and the detail view will be handled using client-side routing.
*   **Technical Decision (T5.1):** The Dashboard Backend Service will expose a new GET endpoint: `/api/v1/reviews/{review_id}/context`. This endpoint will perform the following steps:
    1.  Fetch the `ReviewData` object for the given `review_id` from the Storage Service.
    2.  Perform aggregate queries on the Storage Service using `reviewerId` to calculate `reviewerHistorySummary` (e.g., `COUNT(*)`, `AVG(rating)`, `MIN(timestamp)`, `MAX(timestamp)`, `COUNT(DISTINCT product_asin)`).
    3.  Perform aggregate queries on the Storage Service using `productASIN` to calculate `productDetails` (e.g., `AVG(rating)` for the product).
    4.  Combine all this information into the `ReviewContext` model and return it.
*   **Technical Decision (T5.2):** A new React component, `ReviewDetail.js`, will be created. It will receive the `reviewId` as a prop (or from the URL parameter), fetch the `ReviewContext` data from the backend API, and display it.
*   **Technical Decision (T5.3):** React Router will be used for client-side routing. A route like `/dashboard/reviews/:reviewId` will be defined to load the `ReviewDetail` component. Clicking on a row in `ReviewList` will navigate to this new route.
*   **Technical Decision (T5.4):** Unit tests for the backend will cover the new API endpoint, including data retrieval, aggregation logic, and error handling. Unit tests for the frontend will cover the `ReviewDetail` component's rendering of various data states. E2E tests will verify the navigation from list to detail view and the correct display of full context information.

### Code Snippets / Pseudocode for US5:

#### T5.1: Enhance backend API to retrieve full review context data (Python Pseudocode with FastAPI)

```python
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

# Assume Review model, Base, SessionLocal, and engine from US2's Storage_Plan
# For demonstration, we'll re-include the placeholder Review model.

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

def create_db_tables_for_context_api():
    Base.metadata.create_all(bind=engine)

# --- Placeholder for Review Model from US2 --- END

# Pydantic models for nested context data
class ReviewerHistorySummary(BaseModel):
    totalReviews: int
    averageRating: Optional[float]
    firstReviewDate: Optional[datetime]
    lastReviewDate: Optional[datetime]
    uniqueProductsReviewed: int

class ProductDetails(BaseModel):
    title: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    averageRating: Optional[float]

# Pydantic model for the full review context response
class ReviewContext(BaseModel):
    id: uuid.UUID
    reviewId: str
    reviewerId: str
    productASIN: str
    timestamp: datetime
    ipAddress: str
    reviewText: str
    rating: Optional[int]
    reviewTitle: Optional[str]
    source: str
    ingestionTimestamp: datetime
    status: str
    flaggingReasons: List[str]
    lastUpdated: datetime
    reviewerHistorySummary: ReviewerHistorySummary
    productDetails: ProductDetails

    class Config:
        from_attributes = True

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/reviews/{review_id}/context", response_model=ReviewContext)
async def get_review_context(
    review_id: str = Path(..., description="The unique identifier of the review"),
    db: Session = Depends(get_db)
):
    # 1. Fetch the main review data
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # 2. Aggregate reviewer history summary
    reviewer_history = db.query(
        func.count(Review.id).label('totalReviews'),
        func.avg(Review.rating).label('averageRating'),
        func.min(Review.timestamp).label('firstReviewDate'),
        func.max(Review.timestamp).label('lastReviewDate'),
        func.count(distinct(Review.product_asin)).label('uniqueProductsReviewed')
    ).filter(Review.reviewer_id == review.reviewer_id).one_or_none()

    # Handle cases where reviewer_history might be None (shouldn't happen if review exists, but for safety)
    if reviewer_history:
        reviewer_summary = ReviewerHistorySummary(
            totalReviews=reviewer_history.totalReviews,
            averageRating=reviewer_history.averageRating,
            firstReviewDate=reviewer_history.firstReviewDate,
            lastReviewDate=reviewer_history.lastReviewDate,
            uniqueProductsReviewed=reviewer_history.uniqueProductsReviewed
        )
    else:
        reviewer_summary = ReviewerHistorySummary(totalReviews=0, averageRating=None, firstReviewDate=None, lastReviewDate=None, uniqueProductsReviewed=0)


    # 3. Aggregate product details
    product_stats = db.query(
        func.avg(Review.rating).label('averageRating')
    ).filter(Review.product_asin == review.product_asin).one_or_none()

    # Placeholder for actual product title, category, brand lookup (would come from an external service or a product catalog DB)
    product_details = ProductDetails(
        title=f"Product Title for {review.product_asin}", # Mock data
        category="Electronics", # Mock data
        brand="Generic Brand", # Mock data
        averageRating=product_stats.averageRating if product_stats else None
    )

    # 4. Combine and return
    return ReviewContext(
        id=review.id,
        reviewId=review.review_id,
        reviewerId=review.reviewer_id,
        productASIN=review.product_asin,
        timestamp=review.timestamp,
        ipAddress=review.ip_address,
        reviewText=review.review_text,
        rating=review.rating,
        reviewTitle=review.review_title,
        source=review.source,
        ingestionTimestamp=review.ingestion_timestamp,
        status=review.status,
        flaggingReasons=review.flagging_reasons,
        lastUpdated=review.last_updated,
        reviewerHistorySummary=reviewer_summary,
        productDetails=product_details
    )

# To run this with uvicorn:
# uvicorn main:app --reload
```

#### T5.2: Develop front-end component for displaying full review details (React Pseudocode)

```javascript
// components/ReviewDetail.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom'; // Assuming React Router
import axios from 'axios';

function ReviewDetail() {
    const { reviewId } = useParams(); // Get reviewId from URL parameter
    const [reviewContext, setReviewContext] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchReviewContext = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await axios.get(`/api/v1/reviews/${reviewId}/context`);
                setReviewContext(response.data);
            } catch (err) {
                if (err.response && err.response.status === 404) {
                    setError('Review not found.');
                } else {
                    setError('Failed to fetch review details. Please try again.');
                }
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (reviewId) {
            fetchReviewContext();
        }
    }, [reviewId]);

    if (loading) return <div>Loading review details...</div>;
    if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
    if (!reviewContext) return <div>No review context available.</div>;

    return (
        <div className="review-detail-container">
            <h2>Review Details: {reviewContext.reviewId}</h2>

            <div className="review-main-info">
                <h3>Main Review Information</h3>
                <p><strong>Review ID:</strong> {reviewContext.reviewId}</p>
                <p><strong>Product ASIN:</strong> {reviewContext.productASIN}</p>
                <p><strong>Reviewer ID:</strong> {reviewContext.reviewerId}</p>
                <p><strong>Timestamp:</strong> {new Date(reviewContext.timestamp).toLocaleString()}</p>
                <p><strong>IP Address:</strong> {reviewContext.ipAddress}</p>
                <p><strong>Rating:</strong> {reviewContext.rating ? `${reviewContext.rating} / 5` : 'N/A'}</p>
                <p><strong>Title:</strong> {reviewContext.reviewTitle || 'N/A'}</p>
                <p><strong>Status:</strong> <span className={`status-${reviewContext.status.replace('_', '-')}`}>{reviewContext.status}</span></p>
                <p><strong>Flagging Reasons:</strong> {reviewContext.flaggingReasons.join(', ') || 'None'}</p>
                <h4>Review Text:</h4>
                <p className="review-text-full">{reviewContext.reviewText}</p>
            </div>

            <div className="reviewer-history">
                <h3>Reviewer History Summary</h3>
                <p><strong>Total Reviews by Reviewer:</strong> {reviewContext.reviewerHistorySummary.totalReviews}</p>
                <p><strong>Average Rating by Reviewer:</strong> {reviewContext.reviewerHistorySummary.averageRating ? reviewContext.reviewerHistorySummary.averageRating.toFixed(2) : 'N/A'}</p>
                <p><strong>First Review Date:</strong> {reviewContext.reviewerHistorySummary.firstReviewDate ? new Date(reviewContext.reviewerHistorySummary.firstReviewDate).toLocaleString() : 'N/A'}</p>
                <p><strong>Last Review Date:</strong> {reviewContext.reviewerHistorySummary.lastReviewDate ? new Date(reviewContext.reviewerHistorySummary.lastReviewDate).toLocaleString() : 'N/A'}</p>
                <p><strong>Unique Products Reviewed:</strong> {reviewContext.reviewerHistorySummary.uniqueProductsReviewed}</p>
            </div>

            <div className="product-details">
                <h3>Product Details</h3>
                <p><strong>Product Title:</strong> {reviewContext.productDetails.title || 'N/A'}</p>
                <p><strong>Category:</strong> {reviewContext.productDetails.category || 'N/A'}</p>
                <p><strong>Brand:</strong> {reviewContext.productDetails.brand || 'N/A'}</p>
                <p><strong>Average Product Rating:</strong> {reviewContext.productDetails.averageRating ? reviewContext.productDetails.averageRating.toFixed(2) : 'N/A'}</p>
            </div>

            {/* Placeholder for US6 actions */}
            {/* <div className="review-actions">
                <button onClick={() => console.log('Mark as Abusive')}>Mark as Abusive</button>
                <button onClick={() => console.log('Mark as Legitimate')}>Mark as Legitimate</button>
            </div> */}
        </div>
    );
}

export default ReviewDetail;
```

#### T5.3: Integrate review details view with the dashboard (React Router Pseudocode)

```javascript
// App.js (or main routing file)
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ReviewList from './components/ReviewList';
import ReviewDetail from './components/ReviewDetail';
import './App.css'; // For basic styling

function App() {
    return (
        <Router>
            <div className="app-container">
                <header>
                    <h1>Review Abuse Tracking System</h1>
                    <nav>
                        <Link to="/dashboard/reviews">Dashboard</Link>
                    </nav>
                </header>
                <main>
                    <Routes>
                        <Route path="/dashboard/reviews" element={<ReviewList />} />
                        <Route path="/dashboard/reviews/:reviewId" element={<ReviewDetail />} />
                        <Route path="/" element={<Home />} /> {/* Optional home page */}
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

function Home() {
    return <h2>Welcome to the Analyst Dashboard!</h2>;
}

export default App;

// In ReviewList.js, make review rows clickable:
// ...
// import { useNavigate } from 'react-router-dom';
// ...
// function ReviewList() {
//     const navigate = useNavigate();
//     // ...
//     return (
//         // ...
//             <tbody>
//                 {reviews.length === 0 ? (
//                     <tr><td colSpan="8">No flagged reviews found.</td></tr>
//                 ) : (
//                     reviews.map((review) => (
//                         <tr key={review.id} onClick={() => navigate(`/dashboard/reviews/${review.reviewId}`)} style={{ cursor: 'pointer' }}>
//                             <td>{review.reviewId}</td>
//                             <td>{review.productASIN}</td>
//                             <td>{review.reviewerId}</td>
//                             <td>{new Date(review.timestamp).toLocaleString()}</td>
//                             <td>{review.reviewTextSnippet}</td>
//                             <td>{review.severity}</td>
//                             <td>{review.flaggingReasons.join(', ')}</td>
//                             <td>{review.status}</td>
//                         </tr>
//                     ))
//                 )}
//             </tbody>
//         // ...
//     );
// }
//
// export default ReviewList;
```

#### T5.4: Unit and E2E tests for context view (Conceptual)

*   **Unit Tests (Backend - Python/FastAPI):**
    *   Test `get_review_context` endpoint with valid `review_id`s.
    *   Mock the `db` session to return a `Review` object and then controlled results for reviewer history and product statistics queries.
    *   Verify that the returned `ReviewContext` object contains correct aggregated data.
    *   Test for non-existent `review_id` (expecting 404 HTTPException).
    *   Test edge cases for reviewer history (e.g., reviewer with only one review).
*   **Unit Tests (Frontend - React/Jest/Testing Library):**
    *   Test `ReviewDetail` component rendering with mock `reviewContext` data (full data, partial data, missing optional fields).
    *   Test loading and error states.
    *   Mock `axios.get` for the API call to control response data.
    *   Verify all relevant information from `reviewContext` is displayed correctly.
*   **End-to-End Tests (Cypress/Playwright):**
    *   Launch the full frontend and backend application.
    *   Navigate to the dashboard list view (`/dashboard/reviews`).
    *   Click on a specific review in the list.
    *   Verify that the browser navigates to the correct review detail URL (`/dashboard/reviews/:reviewId`).
    *   Assert that all contextual information (main review, reviewer history, product details) is displayed accurately on the detail page.
    *   Verify correct formatting of dates, ratings, etc.
    *   Test what happens if an invalid `reviewId` is accessed directly in the URL (should show an error).
