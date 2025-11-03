CREATE TABLE Products (
    product_id VARCHAR(255) PRIMARY KEY,
    product_name VARCHAR(255),
    product_category VARCHAR(255),
    product_url TEXT
);

CREATE TABLE Reviewers (
    reviewer_id VARCHAR(255) PRIMARY KEY,
    reviewer_name VARCHAR(255),
    account_creation_date TIMESTAMP,
    total_reviews INT DEFAULT 0
);

CREATE TABLE Orders (
    order_id VARCHAR(255) PRIMARY KEY,
    reviewer_id VARCHAR(255) REFERENCES Reviewers(reviewer_id),
    order_date TIMESTAMP,
    total_amount DECIMAL(10, 2)
);

CREATE TABLE Reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255) REFERENCES Products(product_id),
    reviewer_id VARCHAR(255) REFERENCES Reviewers(reviewer_id),
    order_id VARCHAR(255) REFERENCES Orders(order_id), -- Can be NULL if review is not tied to a specific order
    rating INT CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    content TEXT,
    review_date TIMESTAMP,
    is_abusive BOOLEAN DEFAULT FALSE,
    flagging_reason TEXT
);