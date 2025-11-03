
CREATE TABLE reviews (
    review_id VARCHAR(256) PRIMARY KEY,
    user_id VARCHAR(256),
    product_id VARCHAR(256),
    seller_id VARCHAR(256),
    rating INTEGER,
    title VARCHAR(512),
    content VARCHAR(MAX),
    review_date TIMESTAMP,
    is_verified_purchase BOOLEAN,
    upvotes INTEGER,
    downvotes INTEGER,
    source_ip VARCHAR(64),
    metadata SUPER -- Redshift's JSON-like type for flexibility
)
DISTSTYLE AUTO;

CREATE TABLE users (
    user_id VARCHAR(256) PRIMARY KEY,
    username VARCHAR(256),
    registration_date TIMESTAMP,
    email VARCHAR(256),
    total_reviews_submitted INTEGER,
    avg_rating_given DECIMAL(3,2),
    country VARCHAR(128),
    metadata SUPER
)
DISTSTYLE AUTO;

CREATE TABLE products (
    product_id VARCHAR(256) PRIMARY KEY,
    product_name VARCHAR(512),
    category VARCHAR(256),
    brand VARCHAR(256),
    asin VARCHAR(10),
    release_date TIMESTAMP,
    avg_rating DECIMAL(3,2),
    total_reviews INTEGER,
    metadata SUPER
)
DISTSTYLE AUTO;

CREATE TABLE sellers (
    seller_id VARCHAR(256) PRIMARY KEY,
    seller_name VARCHAR(256),
    registration_date TIMESTAMP,
    total_products_sold INTEGER,
    avg_seller_rating DECIMAL(3,2),
    metadata SUPER
)
DISTSTYLE AUTO;

CREATE TABLE flagged_entity (
    flag_id VARCHAR(256) PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id VARCHAR(256),
    anomaly_type VARCHAR(256),
    flag_timestamp TIMESTAMP,
    severity VARCHAR(50),
    reason VARCHAR(MAX),
    triggered_rules SUPER, -- JSONB equivalent
    status VARCHAR(50),
    metadata SUPER
)
DISTSTYLE AUTO;
