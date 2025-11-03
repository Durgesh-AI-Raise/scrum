
-- db_schema.sql

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(255) PRIMARY KEY,
    product_name TEXT,
    product_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sellers Table
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(255) PRIMARY KEY,
    seller_name TEXT,
    seller_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reviewers Table (basic profile)
CREATE TABLE IF NOT EXISTS reviewers (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    reviewer_name TEXT,
    reviewer_profile_url TEXT,
    total_reviews INTEGER DEFAULT 0, -- Placeholder for future calculation/enrichment
    average_rating NUMERIC(2,1) DEFAULT 0.0, -- Placeholder
    account_creation_date TIMESTAMP WITH TIME ZONE, -- Placeholder
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reviews Table (main table)
CREATE TABLE IF NOT EXISTS reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL REFERENCES products(product_id),
    seller_id VARCHAR(255) REFERENCES sellers(seller_id),
    reviewer_id VARCHAR(255) NOT NULL REFERENCES reviewers(reviewer_id),
    rating INTEGER NOT NULL,
    title TEXT,
    review_text TEXT,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_verified_purchase BOOLEAN,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Abuse Detection Fields
    flagged_reasons TEXT[], -- Array of strings e.g., ['LOW_RATING_SHORT_TEXT', 'NO_REVIEW_TEXT_WITH_EXTREME_RATING']
    risk_score INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_seller_id ON reviews(seller_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id ON reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_risk_score ON reviews(risk_score DESC);

-- Function to update 'updated_at' column automatically
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products table
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_products_timestamp') THEN
        CREATE TRIGGER set_products_timestamp
        BEFORE UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;

-- Trigger for sellers table
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_sellers_timestamp') THEN
        CREATE TRIGGER set_sellers_timestamp
        BEFORE UPDATE ON sellers
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;

-- Trigger for reviewers table
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_reviewers_timestamp') THEN
        CREATE TRIGGER set_reviewers_timestamp
        BEFORE UPDATE ON reviewers
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;

-- Trigger for reviews table
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_reviews_timestamp') THEN
        CREATE TRIGGER set_reviews_timestamp
        BEFORE UPDATE ON reviews
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
