
-- SQL DDL for ARIS Review Data Model (PostgreSQL)

-- Table: products
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_category VARCHAR(255),
    product_description TEXT,
    average_rating NUMERIC(2, 1) DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: reviewers
CREATE TABLE reviewers (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_date TIMESTAMP WITH TIME ZONE,
    total_reviews_written INTEGER DEFAULT 0,
    purchase_history_correlated BOOLEAN DEFAULT FALSE, -- To be integrated later
    is_new_account BOOLEAN DEFAULT TRUE, -- Flag for anomaly detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enum for moderation status
CREATE TYPE moderation_status_enum AS ENUM ('pending', 'approved', 'abusive', 'removed');

-- Table: reviews
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL REFERENCES products(product_id),
    reviewer_id VARCHAR(255) NOT NULL REFERENCES reviewers(reviewer_id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT NOT NULL,
    review_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sentiment_score NUMERIC(4, 3), -- Optional, for future use
    is_flagged_for_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT[], -- Array of strings for multiple reasons
    moderation_status moderation_status_enum DEFAULT 'pending',
    moderator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_reviews_product_id ON reviews(product_id);
CREATE INDEX idx_reviews_reviewer_id ON reviews(reviewer_id);
CREATE INDEX idx_reviews_is_flagged_for_anomaly ON reviews(is_flagged_for_anomaly);
CREATE INDEX idx_reviews_moderation_status ON reviews(moderation_status);
CREATE INDEX idx_reviewers_registration_date ON reviewers(registration_date);
