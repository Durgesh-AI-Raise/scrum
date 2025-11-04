
-- reviews table
CREATE TABLE IF NOT EXISTS reviews (
    review_id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    reviewer_id UUID NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    sentiment_score NUMERIC(3, 2) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- products table (simplified for initial sprint)
CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    category TEXT[], -- Array of strings for categories
    brand VARCHAR(255),
    average_rating NUMERIC(2, 1) CHECK (average_rating >= 1 AND average_rating <= 5),
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- reviewers table (simplified for initial sprint)
CREATE TABLE IF NOT EXISTS reviewers (
    reviewer_id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    country VARCHAR(255),
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- sellers table (simplified for initial sprint)
CREATE TABLE IF NOT EXISTS sellers (
    seller_id UUID PRIMARY KEY,
    seller_name VARCHAR(255) NOT NULL,
    country VARCHAR(255),
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_products_sold INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for common lookups and foreign keys
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id ON reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_review_date ON reviews (review_date);

-- Foreign key constraints (optional for initial MVP, can be added later for data integrity)
-- ALTER TABLE reviews ADD CONSTRAINT fk_reviews_product
--   FOREIGN KEY (product_id) REFERENCES products (product_id);
-- ALTER TABLE reviews ADD CONSTRAINT fk_reviews_reviewer
--   FOREIGN KEY (reviewer_id) REFERENCES reviewers (reviewer_id);
