CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amazon_review_id VARCHAR(255) UNIQUE NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    -- Flags that will be updated by various services
    is_from_fraudulent_account BOOLEAN DEFAULT FALSE,
    fraud_flag_reason TEXT,
    is_suspicious BOOLEAN DEFAULT FALSE,
    suspicious_pattern_id UUID, -- Will reference suspicious_patterns(id)
    is_bot_generated BOOLEAN DEFAULT FALSE,
    bot_detection_reason TEXT,
    is_manually_flagged_abusive BOOLEAN DEFAULT FALSE,
    manual_flag_reason TEXT,
    status VARCHAR(50) DEFAULT 'published' NOT NULL -- e.g., 'published', 'removed', 'pending_investigation'
);

CREATE INDEX idx_reviews_account_id ON reviews (account_id);
CREATE INDEX idx_reviews_product_id ON reviews (product_id);
CREATE INDEX idx_reviews_review_date ON reviews (review_date);
CREATE INDEX idx_reviews_status ON reviews (status);
