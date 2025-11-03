// frontend/ReviewerHistory.js
import React, { useState, useEffect } from 'react';

function ReviewerHistory({ reviewerId }) {
  const [reviewerDetails, setReviewerDetails] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReviewerData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch reviewer details
        const detailsResponse = await fetch(`http://localhost:5000/api/reviewers/${reviewerId}`);
        const detailsData = await detailsResponse.json();
        if (detailsResponse.ok) {
          setReviewerDetails(detailsData);
        } else {
          throw new Error(detailsData.error || 'Failed to fetch reviewer details');
        }

        // Fetch review history
        const reviewsResponse = await fetch(`http://localhost:5000/api/reviewers/${reviewerId}/reviews`);
        const reviewsData = await reviewsResponse.json();
        if (reviewsResponse.ok) {
          setReviews(reviewsData);
        } else {
          throw new Error(reviewsData.error || 'Failed to fetch reviewer reviews');
        }

        // Fetch purchase history
        const purchasesResponse = await fetch(`http://localhost:5000/api/reviewers/${reviewerId}/purchases`);
        const purchasesData = await purchasesResponse.json();
        if (purchasesResponse.ok) {
          setPurchases(purchasesData);
        } else {
          throw new Error(purchasesData.error || 'Failed to fetch reviewer purchases');
        }

      } catch (err) {
        setError(err.message);
        console.error("Error fetching reviewer history:", err);
      } finally {
        setLoading(false);
      }
    };

    if (reviewerId) {
      fetchReviewerData();
    }
  }, [reviewerId]);

  if (loading) {
    return <div>Loading reviewer history...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  if (!reviewerDetails) {
    return <div>No reviewer data found.</div>;
  }

  return (
    <div className="reviewer-history">
      <h2>Reviewer History for {reviewerDetails.username || `ID: ${reviewerId}`}</h2>

      <h3>Reviewer Details</h3>
      <p><strong>ID:</strong> {reviewerDetails.reviewer_id}</p>
      <p><strong>Username:</strong> {reviewerDetails.username}</p>
      <p><strong>Email:</strong> {reviewerDetails.email}</p>
      <p><strong>Registration Date:</strong> {new Date(reviewerDetails.registration_date).toLocaleDateString()}</p>
      <p><strong>Flagged:</strong> {reviewerDetails.is_flagged ? 'Yes' : 'No'}</p>
      {reviewerDetails.is_flagged && <p><strong>Flag Reason:</strong> {reviewerDetails.flagging_reason}</p>}

      <h3>Reviews Written ({reviews.length})</h3>
      {reviews.length === 0 ? (
        <p>This reviewer has not written any reviews.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Review ID</th>
              <th>Product ID</th>
              <th>Review Text</th>
              <th>Rating</th>
              <th>Date</th>
              <th>Flagged</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => (
              <tr key={review.review_id}>
                <td>{review.review_id}</td>
                <td>{review.product_id}</td>
                <td>{review.review_text.substring(0, 70)}...</td>
                <td>{review.rating}</td>
                <td>{new Date(review.review_date).toLocaleDateString()}</td>
                <td>{review.is_flagged ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Purchase History ({purchases.length})</h3>
      {purchases.length === 0 ? (
        <p>No purchase history found for this reviewer.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Purchase ID</th>
              <th>Product ID</th>
              <th>Date</th>
              <th>Quantity</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {purchases.map((purchase) => (
              <tr key={purchase.purchase_id}>
                <td>{purchase.purchase_id}</td>
                <td>{purchase.product_id}</td>
                <td>{new Date(purchase.purchase_date).toLocaleDateString()}</td>
                <td>{purchase.quantity}</td>
                <td>${purchase.price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ReviewerHistory;