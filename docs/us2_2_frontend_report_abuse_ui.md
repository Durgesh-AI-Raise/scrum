## Sprint Backlog - User Story 2.2: Implement front-end UI for "Report Abuse" button and form

### Implementation Plan
*   **Integrate Button/Link:** Implement the "Report Abuse" button/link directly into the product review component using the design specified in US2.1.
*   **Develop Modal/Form Component:** Create the front-end components for the "Report Abuse" modal dialog, including fields for `reason` (dropdown with predefined options) and `comment` (textarea).
*   **State Management:** Implement local state management (e.g., React's useState) to handle the visibility of the modal and the input values of the form fields.
*   **Form Submission Handling:** On form submission, gather the `review_id`, selected `reason`, and `comment`. This data will then be sent to the backend API endpoint (to be developed in US2.3). For now, it will simulate an API call.
*   **Basic Styling:** Apply basic CSS styling to ensure the button/link and form are presentable and fit within the existing product page layout.

### Data Models
*   **Form Data (Client-Side - Conceptual):**
    ```typescript
    interface ReportAbuseFormData {
        reviewId: string;
        reason: 'spam' | 'offensive' | 'fake' | 'irrelevant' | 'other' | '';
        comment: string;
    }
    ```

### Architecture
*   **Client-Side Application:** The front-end UI components (button, modal, form) will be part of the existing web application (e.g., a React, Angular, or Vue.js application).
*   **API Client (Implicit):** A client-side JavaScript module will be responsible for making HTTP POST requests to the `/api/report-abuse` endpoint (US2.3).

### Assumptions/Technical Decisions
*   The existing product review component is extensible to include the "Report Abuse" button/link.
*   A modern JavaScript framework (e.g., React, Vue, Angular) is being used for the front-end. The pseudocode uses React for demonstration.
*   Basic client-side validation (e.g., ensuring a reason is selected) will be implemented to improve user experience before sending data to the backend. More robust validation will occur on the backend (US2.5).
*   For the MVP, a simple `alert()` will be used to confirm submission, with proper UI feedback (e.g., toast messages, success banners) to be implemented in future iterations.

### Code Snippets/Pseudocode (`public/js/components/ReportAbuseButton.js`, `public/js/components/ReportAbuseFormModal.js`, `public/css/ReportAbuseFormModal.css` - React Example):

```javascript
// public/js/components/ReportAbuseButton.js
import React, { useState } from 'react';
import ReportAbuseFormModal from './ReportAbuseFormModal';

const ReportAbuseButton = ({ reviewId }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleOpenModal = () => setIsModalOpen(true);
    const handleCloseModal = () => setIsModalOpen(false);

    const handleSubmitReport = async (reason, comment) => {
        console.log(`Submitting report for review ID: ${reviewId}, Reason: ${reason}, Comment: ${comment}`);
        // TODO: Replace with actual API call to backend (US2.3)
        try {
            // const response = await fetch('/api/report-abuse', {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json',
            //     },
            //     body: JSON.stringify({ reviewId, reason, comment, reportingUserId: 'current_user_id' }), // reportingUserId would come from session/auth
            // });

            // if (!response.ok) {
            //     throw new Error('Failed to submit report');
            // }

            console.log('Report submitted successfully!');
            alert('Thank you for reporting this review. We will review it shortly.');
            handleCloseModal();
        } catch (error) {
            console.error('Error submitting report:', error);
            alert('Failed to submit report. Please try again later.');
        }
    };

    return (
        <>
            <button
                className="report-abuse-btn"
                onClick={handleOpenModal}
                aria-label={`Report abuse for review ${reviewId}`}
            >
                Report Abuse
            </button>

            {isModalOpen && (
                <ReportAbuseFormModal
                    reviewId={reviewId}
                    onClose={handleCloseModal}
                    onSubmit={handleSubmitReport}
                />
            )}
        </>
    );
};

export default ReportAbuseButton;

// public/js/components/ReportAbuseFormModal.js
import React, { useState } from 'react';
import './ReportAbuseFormModal.css'; // Basic styling for the modal

const ReportAbuseFormModal = ({ reviewId, onClose, onSubmit }) => {
    const [reason, setReason] = useState('');
    const [comment, setComment] = useState('');
    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        if (!reason) {
            newErrors.reason = 'Please select a reason for reporting.';
        }
        // Add more validation rules as needed
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validateForm()) {
            onSubmit(reason, comment);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h2>Report Review</h2>
                    <button className="close-button" onClick={onClose}>&times;</button>
                </div>
                <div className="modal-body">
                    <p>Reporting review ID: <strong>{reviewId}</strong></p>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="reason">Reason:</label>
                            <select
                                id="reason"
                                value={reason}
                                onChange={(e) => {
                                    setReason(e.target.value);
                                    setErrors(prev => ({ ...prev, reason: '' })); // Clear error on change
                                }}
                                className={errors.reason ? 'is-invalid' : ''}
                            >
                                <option value="">Select a reason</option>
                                <option value="spam">Spam or Advertising</option>
                                <option value="offensive">Offensive Content</option>
                                <option value="fake">Fake Review</option>
                                <option value="irrelevant">Irrelevant Content</option>
                                <option value="other">Other</option>
                            </select>
                            {errors.reason && <div className="error-message">{errors.reason}</div>}
                        </div>
                        <div className="form-group">
                            <label htmlFor="comment">Comments (Optional):</label>
                            <textarea
                                id="comment"
                                rows="4"
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                                placeholder="Provide more details if necessary..."
                            ></textarea>
                        </div>
                        <div className="modal-footer">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button type="submit" className="btn btn-primary">Submit Report</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ReportAbuseFormModal;

// public/css/ReportAbuseFormModal.css (Basic styling)
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-container {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    width: 90%;
    max-width: 500px;
    position: relative;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.modal-header h2 {
    margin: 0;
    font-size: 1.5em;
}

.close-button {
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group select,
.form-group textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box; /* Ensures padding doesn't increase total width */
}

.form-group .is-invalid {
    border-color: red;
}

.error-message {
    color: red;
    font-size: 0.9em;
    margin-top: 5px;
}

.modal-footer {
    border-top: 1px solid #eee;
    padding-top: 15px;
    margin-top: 20px;
    text-align: right;
}

.btn {
    padding: 10px 15px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1em;
    margin-left: 10px;
}

.btn-primary {
    background-color: #007bff;
    color: white;
    border: none;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
    border: none;
}

.report-abuse-btn {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
    margin-top: 10px;
}

.report-abuse-btn:hover {
    background-color: #e0e0e0;
}
