-- Table to store aggregated review velocity data
CREATE TABLE product_review_velocity (
    velocity_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    time_window_start TIMESTAMP NOT NULL,
    time_window_end TIMESTAMP NOT NULL,
    review_count INT NOT NULL DEFAULT 0,
    positive_review_count INT NOT NULL DEFAULT 0,
    negative_review_count INT NOT NULL DEFAULT 0,
    total_rating_sum INT NOT NULL DEFAULT 0, -- Store sum of all ratings
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, time_window_start)
);

-- Table to store detected anomalies
CREATE TABLE review_velocity_anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    time_window_start TIMESTAMP NOT NULL,
    time_window_end TIMESTAMP NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anomaly_score DECIMAL(5,2), -- e.g., Z-score
    anomaly_type VARCHAR(50), -- e.g., 'spike_positive', 'spike_negative', 'drop'
    status VARCHAR(50) DEFAULT 'open', -- e.g., 'open', 'investigating', 'closed'
    FOREIGN KEY (product_id, time_window_start) REFERENCES product_review_velocity(product_id, time_window_start)
);

-- Indexing for performance
CREATE INDEX idx_product_velocity_product_id ON product_review_velocity (product_id);
CREATE INDEX idx_product_velocity_time_window ON product_review_velocity (time_window_start DESC);
CREATE INDEX idx_anomaly_product_id ON review_velocity_anomalies (product_id);
CREATE INDEX idx_anomaly_detected_at ON review_velocity_anomalies (detected_at DESC);