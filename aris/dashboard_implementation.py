
# aris/frontend/templates/dashboard.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARIS Flagged Reviews Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <header>
        <h1>ARIS Flagged Reviews</h1>
        <nav>
            <!-- Future navigation links -->
        </nav>
    </header>
    <main>
        <div class="dashboard-controls">
            <input type="text" id="search-bar" placeholder="Search by Review ID, User ID, Product ID...">
            <select id="status-filter">
                <option value="">All Statuses</option>
                <option value="PENDING_REVIEW">Pending Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REMOVED">Removed</option>
            </select>
            <button id="apply-filters">Apply Filters</button>
            <button id="refresh-dashboard">Refresh</button>
        </div>
        <div class="flagged-reviews-list">
            <div class="review-card-header">
                <span>Review ID</span>
                <span>Product ID</span>
                <span>User ID</span>
                <span>Flags Triggered</span>
                <span>Severity</span>
                <span>Flagged On</span>
                <span>Status</span>
            </div>
            <div id="reviews-container">
                <!-- Dynamically loaded flagged review cards will go here -->
            </div>
            <div class="pagination">
                <button id="prev-page">Previous</button>
                <span id="page-info">Page 1 of X</span>
                <button id="next-page">Next</button>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2023 Amazon Review Integrity Shield</p>
    </footer>
    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>

# aris/frontend/templates/detailed_review.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARIS Detailed Review - {{ review.original_review.review_id }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <style>
        /* Specific styles for the detailed view if needed, or integrate into main styles.css */
        .detailed-review-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .detailed-review-card h2 {
            color: #232f3e;
            margin-top: 0;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .detailed-review-card p {
            margin-bottom: 10px;
            line-height: 1.6;
        }
        .detailed-review-card strong {
            color: #333;
        }
        .flag-details {
            margin-top: 20px;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }
        .flag-details h3 {
            color: #ff9900;
        }
        .flag {
            background-color: #ffeccf;
            border: 1px solid #ffd790;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .flag p {
            margin: 5px 0;
        }
        .action-buttons {
            margin-top: 20px;
            text-align: right;
        }
        .action-buttons button {
            padding: 10px 20px;
            font-size: 1rem;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            margin-left: 10px;
        }
        .action-buttons .remove-button {
            background-color: #dc3545;
            color: white;
        }
        .action-buttons .remove-button:hover {
            background-color: #c82333;
        }
        .back-button {
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
        }
        .back-button:hover {
            background-color: #5a6268;
        }
    </style>
</head>
<body>
    <header>
        <h1>ARIS Flagged Reviews</h1>
        <nav>
            <a href="/" class="back-button">Back to Dashboard</a>
        </nav>
    </header>
    <main>
        <div class="detailed-review-card">
            <h2>Review ID: {{ review.original_review.review_id }}</h2>
            <p><strong>Status:</strong> <span class="status status-{{ review.status.lower() }}">{{ review.status.replace('_', ' ') }}</span></p>
            <p><strong>Flagged On:</strong> {{ review.timestamp }}</p>
            <p><strong>Product ID:</strong> {{ review.original_review.product_id }}</p>
            <p><strong>User ID:</strong> {{ review.original_review.user_id }}</p>
            <p><strong>IP Address:</strong> {{ review.original_review.ip_address }}</p>
            <p><strong>Review Text:</strong></p>
            <p>"{{ review.original_review.text }}"</p>

            <div class="flag-details">
                <h3>Triggered Flags ({{ review.flags|length }}):</h3>
                {% if review.flags %}
                    {% for flag in review.flags %}
                        <div class="flag">
                            <p><strong>Rule Name:</strong> {{ flag.rule_name }}</p>
                            <p><strong>Rule Type:</strong> {{ flag.rule_type }}</p>
                            <p><strong>Severity:</strong> <span class="severity severity-{{ flag.severity.lower() }}">{{ flag.severity }}</span></p>
                            <p><strong>Triggered At:</strong> {{ flag.triggered_on }}</p>
                            <p><strong>Rule Definition:</strong> {{ flag.rule_definition }}</p>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No specific flags recorded.</p>
                {% endif %}
            </div>

            <!-- Placeholder for additional context (User History, Linked Accounts) -->
            <div class="additional-context">
                <h3>Additional Context:</h3>
                <p><em>(User history and linked accounts will be displayed here in a future task.)</em></p>
                <p><strong>User History (Placeholder):</strong> No user history available.</p>
                <p><strong>Linked Accounts (Placeholder):</strong> No linked accounts found.</p>
            </div>

            <div class="action-buttons">
                <button class="remove-button" data-review-id="{{ review.id }}">Remove Review</button>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2023 Amazon Review Integrity Shield</p>
    </footer>
    <script src="{{ url_for('static', filename='js/detailed_review.js') }}"></script>
</body>
</html>


# aris/frontend/static/js/dashboard.js
document.addEventListener('DOMContentLoaded', () => {
    const reviewsContainer = document.getElementById('reviews-container');
    const searchBar = document.getElementById('search-bar');
    const statusFilter = document.getElementById('status-filter');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const refreshDashboardBtn = document.getElementById('refresh-dashboard');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfoSpan = document.getElementById('page-info');

    let currentPage = 1;
    const itemsPerPage = 10;

    async function fetchFlaggedReviews(page = 1, filters = {}) {
        const queryParams = new URLSearchParams();
        queryParams.append('page', page);
        queryParams.append('limit', itemsPerPage);

        if (filters.search) {
            queryParams.append('search', filters.search);
        }
        if (filters.status) {
            queryParams.append('status', filters.status);
        }

        try {
            const response = await fetch(`/api/flagged-reviews?${queryParams.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderFlaggedReviews(data.reviews);
            updatePagination(data.total_pages);
        } catch (error) {
            console.error("Error fetching flagged reviews:", error);
            reviewsContainer.innerHTML = '<p class="error-message">Failed to load flagged reviews.</p>';
        }
    }

    function renderFlaggedReviews(reviews) {
        reviewsContainer.innerHTML = '';
        if (reviews.length === 0) {
            reviewsContainer.innerHTML = '<p class="no-reviews-message">No flagged reviews found.</p>';
            return;
        }

        reviews.forEach(review => {
            const reviewCard = document.createElement('div');
            reviewCard.classList.add('review-card');
            reviewCard.dataset.reviewId = review.id; // Store review ID for later use

            const flagNames = review.flags.map(flag => flag.rule_name).join(', ') || 'N/A';
            const severities = review.flags.map(flag => flag.severity);
            const highestSeverity = severities.length > 0 ? Math.max(...severities.map(s => {
                if (s === 'high') return 3;
                if (s === 'medium') return 2;
                if (s === 'low') return 1;
                return 0; // Default or unknown
            })) : 0;
            const highestSeverityString = highestSeverity === 3 ? 'High' : (highestSeverity === 2 ? 'Medium' : (highestSeverity === 1 ? 'Low' : 'N/A'));


            reviewCard.innerHTML = `
                <span class="review-id">${review.original_review.review_id}</span>
                <span class="product-id">${review.original_review.product_id}</span>
                <span class="user-id">${review.original_review.user_id}</span>
                <span class="flags">${flagNames}</span>
                <span class="severity severity-${highestSeverityString.toLowerCase()}">${highestSeverityString}</span>
                <span class="flagged-on">${new Date(review.timestamp).toLocaleString()}</span>
                <span class="status status-${review.status.toLowerCase()}">${review.status.replace('_', ' ')}</span>
            `;
            reviewCard.addEventListener('click', () => {
                window.location.href = `/flagged-reviews/${review.id}`; // Navigate to detailed view
            });
            reviewsContainer.appendChild(reviewCard);
        });
    }

    function updatePagination(totalPages) {
        pageInfoSpan.textContent = `Page ${currentPage} of ${totalPages}`;
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage >= totalPages;
    }

    applyFiltersBtn.addEventListener('click', () => {
        const filters = {
            search: searchBar.value.trim(),
            status: statusFilter.value
        };
        currentPage = 1;
        fetchFlaggedReviews(currentPage, filters);
    });

    refreshDashboardBtn.addEventListener('click', () => {
        searchBar.value = '';
        statusFilter.value = '';
        currentPage = 1;
        fetchFlaggedReviews(currentPage, {});
    });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            const filters = {
                search: searchBar.value.trim(),
                status: statusFilter.value
            };
            fetchFlaggedReviews(currentPage, filters);
        }
    });

    nextPageBtn.addEventListener('click', () => {
        currentPage++;
        const filters = {
            search: searchBar.value.trim(),
            status: statusFilter.value
        };
        fetchFlaggedReviews(currentPage, filters);
    });

    fetchFlaggedReviews(currentPage, {}); // Initial load
});


# aris/frontend/static/js/detailed_review.js
document.addEventListener('DOMContentLoaded', () => {
    const removeButton = document.querySelector('.remove-button');

    if (removeButton) {
        removeButton.addEventListener('click', async () => {
            const reviewId = removeButton.dataset.reviewId;
            if (confirm(`Are you sure you want to remove review ${reviewId}?`)) {
                try {
                    // This will be implemented in Task 4.x
                    alert(`Review ${reviewId} removal functionality is not yet implemented (Task 4.x).`);
                    // const response = await fetch(`/api/reviews/${reviewId}/remove`, {
                    //     method: 'POST', // Or DELETE, depending on API design
                    // });

                    // if (!response.ok) {
                    //     throw new Error(`HTTP error! status: ${response.status}`);
                    // }

                    // alert(`Review ${reviewId} successfully removed.`);
                    // window.location.href = '/'; // Go back to dashboard
                } catch (error) {
                    console.error("Error removing review:", error);
                    alert("Failed to remove review. Please try again.");
                }
            }
        });
    }
});


# aris/frontend/static/css/styles.css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f4f4f4;
    color: #333;
}

header {
    background-color: #232f3e;
    color: white;
    padding: 1rem 2rem;
    text-align: center;
}

main {
    padding: 1rem 2rem;
    max-width: 1200px;
    margin: 20px auto;
    background-color: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
}

h1 {
    color: #333;
    text-align: center;
    margin-bottom: 1.5rem;
}

.dashboard-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
    align-items: center;
}

.dashboard-controls input[type="text"],
.dashboard-controls select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
    flex-grow: 1;
    min-width: 150px;
}

.dashboard-controls button {
    padding: 8px 15px;
    background-color: #ff9900;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.dashboard-controls button:hover {
    background-color: #e68a00;
}

.flagged-reviews-list {
    margin-top: 20px;
}

.review-card-header, .review-card {
    display: grid;
    grid-template-columns: 0.8fr 1fr 0.8fr 1.5fr 0.6fr 1.2fr 0.8fr; /* Adjusted for better spacing */
    gap: 10px;
    padding: 10px 15px;
    align-items: center;
    border-bottom: 1px solid #eee;
}

.review-card-header {
    font-weight: bold;
    background-color: #f9f9f9;
    border-top: 1px solid #eee;
}

.review-card {
    background-color: white;
    transition: background-color 0.2s;
    cursor: pointer;
}

.review-card:hover {
    background-color: #f0f8ff;
}

.review-card:last-child {
    border-bottom: none;
}

.status {
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 0.85rem;
    font-weight: bold;
    text-align: center;
}

.status-pending_review {
    background-color: #fff3cd;
    color: #856404;
}

.status-approved {
    background-color: #d4edda;
    color: #155724;
}

.status-removed {
    background-color: #f8d7da;
    color: #721c24;
}

.severity-high {
    color: #dc3545; /* Red */
    font-weight: bold;
}

.severity-medium {
    color: #ffc107; /* Orange */
}

.severity-low {
    color: #17a2b8; /* Cyan */
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #eee;
}

.pagination button {
    padding: 8px 15px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.pagination button:hover:not(:disabled) {
    background-color: #0056b3;
}

.pagination button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}

.no-reviews-message, .error-message {
    text-align: center;
    padding: 20px;
    font-style: italic;
    color: #666;
}

footer {
    text-align: center;
    padding: 1.5rem;
    color: #666;
    font-size: 0.85rem;
    margin-top: 30px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .review-card-header, .review-card {
        grid-template-columns: 1fr 1fr; /* Stack relevant info on smaller screens */
    }

    .dashboard-controls {
        flex-direction: column;
        align-items: stretch;
    }

    .dashboard-controls input[type="text"],
    .dashboard-controls select,
    .dashboard-controls button {
        width: 100%;
    }
}


# aris/api/dashboard_api.py
from flask import Flask, jsonify, request, render_template, send_from_directory
from aris.repositories.flagged_review_repository import InMemoryFlaggedReviewRepository
from aris.rule_engine.rule_engine import RuleEngine
from aris.services.flagging_service import FlaggingService
from aris.data_models.review_data import ReviewData
from aris.data_models.flagged_review import FlaggedReview # Import for type hinting/dummy data
from datetime import datetime, timedelta
import uuid
import math

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Initialize components globally for simplicity in this prototype.
# In a real application, these would be managed via dependency injection.
review_repo = InMemoryFlaggedReviewRepository()
rule_engine = RuleEngine() # This loads hardcoded rules for now (from Task 1.3)
flagging_service = FlaggingService(rule_engine, review_repo)

# --- Dummy Data Generation for Dashboard Testing ---
def generate_dummy_flagged_reviews(count=50):
    if len(review_repo.get_all_flagged_reviews()) > 0:
        print("Dummy data already exists, skipping generation.")
        return

    print(f"Generating {count} dummy flagged reviews...")
    for i in range(count):
        review_id = f"dummy-rev-{str(uuid.uuid4())[:8]}"
        user_id = f"user_{i % 5 + 1}" # 5 distinct users
        product_id = f"product_{i % 10 + 1}" # 10 distinct products
        ip_address = f"192.168.1.{i % 255}"
        text = f"This is dummy review number {i}. It talks about a {product_id}. The user {user_id} posted it."
        timestamp = datetime.now() - timedelta(hours=i * 3) # Reviews spread over time

        dummy_review_data = ReviewData(review_id, user_id, product_id, ip_address, text, timestamp)

        flags = []
        if i % 3 == 0:
            flags.append({
                "rule_id": "rule-1",
                "rule_name": "Suspicious IP Address",
                "rule_type": "IP_MATCH",
                "severity": "high",
                "triggered_on": (timestamp + timedelta(minutes=1)).isoformat(),
                "rule_definition": {"ips": ["192.168.1.100", ip_address]} # Make some IPs match
            })
        if i % 5 == 0:
            flags.append({
                "rule_id": "rule-2",
                "rule_name": "Profanity in Review",
                "rule_type": "KEYWORD_MATCH",
                "severity": "medium",
                "triggered_on": (timestamp + timedelta(minutes=2)).isoformat(),
                "rule_definition": {"keywords": ["badword", "scam", "fraud"], "match_any": True}
            })
        if i % 7 == 0:
             flags.append({
                "rule_id": "rule-3",
                "rule_name": "Rapid Posting (Placeholder)",
                "rule_type": "RAPID_REVIEW",
                "severity": "low",
                "triggered_on": (timestamp + timedelta(minutes=3)).isoformat(),
                "rule_definition": {"max_reviews": 5, "time_window_minutes": 60, "group_by": "user_id"}
            })

        if flags:
            # Manually create FlaggedReview to set status for variety more easily
            flagged_review_obj = FlaggedReview(original_review=dummy_review_data, flags=flags, timestamp=timestamp)

            if i % 7 == 0:
                flagged_review_obj.status = "APPROVED"
            elif i % 11 == 0:
                flagged_review_obj.status = "REMOVED"
            else:
                flagged_review_obj.status = "PENDING_REVIEW"
            review_repo.add_flagged_review(flagged_review_obj)
        else:
            # Simulate some reviews that pass without flagging
            pass # No need to store if not flagged for this dashboard

    print("Dummy data generation complete.")

generate_dummy_flagged_reviews(50) # Generate 50 dummy reviews on startup

# --- Routes ---

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/flagged-reviews', methods=['GET'])
def get_flagged_reviews_api():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search_query = request.args.get('search', '').lower()
    status_filter = request.args.get('status', '').upper()

    all_reviews = review_repo.get_all_flagged_reviews()
    filtered_reviews = []

    for review in all_reviews:
        match = True
        
        # Filter by status
        if status_filter and review.status != status_filter:
            match = False
        
        # Filter by search query across multiple fields
        if search_query:
            found_in_fields = False
            if search_query in review.original_review.review_id.lower(): found_in_fields = True
            if search_query in review.original_review.user_id.lower(): found_in_fields = True
            if search_query in review.original_review.product_id.lower(): found_in_fields = True
            if search_query in review.original_review.text.lower(): found_in_fields = True
            if any(search_query in flag['rule_name'].lower() for flag in review.flags): found_in_fields = True
            
            if not found_in_fields:
                match = False

        if match:
            filtered_reviews.append(review)

    # Sort reviews by timestamp, descending (most recent first)
    filtered_reviews.sort(key=lambda r: r.timestamp, reverse=True)

    # Implement pagination
    total_reviews = len(filtered_reviews)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_reviews = filtered_reviews[start_index:end_index]

    total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else 1

    return jsonify({
        "reviews": [r.to_dict() for r in paginated_reviews],
        "total_reviews": total_reviews,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit
    })

@app.route('/flagged-reviews/<string:review_id>', methods=['GET'])
def get_detailed_flagged_review_page(review_id):
    # This route will render the detailed review page (User Story 3)
    flagged_review = review_repo.get_flagged_review_by_id(review_id)
    if flagged_review:
        return render_template('detailed_review.html', review=flagged_review.to_dict())
    else:
        return "Review not found", 404

# A simple API endpoint to get a single flagged review's data (for detailed view AJAX)
@app.route('/api/flagged-reviews/<string:review_id>', methods=['GET'])
def get_single_flagged_review_api(review_id):
    flagged_review = review_repo.get_flagged_review_by_id(review_id)
    if flagged_review:
        return jsonify(flagged_review.to_dict())
    else:
        return jsonify({"message": "Flagged review not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
