### Task 2.2: Design data model for linking entities.

*   **Implementation Plan:** Design a comprehensive data model for the enriched review data, integrating reviewer, product, and purchase information. This model will be optimized for querying and analytical purposes, suitable for a data warehouse or a managed relational database.
*   **Data Models and Architecture:**
    *   **Storage:** Amazon RDS (PostgreSQL) or a similar managed relational database.
    *   **Core Entity:** `enriched_reviews` table, combining information from the raw review, reviewer, product, and order entities.
    *   **Schema Definition (SQL DDL - PostgreSQL/Redshift compatible):**
        ```sql
        CREATE TABLE IF NOT EXISTS enriched_reviews (
            review_id VARCHAR(255) PRIMARY KEY,
            reviewer_id VARCHAR(255) NOT NULL,
            product_asin VARCHAR(255) NOT NULL,
            order_id VARCHAR(255),
            review_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            review_title TEXT,
            review_text TEXT,
            overall_rating INTEGER,
            ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            
            -- Reviewer Details (Denormalized)
            reviewer_username VARCHAR(255),
            reviewer_email VARCHAR(255),
            reviewer_registration_date TIMESTAMP WITH TIME ZONE,
            reviewer_account_status VARCHAR(50),

            -- Product Details (Denormalized)
            product_name TEXT,
            product_brand VARCHAR(255),
            product_category VARCHAR(255),
            product_price NUMERIC(10, 2),
            product_release_date DATE,

            -- Order Details (Denormalized - simplified, as a review is tied to one order)
            order_date TIMESTAMP WITH TIME ZONE,
            order_total_amount NUMERIC(10, 2),
            order_status VARCHAR(50)

            -- Optional: Add indexes for frequently queried columns
            -- INDEX (reviewer_id),
            -- INDEX (product_asin),
            -- INDEX (review_timestamp DESC)
        );
        ```
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** The internal APIs (defined in Task 2.1) will reliably provide the necessary data for enrichment.
    *   **Decision:** A denormalized approach will be favored for the `enriched_reviews` table to optimize read performance for analytical queries, potentially duplicating some data for efficiency.
    *   **Decision:** PostgreSQL on Amazon RDS is chosen as the target database for its flexibility, SQL capabilities, and managed service benefits, which align well with structured, queryable data.
    *   **Decision:** `TEXT` data type is used for `review_title` and `review_text` to accommodate variable-length string data.
    *   **Decision:** `TIMESTAMP WITH TIME ZONE` is chosen for timestamps to preserve timezone information, crucial for global e-commerce data.
*   **Code Snippets/Pseudocode:** (Provided above in Data Models section.)