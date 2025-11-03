
-- Table: reviewers
-- Stores information about Amazon reviewers.
CREATE TABLE reviewers (
    reviewer_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the reviewer
    name VARCHAR(255),                  -- Reviewer's display name
    profile_url TEXT,                   -- URL to the reviewer's profile
    total_reviews INT DEFAULT 0,        -- Total reviews posted by this reviewer (can be updated)
    avg_rating DECIMAL(2,1),            -- Average rating given by this reviewer (can be updated)
    account_creation_date DATE          -- Date the reviewer's account was created
);

-- Table: products
-- Stores information about Amazon products.
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the product
    product_name TEXT,                  -- Name of the product
    product_url TEXT,                   -- URL to the product page
    category VARCHAR(255),              -- Product category (e.g., "Electronics", "Books")
    brand VARCHAR(255),                 -- Product brand
    avg_rating DECIMAL(2,1),            -- Current average rating of the product (can be updated)
    total_reviews INT DEFAULT 0,        -- Total reviews for this product (can be updated)
    release_date DATE,                  -- Product release date
    seller_id VARCHAR(255)              -- Placeholder for seller if needed later (not a FK in this sprint)
);

-- Table: reviews
-- Stores individual Amazon product reviews and their associated flags/metadata.
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,             -- Unique identifier for the review
    product_id VARCHAR(255) REFERENCES products(product_id), -- Foreign key to products table
    reviewer_id VARCHAR(255) REFERENCES reviewers(reviewer_id), -- Foreign key to reviewers table
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5), -- Rating given (1-5 stars)
    review_title TEXT,                              -- Title of the review
    review_text TEXT NOT NULL,                      -- Full text of the review
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,  -- Date and time the review was posted
    is_verified_purchase BOOLEAN,                   -- True if it's a verified purchase
    helpful_votes INT DEFAULT 0,                    -- Number of helpful votes received
    abuse_flags_count INT DEFAULT 0,                -- Counter for system-generated abuse flags
    sentiment_score DECIMAL(3,2),                   -- Sentiment score (-1.0 to 1.0, to be filled by Task 1.3)
    keywords_detected TEXT[],                       -- Array of abuse-related keywords found (to be filled by Task 1.3)
    is_flagged_auto BOOLEAN DEFAULT FALSE,          -- True if flagged by an automated rule
    is_flagged_manual BOOLEAN DEFAULT FALSE,        -- True if manually flagged by an analyst
    manual_flag_notes TEXT                          -- Notes added during manual flagging
);

-- Indexes for performance on common lookups and filtering
CREATE INDEX idx_reviews_product_id ON reviews (product_id);
CREATE INDEX idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX idx_reviews_review_date ON reviews (review_date DESC); -- For most recent reviews
CREATE INDEX idx_reviews_is_flagged_auto ON reviews (is_flagged_auto);
CREATE INDEX idx_reviews_is_flagged_manual ON reviews (is_flagged_manual);
