// src/web/app.js

const MODERATION_API_BASE_URL = 'http://localhost:5000'; // Replace with actual API URL or proxy

let lastEvaluatedKey = null; // For pagination
let currentFilters = {}; // To store current filter/sort settings

async function fetchFlaggedReviews(startKey = null) {
    const minConfidence = parseFloat(document.getElementById('minConfidence').value) / 100;
    const maxConfidence = parseFloat(document.getElementById('maxConfidence').value) / 100;
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;

    let url = `${MODERATION_API_BASE_URL}/flagged-reviews?limit=10`;
    url += `&min_confidence=${minConfidence}`;
    url += `&max_confidence=${maxConfidence}`;
    url += `&sort_by=${sortBy}`;
    url += `&sort_order=${sortOrder}`;

    if (startKey) {
        url += `&last_evaluated_key=${encodeURIComponent(JSON.stringify(startKey))}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        renderReviews(data.items);
        lastEvaluatedKey = data.last_evaluated_key;
        document.getElementById('next-page-btn').disabled = !lastEvaluatedKey;
    } catch (error) {
        console.error("Failed to fetch flagged reviews:", error);
        document.getElementById('reviews-list').innerHTML = `<p class="no-reviews" style="color: red;">Error loading reviews: ${error.message}</p>`;
    }
}

function renderReviews(reviews) {
    const reviewsList = document.getElementById('reviews-list');
    reviewsList.innerHTML = ''; // Clear previous reviews

    if (reviews.length === 0) {
        reviewsList.innerHTML = '<p class="no-reviews">No flagged reviews found matching criteria.</p>';
        return;
    }

    reviews.forEach(review => {
        const reviewCard = document.createElement('div');
        reviewCard.className = 'review-card';
        // Get a placeholder moderator ID (in a real app, this would come from auth context)
        const moderatorId = 'mod-alpha'; 

        reviewCard.innerHTML = `
            <h3>Flagged Review: ${review.reviewId}</h3>
            <p><strong>Product ID:</strong> ${review.productId}</p>
            <p><strong>Reviewer ID:</strong> ${review.reviewerId}</p>
            <p><strong>Confidence Score:</strong> ${(review.confidenceScore * 100).toFixed(0)}%</p>
            <p><strong>Current Status:</strong> ${review.moderatorStatus || 'PENDING_REVIEW'}</p>
            <p><strong>Review Text:</strong> ${review.reviewText}</p>
            <p><strong>Flagging Reasons:</strong></p>
            <ul>
                ${review.flaggingReasons.map(reason => `<li><span class="reason-tag">${reason.ruleName}</span> - ${reason.reason}</li>`).join('')}
            </ul>
            <div class="actions">
                <button onclick="updateReviewStatus('${review.reviewId}', 'ABUSE_CONFIRMED', '${moderatorId}')">Abuse Confirmed</button>
                <button onclick="updateReviewStatus('${review.reviewId}', 'FALSE_POSITIVE', '${moderatorId}')">False Positive</button>
                <button onclick="triggerReviewAction('${review.reviewId}', 'REMOVE_REVIEW', 'Moderator confirmed abuse and requested removal', '${moderatorId}')">Remove Review</button>
                <button onclick="triggerReviewAction('${review.reviewId}', 'BAN_REVIEWER', 'Moderator confirmed repeated abuse', '${moderatorId}')">Ban Reviewer</button>
                <button onclick="updateReviewStatus('${review.reviewId}', 'UNDER_INVESTIGATION', '${moderatorId}')">Under Investigation</button>
            </div>
        `;
        reviewsList.appendChild(reviewCard);
    });
}

function setupPagination() {
    document.getElementById('prev-page-btn').addEventListener('click', () => {
        // For DynamoDB pagination with ExclusiveStartKey, going 'previous' is non-trivial
        // and usually involves storing a history of LastEvaluatedKeys.
        // For this MVP, we will only implement 'next' or a full reset.
        alert("Going to previous page is not directly supported with current DynamoDB pagination strategy for this MVP. Please use filters or refresh.");
        // As an alternative, one could refetch from start without lastEvaluatedKey
        lastEvaluatedKey = null;
        fetchFlaggedReviews(null); // Reset to first page
    });

    document.getElementById('next-page-btn').addEventListener('click', () => {
        fetchFlaggedReviews(lastEvaluatedKey);
    });
}

// Functions for filtering and sorting
function applyFilters() {
    document.getElementById('minConfidenceValue').textContent = `${document.getElementById('minConfidence').value}%`;
    document.getElementById('maxConfidenceValue').textContent = `${document.getElementById('maxConfidence').value}%`;

    // Reset pagination when filters change
    lastEvaluatedKey = null;
    fetchFlaggedReviews(null);
}

function resetFilters() {
    document.getElementById('minConfidence').value = 0;
    document.getElementById('maxConfidence').value = 100;
    document.getElementById('sortBy').value = 'lastFlaggedAt';
    document.getElementById('sortOrder').value = 'DESC';
    applyFilters();
}

// Functions for moderator actions
async function updateReviewStatus(reviewId, newStatus, moderatorId) {
    const url = `${MODERATION_API_BASE_URL}/reviews/${reviewId}/status`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus, moderatorId: moderatorId })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Review ${reviewId} status updated to ${newStatus}`, data);
        alert(`Review ${reviewId} status updated to ${newStatus}.`);
        // Re-fetch reviews to update the dashboard, resetting pagination
        lastEvaluatedKey = null;
        fetchFlaggedReviews(null);
    } catch (error) {
        console.error(`Failed to update status for review ${reviewId}:`, error);
        alert(`Error updating status for review ${reviewId}: ${error.message}`);
    }
}

async function triggerReviewAction(reviewId, actionType, actionDetails, moderatorId) {
    const url = `${MODERATION_API_BASE_URL}/reviews/${reviewId}/actions`;
    if (confirm(`Are you sure you want to perform ${actionType} on review ${reviewId}?`)) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ actionType: actionType, actionDetails: actionDetails, moderatorId: moderatorId })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(`Action ${actionType} triggered for review ${reviewId}`, data);
            alert(`${actionType} action successful for review ${reviewId}.`);
            // Re-fetch reviews if status might have changed, or just update UI locally
            lastEvaluatedKey = null;
            fetchFlaggedReviews(null);
        } catch (error) {
            console.error(`Failed to trigger action ${actionType} for review ${reviewId}:`, error);
            alert(`Error triggering action ${actionType} for review ${reviewId}: ${error.message}`);
        }
    }
}

// Initial setup when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('root');
    root.innerHTML = `
        <div class="container">
            <h1>Review Abuse Moderator Dashboard</h1>

            <div class="filters">
                <label for="minConfidence">Min Confidence:</label>
                <input type="range" id="minConfidence" min="0" max="100" value="0" onchange="applyFilters()">
                <span id="minConfidenceValue">0%</span>

                <label for="maxConfidence">Max Confidence:</label>
                <input type="range" id="maxConfidence" min="0" max="100" value="100" onchange="applyFilters()">
                <span id="maxConfidenceValue">100%</span>

                <label for="sortBy">Sort By:</label>
                <select id="sortBy" onchange="applyFilters()">
                    <option value="lastFlaggedAt">Date Flagged</option>
                    <option value="confidenceScore">Confidence Score</option>
                </select>

                <label for="sortOrder">Order:</label>
                <select id="sortOrder" onchange="applyFilters()">
                    <option value="DESC">Descending</option>
                    <option value="ASC">Ascending</option>
                </select>
                <button onclick="resetFilters()">Reset Filters</button>
            </div>

            <div class="reviews-list" id="reviews-list">
                <p class="no-reviews">Loading flagged reviews...</p>
            </div>
            <div class="pagination">
                <button id="prev-page-btn" disabled>Previous</button>
                <button id="next-page-btn">Next</button>
            </div>
        </div>
    `;
    applyFilters(); // Initial fetch with default filters
    setupPagination();
});
