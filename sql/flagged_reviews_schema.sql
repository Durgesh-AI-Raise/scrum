-- flagged_reviews_schema.sql
CREATE TABLE IF NOT EXISTS flagged_reviews (
    flag_id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) UNIQUE NOT NULL REFERENCES raw_reviews(review_id),
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    review_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT,
    flagging_reason TEXT NOT NULL,
    flagging_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    risk_score DECIMAL(5, 2) DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'PENDING_REVIEW'
);

CREATE INDEX IF NOT EXISTS idx_flagged_reviews_product_id ON flagged_reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_flagged_reviews_reviewer_id ON flagged_reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS idx_flagged_reviews_timestamp ON flagged_reviews (flagging_timestamp);
CREATE INDEX IF NOT EXISTS idx_flagged_reviews_risk_score ON flagged_reviews (risk_score);