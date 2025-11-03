CREATE TABLE flagged_behavioral_patterns (
    flag_id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) NOT NULL, -- Foreign key to the main reviews table or review_behavioral_data
    flag_type VARCHAR(50) NOT NULL,   -- e.g., 'sudden_spike', 'multiple_reviews_ip_device', 'keyword_stuffing', 'external_link'
    severity VARCHAR(20) NOT NULL,    -- e.g., 'low', 'medium', 'high'
    detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB,                    -- Store additional context like spike magnitude, IPs involved, keywords, etc.
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Add a unique constraint to prevent duplicate flags for the same review_id and flag_type
    CONSTRAINT uc_review_flag UNIQUE (review_id, flag_type)
);

CREATE INDEX idx_fbp_review_id ON flagged_behavioral_patterns (review_id);
CREATE INDEX idx_fbp_flag_type ON flagged_behavioral_patterns (flag_type);
CREATE INDEX idx_fbp_detection_timestamp ON flagged_behavioral_patterns (detection_timestamp);
