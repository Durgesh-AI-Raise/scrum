-- Table for storing original review data
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    review_text TEXT NOT NULL,
    rating INT,
    review_date TIMESTAMP NOT NULL,
    -- Add other relevant review metadata as needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing flags related to text abuse
CREATE TYPE text_flag_type AS ENUM (
    'unnatural_phrasing',
    'repeated_keywords',
    'overly_generic_praise',
    'overly_generic_criticism',
    'unrelated_content',
    'other_text_abuse'
);

CREATE TABLE text_abuse_flags (
    flag_id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) NOT NULL REFERENCES reviews(review_id),
    flag_type text_flag_type NOT NULL,
    suspicion_score DECIMAL(5, 4) NOT NULL CHECK (suspicion_score >= 0 AND suspicion_score <= 1),
    detection_details JSONB, -- Store details like matched patterns, keywords, etc.
    is_active BOOLEAN DEFAULT TRUE, -- Flag status (e.g., active, resolved)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient lookup of flags by review and type
CREATE INDEX idx_text_abuse_flags_review_id ON text_abuse_flags (review_id);
CREATE INDEX idx_text_abuse_flags_flag_type ON text_abuse_flags (flag_type);
-- Index for efficient querying by suspicion score (for dashboard prioritization)
CREATE INDEX idx_text_abuse_flags_suspicion_score ON text_abuse_flags (suspicion_score DESC);