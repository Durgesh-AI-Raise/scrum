// frontend/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import ReviewerHistory from './ReviewerHistory';

function App() {
  const [flaggedReviews, setFlaggedReviews] = useState([]);
  const [selectedReviewerId, setSelectedReviewerId] = useState(null);
  const [filterReason, setFilterReason] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc' or 'desc'

  useEffect(() => {
    fetchFlaggedReviews();
  }, [filterReason, sortBy, sortOrder]);

  const fetchFlaggedReviews = async () => {
    try {
      const params = new URLSearchParams();
      if (filterReason) params.append('reason', filterReason);
      params.append('sort_by', sortBy);
      params.append('order', sortOrder);
      const response = await fetch(`http://localhost:5000/api/flagged-reviews?${params.toString()}`);
      const data = await response.json();
      if (response.ok) {
        setFlaggedReviews(data);
      } else {
        console.error("Error fetching flagged reviews:", data.error);
      }
    } catch (error) {
      console.error("Network error:", error);
    }
  };

  const handleViewReviewerHistory = (reviewerId) => {
    setSelectedReviewerId(reviewerId);
  };

  const handleBackToDashboard = () => {
    setSelectedReviewerId(null);
  };

  if (selectedReviewerId) {
    return (
      <div className="App">
        <button onClick={handleBackToDashboard}>Back to Dashboard</button>
        <ReviewerHistory reviewerId={selectedReviewerId} />
      </div>
    );
  }

  return (
    <div className="App">
      <h1>Review Integrity Dashboard</h1>

      <div className="controls">
        <label>
          Filter by Reason:
          <select value={filterReason} onChange={(e) => setFilterReason(e.target.value)}>
            <option value="">All</option>
            <option value="similar_content">Similar Content</option>
            <option value="high_volume">High Volume</option>
            {/* Add more reasons as they are defined */}
          </select>
        </label>
        <label>
          Sort by:
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="timestamp">Flag Date</option>
            {/* Add more sorting options if needed, e.g., 'rating' */}
          </select>
        </label>
        <label>
          Order:
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </div>

      <h2>Flagged Reviews</h2>
      {flaggedReviews.length === 0 ? (
        <p>No high-risk reviews found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Flag ID</th>
              <th>Review ID</th>
              <th>Reviewer ID</th>
              <th>Review Text</th>
              <th>Rating</th>
              <th>Flag Reason</th>
              <th>Flag Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {flaggedReviews.map((review) => (
              <tr key={review.flag_id}>
                <td>{review.flag_id}</td>
                <td>{review.reviewer_id}</td>
                <td>{review.review_id}</td>
                <td>{review.review_text.substring(0, 50)}...</td>
                <td>{review.rating}</td>
                <td>{review.flagging_reason}</td>
                <td>{new Date(review.flag_timestamp).toLocaleString()}</td>
                <td>{review.status}</td>
                <td>
                  <button onClick={() => handleViewReviewerHistory(review.reviewer_id)}>
                    View Reviewer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;