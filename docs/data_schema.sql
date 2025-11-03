CREATE TABLE reviews (
    review_id UUID PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    submission_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    review_content TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'removed'
    flagged BOOLEAN DEFAULT FALSE,
    flagged_reason JSONB DEFAULT '[]'::jsonb,
    abuse_score FLOAT DEFAULT 0.0,
    moderator_notes TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_product_time ON reviews (product_id, submission_timestamp DESC);