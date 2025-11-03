// FlaggedReviewsDashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Or use native fetch API

const FlaggedReviewsDashboard = () => {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchFlaggedReviews = async () => {
            try {
                // API endpoint for flagged reviews
                const response = await axios.get('/api/flagged-reviews');
                setReviews(response.data);
            } catch (err) {
                setError('Failed to fetch flagged reviews. Please try again later.');
                console.error('Error fetching flagged reviews:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchFlaggedReviews();
    }, []); // Empty dependency array means this runs once on mount

    if (loading) return <div className="loading-message">Loading flagged reviews...</div>;
    if (error) return <div className="error-message">Error: {error}</div>;

    return (
        <div className="dashboard-container">
            <h1>Flagged Reviews Dashboard</h1>
            {reviews.length === 0 ? (
                <p>No flagged reviews found.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Review ID</th>
                            <th>Product ID</th>
                            <th>Reviewer ID</th>
                            <th>Flag Reasons</th>
                            <th>Status</th>
                            <th>Flagged At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reviews.map(review => (
                            <tr key={review.review_id}>
                                <td>{review.review_id}</td>
                                <td>{review.product_id}</td>
                                <td>{review.reviewer_id}</td>
                                <td>{review.flag_reasons ? review.flag_reasons.join(', ') : 'N/A'}</td>
                                <td>{review.manual_status}</td>
                                <td>{new Date(review.flagged_at).toLocaleString()}</td>
                                <td>
                                    <button onClick={() => alert(`Viewing details for ${review.review_id}`)}>View Details</button>
                                    {/* Placeholder for detail view navigation */}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default FlaggedReviewsDashboard;