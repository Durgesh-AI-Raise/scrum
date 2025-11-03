CREATE TABLE ReviewerProfile (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    account_creation_date TIMESTAMP NOT NULL,
    total_reviews_submitted INT DEFAULT 0,
    last_review_timestamp TIMESTAMP,
    reviews_in_last_day INT DEFAULT 0,
    reviews_in_last_week INT DEFAULT 0,
    reviews_in_last_month INT DEFAULT 0,
    unique_products_reviewed_count INT DEFAULT 0,
    recent_review_timestamps JSONB DEFAULT '[]'::jsonb, -- Store timestamps for rapid submission check
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviewer_id ON ReviewerProfile (reviewer_id);
