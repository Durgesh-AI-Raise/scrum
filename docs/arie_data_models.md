### Consolidated Data Models for Amazon Review Integrity Engine (ARIE)

Here are the core data models for ARIE, outlining the structure for raw review data, aggregated reviewer profiles, and flagged abusive reviews.

**1. `reviews` (Raw Review Data - Data Lake/NoSQL Document Store)**

This schema defines the structure for all incoming and historical product review data. It's designed for high volume and flexibility, suitable for a data lake (e.g., S3 with Parquet) or a NoSQL document store (e.g., MongoDB).

```json
{
    "review_id": "string",         // Unique identifier for the review (Primary Key)
    "reviewer_id": "string",       // Unique identifier for the reviewer
    "product_id": "string",        // Unique identifier for the product
    "stars": "integer",            // Rating given (1-5)
    "review_text": "string",       // Full text of the review
    "review_timestamp": "timestamp", // When the review was submitted (ISO 8601 format, e.g., "2023-10-27T10:00:00Z")
    "purchase_date": "timestamp",  // When the product was purchased (ISO 8601, nullable)
    "purchase_details": {          // Object for additional purchase information
        "type": "object",
        "properties": {
            "price": {"type": "number"},
            "currency": {"type": "string"}
        },
        "description": "Details about the product purchase, e.g., price, currency."
    },
    "review_source": "string",     // e.g., "Amazon.com", "Mobile App"
    "ingestion_timestamp": "timestamp" // When the data was ingested into ARIE (ISO 8601)
}
```

**2. `reviewer_profiles` (Aggregated Reviewer Data - Relational/NoSQL)**

This model stores aggregated metrics for each reviewer, updated periodically. It is suitable for a relational database like PostgreSQL for structured queries or a NoSQL key-value/document store if schema flexibility is preferred for future metrics.

```sql
-- PostgreSQL DDL equivalent for reviewer_profiles table
CREATE TABLE reviewer_profiles (
    reviewer_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the reviewer
    total_reviews_written INTEGER NOT NULL, -- Total number of reviews posted by this reviewer
    average_rating_given NUMERIC(3, 2),     -- Average star rating given by this reviewer (e.g., 4.50)
    review_velocity_24h INTEGER,            -- Number of reviews posted in the last 24 hours
    review_velocity_7d INTEGER,             -- Number of reviews posted in the last 7 days
    unique_products_reviewed INTEGER,       -- Count of distinct products reviewed by this reviewer
    last_aggregation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL -- Timestamp of the last profile update
);

-- Index for efficient lookup if needed beyond PK
CREATE INDEX idx_reviewer_total_reviews ON reviewer_profiles (total_reviews_written);
```

**3. `flagged_reviews` (Flagging & Severity - Relational with JSONB)**

This model stores information about reviews identified as potentially abusive, including their assigned confidence scores and severity levels. This is well-suited for a relational database with JSONB support (like PostgreSQL) to store flexible rule details while maintaining structured core fields.

```sql
-- PostgreSQL DDL for flagged_reviews table
CREATE TYPE severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE flag_status_enum AS ENUM ('PENDING_REVIEW', 'ACTIONED', 'FALSE_POSITIVE', 'INVESTIGATING');

CREATE TABLE flagged_reviews (
    flag_id UUID PRIMARY KEY,                 -- Unique identifier for the flag event
    review_id VARCHAR(255) NOT NULL,          -- Identifier of the review that was flagged (FK to raw reviews, not enforced for de-coupling)
    reviewer_id VARCHAR(255) NOT NULL,        -- Identifier of the reviewer who posted the flagged review
    product_id VARCHAR(255) NOT NULL,         -- Identifier of the product related to the flagged review
    flag_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- When the review was flagged
    rules_triggered JSONB NOT NULL,           -- JSON array of rule IDs that triggered the flag (e.g., ["RULE_ID_1", "RULE_ID_2"])
    confidence_score NUMERIC(3, 2) NOT NULL,  -- Confidence level of the flag (0.00 to 1.00)
    severity_level severity_enum NOT NULL,    -- Severity level of the detected abuse
    status flag_status_enum NOT NULL DEFAULT 'PENDING_REVIEW', -- Current status of the flag (e.g., pending, actioned)
    additional_details JSONB,                 -- Free-form JSON for extra context from the rule engine or analysts
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Timestamp when the flag record was created
);

-- Indexes for common queries
CREATE INDEX idx_flagged_reviews_reviewer_id ON flagged_reviews (reviewer_id);
CREATE INDEX idx_flagged_reviews_product_id ON flagged_reviews (product_id);
CREATE INDEX idx_flagged_reviews_timestamp ON flagged_reviews (flag_timestamp DESC);
CREATE INDEX idx_flagged_reviews_severity_status ON flagged_reviews (severity_level, status);
