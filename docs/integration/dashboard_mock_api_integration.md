```javascript
// backend/mock-api/server.js (Pseudocode for Mock API)
const express = require('express');
const cors = require('cors');
const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

const mockReviews = [
    {
        reviewId: 'REV001', reviewerId: 'USR001', reviewerName: 'John Doe',
        productAsin: 'B001', reviewContent: 'This product is amazing...', rating: 5,
        detectionType: 'Similar Content', similarityScore: 0.98, status: 'Pending'
    },
    {
        reviewId: 'REV002', reviewerId: 'USR002', reviewerName: 'Jane Smith',
        productAsin: 'B002', reviewContent: 'Horrible experience, do not buy.', rating: 1,
        detectionType: 'Suspicious Activity', status: 'Pending'
    },
    {
        reviewId: 'REV003', reviewerId: 'USR003', reviewerName: 'Alice Wonderland',
        productAsin: 'B003', reviewContent: 'Good value for money.', rating: 4,
        detectionType: 'None', status: 'Actioned'
    },
];

app.get('/api/reviews', (req, res) => {
    console.log('Fetching mock reviews...');
    res.json(mockReviews);
});

app.listen(port, () => {
    console.log(`Mock API listening at http://localhost:${port}`);
});
```

```jsx
// frontend/src/components/Dashboard.js (Updated Pseudocode)
import React, { useState, useEffect } from 'react';

const Dashboard = () => {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchReviews = async () => {
            try {
                const response = await fetch('http://localhost:3001/api/reviews'); // Assuming mock API runs on port 3001
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setReviews(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchReviews();
    }, []);

    if (loading) return <div>Loading reviews...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <h1>Abusive Reviews Dashboard</h1>
            {/* Filter and Search Bar Placeholder */}
            <div className="filter-bar">
                <input type="text" placeholder="Search..." />
                <select>
                    <option>All Detection Types</option>
                    <option>Similar Content</option>
                </select>
                <button>Apply Filters</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Review ID</th>
                        <th>Reviewer Name</th>
                        <th>Product ASIN</th>
                        <th>Content Snippet</th>
                        <th>Rating</th>
                        <th>Detection Type</th>
                        <th>Similarity Score</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {reviews.map(review => (
                        <tr key={review.reviewId}>
                            <td>{review.reviewId}</td>
                            <td>{review.reviewerName}</td>
                            <td>{review.productAsin}</td>
                            <td>{review.reviewContent.substring(0, 50)}...</td>
                            <td>{review.rating}</td>
                            <td>{review.detectionType}</td>
                            <td>{review.similarityScore || 'N/A'}</td>
                            <td>{review.status}</td>
                            <td>
                                <button onClick={() => alert(`View details for ${review.reviewId}`)}>View</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Dashboard;
```
