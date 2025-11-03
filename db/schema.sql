CREATE TABLE reviews (
    review_id UUID PRIMARY KEY,
    reviewer_id VARCHAR(255) NOT NULL,
    ip_address INET,
    device_fingerprint VARCHAR(255),
    review_text TEXT NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    product_asin VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    purchase_history JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Indexing for common query patterns
CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX idx_reviews_product_asin ON reviews (product_asin);
CREATE INDEX idx_reviews_timestamp ON reviews (timestamp);
