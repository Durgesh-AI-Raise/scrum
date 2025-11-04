document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/flagged_reviews')
        .then(response => response.json())
        .then(reviews => {
            const tableBody = document.querySelector('#flaggedReviewsTable tbody');
            tableBody.innerHTML = ''; // Clear loading message

            if (reviews.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7">No flagged reviews found.</td></tr>';
                return;
            }

            reviews.forEach(review => {
                const row = tableBody.insertRow();
                row.insertCell().textContent = review.review_id;
                row.insertCell().textContent = review.product_id;
                row.insertCell().textContent = review.reviewer_id;
                row.insertCell().textContent = review.rating;
                const reviewTextCell = row.insertCell();
                reviewTextCell.classList.add('review-text-snippet');
                reviewTextCell.textContent = review.review_text;
                row.insertCell().textContent = new Date(review.timestamp).toLocaleString();
                row.insertCell().textContent = review.flagged_reason || 'N/A';
            });
        })
        .catch(error => {
            console.error('Error fetching flagged reviews:', error);
            const tableBody = document.querySelector('#flaggedReviewsTable tbody');
            tableBody.innerHTML = '<tr><td colspan="7">Error loading flagged reviews.</td></tr>';
        });
});