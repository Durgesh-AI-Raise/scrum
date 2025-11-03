// frontend/src/components/ReviewFlagButton.js
import React, { useState } from 'react';

const ReviewFlagButton = ({ reviewId, initialIsFlagged }) => {
  const [isFlagged, setIsFlagged] = useState(initialIsFlagged);

  const handleClick = () => {
    // This will trigger the backend call in Task 4
    console.log(`Review ${reviewId} clicked to be ${isFlagged ? 'unflagged' : 'flagged'}`);
    // For design purposes, we'll just toggle the state visually
    setIsFlagged(!isFlagged);
  };

  return (
    <button
      onClick={handleClick}
      style={{
        backgroundColor: isFlagged ? '#e74c3c' : '#3498db',
        color: 'white',
        padding: '8px 12px',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        marginLeft: '10px'
      }}
    >
      {isFlagged ? 'Flagged' : 'Flag as Suspicious'}
    </button>
  );
};

export default ReviewFlagButton;

// Example usage in an existing ReviewCard component
/*
import ReviewFlagButton from './ReviewFlagButton';

const ReviewCard = ({ review }) => {
  return (
    <div style={{ border: '1px solid #ccc', padding: '15px', margin: '10px', borderRadius: '8px' }}>
      <h3>Review by {review.reviewerName}</h3>
      <p>{review.text}</p>
      <p>Product: {review.productName}</p>
      <ReviewFlagButton reviewId={review.id} initialIsFlagged={review.isSuspicious} />
    </div>
  );
};
*/