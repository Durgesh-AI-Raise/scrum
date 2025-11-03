-- src/database/db_schema.sql

-- Table for storing raw Amazon review data
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL,
    title TEXT,
    comment TEXT NOT NULL,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    source_ip INET, -- Stores IPv4 or IPv6 addresses
    is_vine_review BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    -- Fields for flagging and moderation (to be added in subsequent tasks)
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    flag_severity VARCHAR(50), -- e.g., 'low', 'medium', 'high', 'critical'
    flag_type TEXT, -- e.g., 'duplicate_content', 'blocked_ip', 'excessive_keywords', 'manual_spam'
    status VARCHAR(50) DEFAULT 'ingested', -- e.g., 'ingested', 'pending_review', 'actioned', 'dismissed'
    abuse_type VARCHAR(50), -- e.g., 'spam', 'fake', 'offensive' (manual flagging)
    action_taken VARCHAR(50), -- e.g., 'removed', 'hidden', 'marked_legitimate'
    action_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_reviews_product_id ON reviews (product_id);
CREATE INDEX idx_reviews_user_id ON reviews (user_id);
CREATE INDEX idx_reviews_is_flagged ON reviews (is_flagged);
CREATE INDEX idx_reviews_status ON reviews (status);


-- Table for dynamic heuristic rules configuration
CREATE TABLE heuristic_rules (
    rule_id VARCHAR(255) PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    rule_description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- e.g., 'duplicate_content', 'blocked_ip', 'keyword_excess'
    rule_config JSONB, -- JSON configuration for the rule (e.g., {'threshold': 3} for keywords)
    is_active BOOLEAN DEFAULT TRUE,
    severity VARCHAR(50) NOT NULL DEFAULT 'medium', -- e.g., 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing known blocked IP addresses (for 'blocked_ip' heuristic)
CREATE TABLE blocked_ips (
    ip_address INET PRIMARY KEY,
    reason TEXT,
    blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);