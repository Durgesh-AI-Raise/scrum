
-- Schema for ReviewVelocity (US1.1.1)
CREATE TABLE ReviewVelocity (
    product_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- Rounded to the hour for hourly velocity
    review_count_last_hour INT DEFAULT 0,
    review_count_last_day INT DEFAULT 0,
    average_velocity_last_7_days FLOAT DEFAULT 0.0, -- Stored for historical context/baseline
    is_anomaly BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (product_id, timestamp)
);

CREATE INDEX idx_reviewvelocity_product_id ON ReviewVelocity (product_id);
CREATE INDEX idx_reviewvelocity_timestamp ON ReviewVelocity (timestamp DESC);

-- Schema for FlaggedReview (US1.1.4)
CREATE TABLE FlaggedReview (
    flagged_review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id VARCHAR(255) NOT NULL, -- Foreign key to the external Review Management Service's Review ID
    product_id VARCHAR(255) NOT NULL,
    flagged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score FLOAT NOT NULL,
    status VARCHAR(50) DEFAULT 'NEW' CHECK (status IN ('NEW', 'INVESTIGATING', 'ABUSIVE', 'CLEARED')),
    flagging_reason TEXT,
    investigator_id VARCHAR(255), -- ID of the investigator who took action
    investigation_notes TEXT,
    action_taken_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (review_id) -- A review should ideally only be flagged once
);

CREATE INDEX idx_flaggedreview_confidence_score ON FlaggedReview (confidence_score DESC);
CREATE INDEX idx_flaggedreview_status ON FlaggedReview (status);
CREATE INDEX idx_flaggedreview_product_id ON FlaggedReview (product_id);
