CREATE TABLE IF NOT EXISTS flagged_reviews_burst (
    flag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Unique ID for this flag instance
    review_id VARCHAR(255) NOT NULL REFERENCES reviews(review_id), -- Foreign key to the original review
    product_id VARCHAR(255) NOT NULL,
    flagged_by_model VARCHAR(50) NOT NULL DEFAULT 'burst_detection',
    flag_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    burst_type VARCHAR(20), -- 'positive', 'negative', 'mixed'
    current_positive_reviews_short_window INT,
    current_negative_reviews_short_window INT,
    avg_positive_rate_long_window_per_hour NUMERIC(10, 2),
    avg_negative_rate_long_window_per_hour NUMERIC(10, 2),
    flag_reason TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_flagged_burst_product_id ON flagged_reviews_burst (product_id);
CREATE INDEX idx_flagged_burst_flag_timestamp ON flagged_reviews_burst (flag_timestamp);
CREATE INDEX idx_flagged_burst_is_resolved ON flagged_reviews_burst (is_resolved);
