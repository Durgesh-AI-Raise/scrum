CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    review_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date TIMESTAMP NOT NULL,
    verified_purchase BOOLEAN NOT NULL DEFAULT FALSE,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    flagged_status BOOLEAN DEFAULT FALSE,
    investigation_status VARCHAR(50) DEFAULT 'Pending' CHECK (investigation_status IN ('Pending', 'Abusive', 'Legitimate'))
);

-- Index for faster lookup of flagged reviews
CREATE INDEX idx_reviews_flagged_status ON reviews (flagged_status);