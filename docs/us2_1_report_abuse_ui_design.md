# Sprint Backlog - User Story 2.1: Design "Report Abuse" button/link UI

### Implementation Plan
*   **Identify Placement:** Determine the optimal, user-friendly placement for the "Report Abuse" button/link within the product review component on the front-end (e.g., near the review's helpfulness rating or under the review text).
*   **Design Interaction:** Define the user interaction flow for clicking the button/link. This will likely involve a modal dialog or a redirect to a dedicated report page with a simple form. For the MVP, a modal dialog that overlays the current page is preferred for minimal navigation disruption.
*   **Visual Design:** Create a simple, clear visual design for the button/link, ensuring it's recognizable but not overly prominent to avoid accidental clicks. It should align with existing Amazon UI/UX guidelines.

### Data Models
This task is primarily UI/UX design, so there are no new backend data models directly created here. However, the design will inform the data required for the submission form in US2.2 and US2.3.

*   **Implicit Data for Reporting:**
    *   `review_id`: The ID of the review being reported.
    *   `reporting_user_id` (optional): The ID of the user submitting the report (if logged in).
    *   `reason`: A user-selected reason for reporting (e.g., "Spam," "Offensive," "Irrelevant," "Other").
    *   `comment` (optional): A free-text field for the user to provide more details.

### Architecture
This is a front-end design task.

*   **Client-Side UI:** The "Report Abuse" button/link and the associated form will be part of the existing product detail page's front-end application (e.g., React, Angular, Vue.js, or server-rendered HTML with JavaScript).

### Assumptions/Technical Decisions
*   The button/link will be visible to all users (logged-in or anonymous) but the form submission might require a logged-in user or reCAPTCHA for anonymous submissions to prevent abuse. (For MVP, assume all users can click the button, and the form will handle user identification).
*   The "Report Abuse" functionality will be implemented as a client-side interaction (e.g., a JavaScript-driven modal) to minimize page reloads.
*   The initial design will be minimalistic, focusing on core functionality rather than advanced features like categorized reporting reasons or immediate feedback messages.

### Code Snippets/Pseudocode (`public/js/components/ReviewComponent.js` - Example React/Vue Component)
```javascript
// Example: React component for a single product review

import React, { useState } from 'react';
import ReportAbuseModal from './ReportAbuseModal'; // Assume this component exists

const ReviewComponent = ({ reviewId, reviewText, author }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleReportClick = () => {
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
    };

    const handleSubmitReport = (reason, comment) => {
        console.log(`Reporting review ${reviewId} for reason: ${reason}, comment: ${comment}`);
        // In a real application, this would call an API endpoint (US2.3)
        // For now, simulate API call success
        alert('Thank you for reporting this review!');
        handleCloseModal();
    };

    return (
        <div className="product-review">
            <p className="review-text">{reviewText}</p>
            <p className="review-author">- {author}</p>
            {/* Other review details like rating, date, etc. */}

            <button
                className="report-abuse-button"
                onClick={handleReportClick}
                aria-label={`Report abuse for review by ${author}`}
            >
                Report Abuse
            </button>

            {isModalOpen && (
                <ReportAbuseModal
                    reviewId={reviewId}
                    onClose={handleCloseModal}
                    onSubmit={handleSubmitReport}
                />
            )}
        </div>
    );
};

export default ReviewComponent;

// --- ReportAbuseModal.js (Conceptual Modal Component) ---
import React, { useState } from 'react';

const ReportAbuseModal = ({ reviewId, onClose, onSubmit }) => {
    const [reason, setReason] = useState('');
    const [comment, setComment] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!reason) {
            alert('Please select a reason for reporting.');
            return;
        }
        onSubmit(reason, comment);
    };

    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Report Suspicious Review</h2>
                <p>You are reporting review ID: <strong>{reviewId}</strong></p>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="reason">Reason for reporting:</label>
                        <select
                            id="reason"
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            required
                        >
                            <option value="">-- Select a reason --</option>
                            <option value="spam">Spam or Advertising</option>
                            <option value="offensive">Offensive Content</option>
                            <option value="irrelevant">Irrelevant to Product</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="comment">Additional Comments (Optional):</label>
                        <textarea
                            id="comment"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            rows="4"
                            placeholder="Provide more details if necessary..."
                        ></textarea>
                    </div>

                    <div className="modal-actions">
                        <button type="button" onClick={onClose} className="btn-cancel">Cancel</button>
                        <button type="submit" className="btn-primary">Submit Report</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ReportAbuseModal;
