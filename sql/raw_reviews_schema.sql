-- raw_reviews_schema.sql
CREATE TABLE IF NOT EXISTS raw_reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    review_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    rating INTEGER,
    title TEXT,
    content TEXT,
    source_ip INET,
    country VARCHAR(10),
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_raw_reviews_product_id ON raw_reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_raw_reviews_reviewer_id ON raw_reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS idx_raw_reviews_timestamp ON raw_reviews (review_timestamp);