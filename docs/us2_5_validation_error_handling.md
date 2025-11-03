## Sprint Backlog - User Story 2.5: Add validation and error handling for report submission

### Implementation Plan
*   **Enhance API Endpoint Validation (Backend):**
    *   Expand validation in the `/api/report-abuse` endpoint (from US2.3) to cover all incoming fields.
    *   **Review ID:** Ensure it's a valid format (e.g., alphanumeric string, non-empty).
    *   **Reason:** Enforce that `reason` is one of the predefined valid categories.
    *   **Comment:** Validate `comment` length (e.g., max 500 characters) and perform basic sanitization to prevent XSS attacks.
    *   **Reporting User ID:** If present, validate its format.
*   **Centralized Validation Logic:**
    *   Introduce validation logic directly within the endpoint for MVP.
*   **Robust Error Responses (Backend):**
    *   Return clear, structured error messages in the API response for invalid inputs (HTTP 400 Bad Request).
    *   Include specific error details (e.g., which field failed, why) to aid front-end debugging and user feedback.
    *   Implement generic error handling for unexpected server-side issues (HTTP 500 Internal Server Error).
*   **Backend Error Logging:**
    *   Ensure all validation failures and unexpected errors are properly logged with sufficient detail for debugging and monitoring.
*   **Front-end Error Display (Client-Side):**
    *   Update the `ReportAbuseFormModal` (from US2.2) to display validation errors received from the backend API.
    *   Show inline error messages next to the relevant form fields.
    *   Provide general error messages for submission failures that are not specific to a field.

### Data Models
*   **No new core data models.** This task primarily focuses on refining the input and output structures for validation and error reporting.
*   **`ErrorResponse` (API Output - Conceptual):**
    ```json
    {
        "status": "error",
        "message": "string", // General error message
        "errors": {
            "field_name_1": "error_message_1",
            "field_name_2": "error_message_2",
            // ...
        } // Optional: detailed field-specific errors
    }
    ```

### Architecture
*   **`CustomerReportingService` (Backend):** The API endpoint `/api/report-abuse` within this service will be enhanced.
*   **Client-Side Application:** The `ReportAbuseFormModal` and its submission logic will be updated to handle and display backend validation errors.

### Assumptions/Technical Decisions
*   **Python Backend:** Using Flask/FastAPI for the backend service (consistent with US2.3).
*   **Direct Validation:** For MVP, direct validation checks within the API endpoint function are acceptable. Future iterations might integrate a more robust validation library (e.g., Pydantic).
*   **Standard HTTP Error Codes:** Using standard HTTP status codes (400 for client errors, 500 for server errors).
*   **Detailed Error Messages:** Backend will provide detailed error messages to facilitate specific front-end feedback.
*   **Logging:** Basic logging is set up for backend services.
*   **Frontend Library:** Assumed to be using a modern JavaScript framework (like React) for front-end development, allowing for dynamic error display.

### Code Snippets/Pseudocode

#### `app/api/customer_reporting_api.py` (Enhanced with Validation and Error Handling)
```python
from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import json
import logging
import re # For regex validation if needed

app = Flask(__name__)
logging.basicConfig(level=logging.INFO) # Basic logging setup

# Placeholder for a message queue producer
# from some_mq_library import MessageQueueProducer
# mq_producer = MessageQueueProducer('customer_abuse_reports_events')

@app.route('/api/report-abuse', methods=['POST'])
def report_abuse():
    data = request.get_json()
    errors = {}

    # 1. Robust Input Validation
    # Validate review_id
    review_id = data.get('review_id')
    if not review_id:
        errors['review_id'] = 'Review ID is required.'
    elif not isinstance(review_id, str) or not re.match(r'^[a-zA-Z0-9_-]+$', review_id): # Example: alphanumeric, hyphen, underscore
        errors['review_id'] = 'Invalid Review ID format.'

    # Validate reason
    reason = data.get('reason')
    allowed_reasons = ["spam", "offensive", "fake", "irrelevant", "other"]
    if not reason:
        errors['reason'] = 'Reason for reporting is required.'
    elif reason not in allowed_reasons:
        errors['reason'] = f'Invalid reason provided. Must be one of: {", '.join(allowed_reasons)}.'

    # Validate comment (optional)
    comment = data.get('comment')
    if comment and not isinstance(comment, str):
        errors['comment'] = 'Comment must be a string.'
    elif comment and len(comment) > 500:
        errors['comment'] = 'Comment cannot exceed 500 characters.'
    # Basic sanitization (production-grade would use a dedicated library)
    if comment:
        comment = comment.replace('<', '&lt;').replace('>', '&gt;')

    # Validate reporting_user_id (optional)
    reporting_user_id = data.get('reporting_user_id')
    if reporting_user_id and not isinstance(reporting_user_id, str):
        errors['reporting_user_id'] = 'Reporting User ID must be a string.'
    # Further validation (e.g., UUID format for user_id) could be added here.

    if errors:
        logging.warning(f"Validation failed for abuse report: {errors}")
        return jsonify({"status": "error", "message": "Validation failed.", "errors": errors}), 400

    # If validation passes, proceed
    report_id = str(uuid.uuid4())
    report_timestamp = datetime.utcnow().isoformat() + "Z"

    event_payload = {
        "report_id": report_id,
        "review_id": review_id,
        "reason": reason,
        "comment": comment,
        "reporting_user_id": reporting_user_id,
        "report_timestamp": report_timestamp
    }

    # 2. Publish Event to Message Queue (Pseudocode with Error Handling)
    try:
        # mq_producer.publish(event_payload)
        logging.info(f"Simulating MQ publish for customer report: {report_id}")
    except Exception as e:
        logging.error(f"Message queue error publishing report {report_id}: {e}", exc_info=True)
        # In a real system, you might have a retry mechanism or a dead-letter queue
        # For this MVP, we consider it a server error if MQ fails critically
        return jsonify({"status": "error", "message": "Report received but failed to publish for processing. Please try again later."}), 500

    return jsonify({"status": "success", "message": "Abuse report received and is being processed.", "report_id": report_id}), 202

if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

#### `public/js/components/ReportAbuseFormModal.js` (Updated for Error Handling)
```javascript
import React, { useState } from 'react';
import './ReportAbuseFormModal.css'; // Basic styling for the modal

const ReportAbuseFormModal = ({ reviewId, onClose, onSubmit }) => {
    const [reason, setReason] = useState('');
    const [comment, setComment] = useState('');
    const [formErrors, setFormErrors] = useState({}); // To store backend errors
    const [generalError, setGeneralError] = useState(''); // For non-field-specific errors
    const [isSubmitting, setIsSubmitting] = useState(false); // To prevent double submission

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({}); // Clear previous errors
        setGeneralError('');
        setIsSubmitting(true);

        // Basic client-side validation (can be more extensive)
        if (!reason) {
            setFormErrors(prev => ({ ...prev, reason: 'Please select a reason for reporting.' }));
            setIsSubmitting(false);
            return;
        }

        try {
            const response = await fetch('/api/report-abuse', { // This is the actual API call
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    review_id: reviewId,
                    reason,
                    comment,
                    // reporting_user_id: 'current_user_id' // This would come from session/auth
                }),
            });

            const responseData = await response.json();

            if (!response.ok) {
                if (response.status === 400 && responseData.errors) {
                    setFormErrors(responseData.errors); // Display field-specific errors
                    setGeneralError(responseData.message || 'Please correct the errors below.');
                } else {
                    setGeneralError(responseData.message || 'Failed to submit report. Please try again later.');
                }
            } else {
                alert('Thank you for reporting this review. We will review it shortly.');
                onSubmit(); // Call the parent's onSubmit, which might just close the modal
            }
        } catch (error) {
            console.error('Error submitting report:', error);
            setGeneralError('An unexpected error occurred. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h2>Report Review</h2>
                    <button className="close-button" onClick={onClose} disabled={isSubmitting}>&times;</button>
                </div>
                <div className="modal-body">
                    <p>Reporting review ID: <strong>{reviewId}</strong></p>

                    {generalError && <div className="alert-error">{generalError}</div>} {/* General error message */}

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="reason">Reason:</label>
                            <select
                                id="reason"
                                value={reason}
                                onChange={(e) => {
                                    setReason(e.target.value);
                                    setFormErrors(prev => ({ ...prev, reason: '' })); // Clear error on change
                                }}
                                className={formErrors.reason ? 'is-invalid' : ''}
                            >
                                <option value="">Select a reason</option>
                                <option value="spam">Spam or Advertising</option>
                                <option value="offensive">Offensive Content</option>
                                <option value="fake">Fake Review</option>
                                <option value="irrelevant">Irrelevant Content</option>
                                <option value="other">Other</option>
                            </select>
                            {formErrors.reason && <div className="error-message">{formErrors.reason}</div>}
                        </div>
                        <div className="form-group">
                            <label htmlFor="comment">Comments (Optional):</label>
                            <textarea
                                id="comment"
                                rows="4"
                                value={comment}
                                onChange={(e) => {
                                    setComment(e.target.value);
                                    setFormErrors(prev => ({ ...prev, comment: '' })); // Clear error on change
                                }}
                                placeholder="Provide more details if necessary..."
                                className={formErrors.comment ? 'is-invalid' : ''}
                            ></textarea>
                            {formErrors.comment && <div className="error-message">{formErrors.comment}</div>}
                        </div>
                        <div className="modal-footer">
                            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={isSubmitting}>Cancel</button>
                            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                                {isSubmitting ? 'Submitting...' : 'Submit Report'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ReportAbuseFormModal;
```