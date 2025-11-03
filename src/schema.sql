CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) NOT NULL,
    reviewer_id VARCHAR(50) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    submission_date TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_purchase BOOLEAN NOT NULL
);