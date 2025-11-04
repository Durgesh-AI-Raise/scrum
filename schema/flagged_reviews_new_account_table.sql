CREATE TABLE IF NOT EXISTS flagged_reviews_new_account (
    flag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id VARCHAR(255) NOT NULL REFERENCES reviews(review_id),
    user_id VARCHAR(255) NOT NULL,
    flagged_by_model VARCHAR(50) NOT NULL DEFAULT 'new_account_activity',
    flag_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_review_date TIMESTAMP WITH TIME ZONE,
    review_count_in_window INT,
    distinct_products_in_window INT,
    threshold_review_count INT,
    threshold_distinct_products INT,
    flag_reason TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_flagged_new_account_user_id ON flagged_reviews_new_account (user_id);
CREATE INDEX idx_flagged_new_account_flag_timestamp ON flagged_reviews_new_account (flag_timestamp);
CREATE INDEX idx_flagged_new_account_is_resolved ON flagged_reviews_new_account (is_resolved);
