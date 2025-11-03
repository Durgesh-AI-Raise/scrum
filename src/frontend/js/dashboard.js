document.addEventListener('DOMContentLoaded', () => {
    const flaggedReviewsTableBody = document.querySelector('#flaggedReviewsTableBody');
    const searchInput = document.querySelector('#searchInput');
    const severityFilter = document.querySelector('#severityFilter');
    const applyFiltersButton = document.querySelector('#applyFiltersButton');

    let allFlaggedReviews = []; // Store all reviews fetched from the API

    const fetchFlaggedReviews = async () => {
        try {
            // Placeholder for API call. This endpoint will be implemented in a later task.
            // For now, returning mock data.
            const mockData = [
                {
                    review_id: 'review123',
                    product_id: 'prodA',
                    user_id: 'userX',
                    rating: 1,
                    review_content_snippet: 'This product is terrible...',
                    flagging_reasons: ['Suspicious review velocity for new accounts.'],
                    severity: 'HIGH',
                    flagged_on: '2023-10-27T10:05:00Z'
                },
                {
                    review_id: 'review456',
                    product_id: 'prodB',
                    user_id: 'userY',
                    rating: 5,
                    review_content_snippet: 'Identical content found...',
                    flagging_reasons: ['Identical review content found across multiple reviews.'],
                    severity: 'MEDIUM',
                    flagged_on: '2023-10-27T11:15:20Z'
                },
                {
                    review_id: 'review789',
                    product_id: 'prodC',
                    user_id: 'userZ',
                    rating: 2,
                    review_content_snippet: 'Not worth the price.',
                    flagging_reasons: ['Low rating from new account on new product.'],
                    severity: 'MEDIUM',
                    flagged_on: '2023-10-28T09:30:00Z'
                }
            ];
            allFlaggedReviews = mockData;
            renderFlaggedReviews(allFlaggedReviews);

            // Original fetch call (commented out for mock data)
            // const response = await fetch('/api/flagged-reviews');
            // if (!response.ok) {
            //     throw new Error(`HTTP error! status: ${response.status}`);
            // }
            // allFlaggedReviews = await response.json();
            // renderFlaggedReviews(allFlaggedReviews);

        } catch (error) {
            console.error('Error fetching flagged reviews:', error);
            flaggedReviewsTableBody.innerHTML = '<tr><td colspan="8">Error loading flagged reviews.</td></tr>';
        }
    };

    const renderFlaggedReviews = (reviews) => {
        flaggedReviewsTableBody.innerHTML = ''; // Clear existing rows

        if (reviews.length === 0) {
            flaggedReviewsTableBody.innerHTML = '<tr><td colspan="8">No flagged reviews found.</td></tr>';
            return;
        }

        reviews.forEach(review => {
            const row = flaggedReviewsTableBody.insertRow();
            row.innerHTML = `
                <td>${review.review_id}</td>
                <td>${review.product_id}</td>
                <td>${review.user_id}</td>
                <td>${review.rating}</td>
                <td>${review.review_content_snippet}</td>
                <td>${review.flagging_reasons.join(', ')}</td>
                <td class="severity-${review.severity.toLowerCase()}">${review.severity}</td>
                <td>${new Date(review.flagged_on).toLocaleString()}</td>
            `;
        });
    };

    const applyFilters = () => {
        const searchText = searchInput.value.toLowerCase();
        const selectedSeverity = severityFilter.value;

        const filteredReviews = allFlaggedReviews.filter(review => {
            const matchesSearch = review.review_id.toLowerCase().includes(searchText) ||
                                  review.product_id.toLowerCase().includes(searchText) ||
                                  review.review_content_snippet.toLowerCase().includes(searchText) ||
                                  review.user_id.toLowerCase().includes(searchText);
            const matchesSeverity = selectedSeverity === '' || review.severity === selectedSeverity;
            return matchesSearch && matchesSeverity;
        });
        renderFlaggedReviews(filteredReviews);
    };

    applyFiltersButton.addEventListener('click', applyFilters);
    searchInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            applyFilters();
        }
    });
    severityFilter.addEventListener('change', applyFilters);

    // Initial load
    fetchFlaggedReviews();
});