CREATE TABLE review_behavioral_data (
    behavior_id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) NOT NULL UNIQUE, -- Foreign key to the main reviews table
    reviewer_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    ip_address INET,
    submission_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rbd_reviewer_id ON review_behavioral_data (reviewer_id);
CREATE INDEX idx_rbd_device_id ON review_behavioral_data (device_id);
CREATE INDEX idx_rbd_ip_address ON review_behavioral_data (ip_address);
CREATE INDEX idx_rbd_submission_timestamp ON review_behavioral_data (submission_timestamp);
