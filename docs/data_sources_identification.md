# Identified Data Sources for ARIS Review Data

## 1. Introduction
This document outlines the potential internal Amazon systems and databases identified as primary data sources for ingesting review-related information into the Amazon Review Integrity System (ARIS). A comprehensive dataset is crucial for effective abuse detection.

## 2. Identified Data Sources and Their Contributions

### 2.1. Review Service Database (Primary Source)
*   **Description:** The core database storing all submitted customer reviews.
*   **Data Contributed:**
    *   `review_id` (Unique identifier for the review)
    *   `product_id` (ID of the product being reviewed)
    *   `reviewer_id` (ID of the customer who wrote the review)
    *   `review_text` (The actual review content)
    *   `rating` (Star rating given by the reviewer)
    *   `review_date` (Timestamp of review submission)
    *   `helpful_votes` (Number of users who found the review helpful)
    *   `sentiment_score` (Potentially pre-calculated or to be calculated by ARIS NLP)
    *   `is_verified_purchase` (Flag indicating if the reviewer purchased the product from Amazon)
    *   `review_status` (e.g., 'pending', 'approved', 'rejected')

### 2.2. Product Catalog Service / Database
*   **Description:** System containing detailed information about all products sold on Amazon.
*   **Data Contributed (via `product_id` lookup):
    *   `product_name`
    *   `product_category` / `department`
    *   `seller_id` (Primary seller of the product)
    *   `brand`
    *   `product_creation_date`
    *   `product_lifecycle_status`

### 2.3. Customer Profile Service / Database
*   **Description:** Stores comprehensive information about Amazon customers.
*   **Data Contributed (via `reviewer_id` lookup):
    *   `customer_id`
    *   `customer_registration_date`
    *   `customer_country`
    *   `customer_prime_status`
    *   `historical_review_count` (Total reviews posted by the customer)
    *   `average_rating_given`
    *   `account_status` (e.g., 'active', 'suspended', 'compromised')

### 2.4. Order History Service / Database
*   **Description:** Records all purchase transactions made by customers.
*   **Data Contributed (via `reviewer_id` and `product_id` lookup):
    *   `purchase_history` (e.g., frequency of purchases, value of purchases)
    *   `product_purchase_date` (Relevant for `is_verified_purchase` cross-check)
    *   `shipping_address_history` (Potentially for geo-location analysis)

### 2.5. Seller Service / Database
*   **Description:** Contains information about third-party sellers on Amazon.
*   **Data Contributed (via `seller_id` lookup):
    *   `seller_name`
    *   `seller_registration_date`
    *   `seller_performance_metrics`
    *   `seller_country`

### 2.6. IP Address / Session Data (Log Services)
*   **Description:** Logging services that capture user session and access IP addresses associated with review submissions.
*   **Data Contributed:
    *   `ip_address` (IP address from which the review was submitted)
    *   `user_agent` (Browser/device information)
    *   `session_id`
    *   `geo_location_data` (Derived from IP address, if available)

## 3. Data Volume and Frequency Considerations
*   **New Reviews:** High volume, real-time streaming (tens of thousands per minute).
*   **Existing Reviews:** Potentially petabytes of historical data requiring initial bulk ingestion, followed by incremental updates.

This identification serves as the foundation for designing the data ingestion pipeline in subsequent tasks.