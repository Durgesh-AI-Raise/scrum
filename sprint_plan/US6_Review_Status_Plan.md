# User Story 6 (US6): Mark a review as "Abusive," "Legitimate," or "Needs More Info."

### Implementation Plan

The **Analyst Dashboard** will be extended to allow analysts to update the status of a review from its detail view (US5). This involves:

*   **Dashboard Backend Service Enhancement:**
    *   Add a new API endpoint to receive status update requests for a specific review.
    *   Implement logic to update the `status` field and `lastUpdated` timestamp in the Storage Service (US2).
    *   Implement audit logging for all status changes.
*   **Dashboard Frontend Application Enhancement:**
    *   Add UI elements (e.g., dropdown, buttons) in the `ReviewDetail` component for analysts to select a new status.
    *   Integrate these UI elements to call the new backend API for status updates.

### Data Models

1.  **ReviewStatusUpdateRequest (New Model - for API request):** This model defines the payload for updating a review's status.

    ```json
    {
        "status": "string",          // New status: "abusive", "legitimate", "needs_info"
        "analystId": "string",       // ID of the analyst performing the action
        "notes": "string"            // Optional notes from the analyst
    }
    ```

2.  **AuditLogEntry (New Model - for audit logging):** This model defines the structure for recording status changes.

    ```json
    {
        "id": "UUID",
        "reviewId": "string",
        "timestamp": "datetime",
        "oldStatus": "string",
        "newStatus": "string",
        "actionBy": "string",       // Analyst ID
        "notes": "string"           // Analyst's notes
    }
    ```

### Architecture

```
[Web Browser (Analyst)]
        |
        V
[Dashboard Frontend Application] (React/Vue/Angular)
        | (HTTP/REST: PUT /api/v1/reviews/{review_id}/status)
        V
[Dashboard Backend Service] (Python/FastAPI)
        | (API Calls / ORM)
        V
[Storage Service] (Database: PostgreSQL) <-- Update ReviewData, Insert AuditLogEntry
```

**Components:**

*   **Dashboard Frontend Application:** `ReviewDetail` component updated with status selection UI.
*   **Dashboard Backend Service:** Extends its API with a PUT endpoint for status updates and includes logic for audit logging.
*   **Storage Service:** Updates `ReviewData` and potentially stores `AuditLogEntry` (or a dedicated Audit Log Service). For simplicity in this sprint, audit logs will be part of the Storage Service's database.

### Assumptions and Technical Decisions

*   **Assumption (T6.1):** The API for updating review status will be a RESTful PUT/PATCH endpoint on the Dashboard Backend Service, which then delegates the update to the Storage Service.
*   **Assumption (T6.2):** Audit logging is crucial for compliance and traceability. A separate table (`audit_logs`) will be created in the database (US2's PostgreSQL) to store these entries. The backend logic will handle both the status update and the audit log entry as a single transactional unit if possible.
*   **Assumption (T6.3):** The UI for status selection will be a simple dropdown or set of radio buttons within the `ReviewDetail` component, offering the predefined status options.
*   **Assumption (T6.4):** The status update functionality will be integrated directly into the `ReviewDetail` component, providing immediate feedback to the analyst.
*   **Technical Decision (T6.1):** The Dashboard Backend Service will expose a `PUT /api/v1/reviews/{review_id}/status` endpoint. It will accept a `ReviewStatusUpdateRequest` payload.
*   **Technical Decision (T6.2):** The backend logic will perform the following steps:
    1.  Validate the incoming `status` and `analystId`.
    2.  Retrieve the current `Review` object from the database to get the `oldStatus`.
    3.  Update the `status` and `lastUpdated` fields of the `Review` object in the database.
    4.  Create a new `AuditLogEntry` with `review_id`, `oldStatus`, `newStatus`, `actionBy`, `notes`, and `timestamp`.
    5.  Persist the `AuditLogEntry` to a new `audit_logs` table.
    6.  Ensure these two database operations (review update, log insert) are handled within a single transaction to maintain data consistency.
*   **Technical Decision (T6.3):** The `ReviewDetail` React component will include a dropdown (`<select>`) for status selection and an optional text area for notes. A "Submit" button will trigger the API call.
*   **Technical Decision (T6.4):** Upon successful update, the `ReviewDetail` component's state will be updated to reflect the new status, and a success message will be displayed. Error messages will be shown for failures.
*   **Technical Decision (T6.5):** Unit tests for the backend will cover the status update API, including validation, database transaction, and audit log creation. Unit tests for the frontend will cover the status selection UI and event handling. E2E tests will simulate an analyst updating a review's status from the dashboard and verify the status change and audit log entry.

### Code Snippets / Pseudocode for US6:

#### T6.1: Design API for updating review status (Python Pseudocode with FastAPI)

```python
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

# Assume Review model, Base, SessionLocal, and engine from US2's Storage_Plan
# We'll also define a placeholder AuditLog model here.

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

# --- Placeholder for Review Model from US2 --- END

# New AuditLog model
class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(SQL_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(String(255), nullable=False) # Link to the review
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    action_by = Column(String(255), nullable=False) # Analyst ID
    notes = Column(Text)

    def __repr__(self):
        return f"<AuditLog(review_id='{self.review_id}', old='{self.old_status}', new='{self.new_status}')>"

# Example DB setup (for standalone running, replace with actual config)
DATABASE_URL = "sqlite:///./test.db" # Use a simple SQLite for demonstration
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_tables_for_status_api():
    Base.metadata.create_all(bind=engine)

# Pydantic model for request payload
class ReviewStatusUpdateRequest(BaseModel):
    status: str
    analystId: str
    notes: Optional[str] = None

# Pydantic model for response (can be a simple success message or updated review summary)
class StatusUpdateResponse(BaseModel):
    message: str
    reviewId: str
    newStatus: str
    lastUpdated: datetime

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.put("/api/v1/reviews/{review_id}/status", response_model=StatusUpdateResponse)
async def update_review_status(
    review_id: str = Path(..., description="The unique identifier of the review"),
    request: ReviewStatusUpdateRequest = Depends(),
    db: Session = Depends(get_db)
):
    # Validate new status
    allowed_statuses = ["abusive", "legitimate", "needs_info", "pending", "flagged_abuse"]
    if request.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}. Allowed statuses are: {', '.join(allowed_statuses)}")

    # 1. Retrieve the current review
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    old_status = review.status

    # 2. Update review status and last_updated
    review.status = request.status
    review.last_updated = datetime.now(timezone.utc) # Explicitly set, as onupdate might be lazy

    # 3. Create audit log entry
    audit_log = AuditLog(
        review_id=review_id,
        old_status=old_status,
        new_status=request.status,
        action_by=request.analystId,
        notes=request.notes
    )
    db.add(audit_log)

    try:
        db.commit()
        db.refresh(review) # Refresh to get the latest updated_at
        print(f"Review {review_id} status updated from {old_status} to {request.status} by {request.analystId}")
        return StatusUpdateResponse(
            message="Review status updated successfully",
            reviewId=review.review_id,
            newStatus=review.status,
            lastUpdated=review.last_updated
        )
    except Exception as e:
        db.rollback()
        print(f"Error updating review status or audit log for {review_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update review status due to a database error.")

# To run this with uvicorn:
# uvicorn main:app --reload
```

#### T6.2: Implement backend logic for status update and audit logging (Covered in T6.1 pseudocode)

The `update_review_status` FastAPI endpoint directly implements the logic for:
*   Fetching the existing review to get `old_status`.
*   Updating the `status` and `last_updated` fields of the `Review` object.
*   Creating and adding a new `AuditLog` entry.
*   Ensuring atomicity with `db.commit()` and `db.rollback()`.

A new table `audit_logs` is defined in the SQLAlchemy `Base` and will be created via `create_db_tables_for_status_api()`.

#### T6.3: Develop front-end UI for status selection (React Pseudocode)

```javascript
// components/ReviewDetail.js (modification)
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

function ReviewDetail() {
    const { reviewId } = useParams();
    const [reviewContext, setReviewContext] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [statusUpdateLoading, setStatusUpdateLoading] = useState(false);
    const [statusUpdateError, setStatusUpdateError] = useState(null);
    const [statusUpdateSuccess, setStatusUpdateSuccess] = useState(null);

    const [selectedStatus, setSelectedStatus] = useState('');
    const [analystNotes, setAnalystNotes] = useState('');

    useEffect(() => {
        fetchReviewContext();
    }, [reviewId]);

    const fetchReviewContext = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`/api/v1/reviews/${reviewId}/context`);
            setReviewContext(response.data);
            setSelectedStatus(response.data.status); // Set initial status for dropdown
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

    const handleStatusChange = (e) => {
        setSelectedStatus(e.target.value);
        setStatusUpdateError(null); // Clear previous errors on change
        setStatusUpdateSuccess(null);
    };

    const handleNotesChange = (e) => {
        setAnalystNotes(e.target.value);
    };

    const handleSubmitStatusUpdate = async () => {
        if (!selectedStatus || !reviewId) {
            setStatusUpdateError('Please select a status and ensure review ID is present.');
            return;
        }
        
        // For MVP, hardcode analystId or fetch from auth context
        const analystId = "analyst_john_doe"; 

        setStatusUpdateLoading(true);
        setStatusUpdateError(null);
        setStatusUpdateSuccess(null);

        try {
            const response = await axios.put(`/api/v1/reviews/${reviewId}/status`, {
                status: selectedStatus,
                analystId: analystId,
                notes: analystNotes || null, // Send null if empty
            });
            // Update the local state with the new status and last updated timestamp
            setReviewContext(prevContext => ({
                ...prevContext,
                status: response.data.newStatus,
                lastUpdated: new Date(response.data.lastUpdated),
            }));
            setStatusUpdateSuccess('Review status updated successfully!');
            setAnalystNotes(''); // Clear notes after successful update
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to update review status.';
            setStatusUpdateError(errorMessage);
            console.error('Status update error:', err);
        } finally {
            setStatusUpdateLoading(false);
        }
    };

    if (loading) return <div>Loading review details...</div>;
    if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
    if (!reviewContext) return <div>No review context available.</div>;

    return (
        <div className="review-detail-container">
            <h2>Review Details: {reviewContext.reviewId}</h2>

            <div className="review-main-info">
                {/* ... (existing display of reviewContext data) ... */}
                <p><strong>Review ID:</strong> {reviewContext.reviewId}</p>
                <p><strong>Product ASIN:</strong> {reviewContext.productASIN}</p>
                <p><strong>Reviewer ID:</strong> {reviewContext.reviewerId}</p>
                <p><strong>Timestamp:</strong> {new Date(reviewContext.timestamp).toLocaleString()}</p>
                <p><strong>IP Address:</strong> {reviewContext.ipAddress}</p>
                <p><strong>Rating:</strong> {reviewContext.rating ? `${reviewContext.rating} / 5` : 'N/A'}</p>
                <p><strong>Title:</strong> {reviewContext.reviewTitle || 'N/A'}</p>
                <p><strong>Current Status:</strong> <span className={`status-${reviewContext.status.replace('_', '-')}`}>{reviewContext.status}</span></p>
                <p><strong>Flagging Reasons:</strong> {reviewContext.flaggingReasons.join(', ') || 'None'}</p>
                <p><strong>Last Updated:</strong> {new Date(reviewContext.lastUpdated).toLocaleString()}</p>
                <h4>Review Text:</h4>
                <p className="review-text-full">{reviewContext.reviewText}</p>
            </div>

            <div className="reviewer-history">
                {/* ... (existing display of reviewer history) ... */}
            </div>

            <div className="product-details">
                {/* ... (existing display of product details) ... */}
            </div>

            <div className="review-actions">
                <h3>Update Review Status</h3>
                <div>
                    <label htmlFor="status-select">New Status:</label>
                    <select id="status-select" value={selectedStatus} onChange={handleStatusChange} disabled={statusUpdateLoading}>
                        <option value="flagged_abuse">Flagged Abuse</option>
                        <option value="abusive">Abusive</option>
                        <option value="legitimate">Legitimate</option>
                        <option value="needs_info">Needs More Info</option>
                        <option value="pending">Pending</option> {/* Can revert to pending */}
                    </select>
                </div>
                <div>
                    <label htmlFor="analyst-notes">Notes (Optional):</label>
                    <textarea id="analyst-notes" value={analystNotes} onChange={handleNotesChange} rows="3" disabled={statusUpdateLoading}></textarea>
                </div>
                <button onClick={handleSubmitStatusUpdate} disabled={statusUpdateLoading}>
                    {statusUpdateLoading ? 'Updating...' : 'Update Status'}
                </button>
                {statusUpdateError && <p style={{ color: 'red' }}>{statusUpdateError}</p>}
                {statusUpdateSuccess && <p style={{ color: 'green' }}>{statusUpdateSuccess}</p>}
            </div>
        </div>
    );
}

export default ReviewDetail;
```

#### T6.4: Integrate status update functionality with review details view (Covered in T6.3 pseudocode)

The React `ReviewDetail` component is updated to include:
*   State variables for `selectedStatus`, `analystNotes`, and UI feedback (`statusUpdateLoading`, `statusUpdateError`, `statusUpdateSuccess`).
*   A `useEffect` hook to initialize `selectedStatus` from the fetched `reviewContext.status`.
*   A `<select>` element for `selectedStatus` and a `<textarea>` for `analystNotes`.
*   An "Update Status" `<button>` which triggers `handleSubmitStatusUpdate`.
*   `handleSubmitStatusUpdate` constructs the request payload, makes the `axios.put` call to the backend API, and updates the local `reviewContext` state upon success.

#### T6.5: Unit and E2E tests for status update (Conceptual)

*   **Unit Tests (Backend - Python/FastAPI):**
    *   Test `update_review_status` endpoint with valid status updates, ensuring both the `Review` table and `AuditLog` table are correctly updated within a transaction.
    *   Mock the `db` session to verify `db.query`, `db.add`, `db.commit`, and `db.rollback` calls.
    *   Test with invalid `review_id` (expecting 404).
    *   Test with invalid `status` values (expecting 400).
    *   Test concurrent updates (though transactional integrity should handle this at DB level).
*   **Unit Tests (Frontend - React/Jest/Testing Library):**
    *   Test `ReviewDetail` component rendering with status selection UI.
    *   Simulate user selecting a status, typing notes, and clicking the "Update Status" button.
    *   Mock `axios.put` to simulate successful and failed API responses.
    *   Verify that the `reviewContext` state is updated correctly after a successful API call.
    *   Verify loading, success, and error messages are displayed appropriately.
    *   Ensure the "Update Status" button is disabled during API calls.
*   **End-to-End Tests (Cypress/Playwright):**
    *   Launch the full frontend and backend application.
    *   Navigate to a specific review's detail page (`/dashboard/reviews/:reviewId`).
    *   Select a new status from the dropdown and optionally enter notes.
    *   Click the "Update Status" button.
    *   Verify that a success message appears on the frontend.
    *   Refresh the page or navigate away and back to the same review to verify the new status is persistently displayed.
    *   Directly query the backend API for the review context to verify the status change and check the `audit_logs` table for the new entry.
    *   Test for error scenarios (e.g., trying to update a non-existent review, network issues).
