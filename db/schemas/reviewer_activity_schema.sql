-- Schema for Reviewer Activity Database

-- Reviewer Table
CREATE TABLE reviewers (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    reviewer_name VARCHAR(255),
    account_creation_date TIMESTAMP,
    avg_reviews_per_day DECIMAL(10, 2), -- Historical average
    std_dev_reviews_per_day DECIMAL(10, 2), -- Historical standard deviation
    last_activity_timestamp TIMESTAMP
);

-- Product Table
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,
    product_name VARCHAR(255),
    product_category VARCHAR(255),
    seller_id VARCHAR(255)
);

-- Review Table
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    reviewer_id VARCHAR(255) REFERENCES reviewers(reviewer_id),
    product_id VARCHAR(255) REFERENCES products(product_id),
    rating INT,
    review_text TEXT,
    review_timestamp TIMESTAMP,
    is_positive BOOLEAN -- Derived: rating >= 4
);

-- Index for efficient time-series queries on reviews
CREATE INDEX idx_reviews_reviewer_id_timestamp ON reviews (reviewer_id, review_timestamp);
CREATE INDEX idx_reviews_product_id_timestamp ON reviews (product_id, review_timestamp);