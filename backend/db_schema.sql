CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    review_content TEXT NOT NULL,
    submission_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET NOT NULL,
    review_content_hash VARCHAR(64) NOT NULL, -- SHA256 hash of review_content
    is_flagged BOOLEAN DEFAULT FALSE,
    flagging_reason JSONB, -- Stores an array of JSON objects for multiple reasons
    severity_score INTEGER DEFAULT 0,
    is_abusive BOOLEAN DEFAULT FALSE,
    is_legitimate BOOLEAN DEFAULT FALSE,
    moderator_id VARCHAR(255),
    moderator_action_timestamp TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reviews_product_id ON reviews (product_id);
CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX idx_reviews_submission_timestamp ON reviews (submission_timestamp);
CREATE INDEX idx_reviews_ip_address ON reviews (ip_address);
CREATE INDEX idx_reviews_content_hash ON reviews (review_content_hash);
CREATE INDEX idx_reviews_is_flagged ON reviews (is_flagged);

CREATE TABLE moderator_action_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    moderator_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- e.g., 'REMOVE', 'MARK_LEGITIMATE'
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT,
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

CREATE INDEX idx_mod_action_review_id ON moderator_action_log (review_id);
CREATE INDEX idx_mod_action_moderator_id ON moderator_action_log (moderator_id);

CREATE TABLE reviewer_history (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    total_reviews_submitted INTEGER DEFAULT 0,
    total_flagged_reviews INTEGER DEFAULT 0,
    total_abusive_reviews INTEGER DEFAULT 0,
    last_flagged_timestamp TIMESTAMP WITH TIME ZONE,
    last_abusive_timestamp TIMESTAMP WITH TIME ZONE
);