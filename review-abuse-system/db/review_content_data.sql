CREATE TABLE review_content_data (
    content_id SERIAL PRIMARY KEY,
    review_id VARCHAR(255) NOT NULL UNIQUE, -- Foreign key to the main reviews table
    review_text TEXT NOT NULL,
    submission_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_rcd_review_id ON review_content_data (review_id);
CREATE INDEX idx_rcd_submission_timestamp ON review_content_data (submission_timestamp);
