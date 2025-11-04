# Real-time Review Data Stream Research Summary

**Objective:** Identify suitable Amazon internal/external APIs or data streams for real-time ingestion of product review data.

**Findings (Hypothetical based on common Amazon architecture):**

1.  **Primary Candidate: Amazon Review Event Stream (Internal Kinesis/Kafka)**
    *   **Description:** An internal, high-throughput streaming service that publishes events whenever a new product review is submitted or an existing one is updated. This is the ideal source.
    *   **Available Fields (Expected):**
        *   `review_id` (String, unique identifier for the review)
        *   `reviewer_id` (String, unique identifier for the reviewer)
        *   `product_id` (String, unique identifier for the reviewed product)
        *   `marketplace_id` (String, e.g., 'ATVPDKIKX0DER' for Amazon.com)
        *   `star_rating` (Number, 1-5)
        *   `review_title` (String, title of the review)
        *   `review_text` (String, full content of the review)
        *   `review_date` (ISO 8601 String, timestamp of review submission)
        *   `product_category` (String, primary category of the product, e.g., 'Electronics', 'Books') - *Assumption: This field is directly available or can be easily derived/joined.*
        *   `helpful_votes` (Number)
        *   `verified_purchase` (Boolean)
    *   **Access Requirements:** Internal AWS IAM roles, Vpc connectivity, specific permissions for the Kinesis/Kafka stream.
    *   **Pros:** Real-time, high volume, comprehensive data, direct from source.
    *   **Cons:** Requires internal Amazon access and potentially specific service subscriptions.

2.  **Secondary Candidate: Amazon Selling Partner API (SP-API) - Feeds API / Notifications API**
    *   **Description:** Primarily for sellers, but has some data feeds. Notifications API *might* allow subscribing to review events, but usually limited to seller's own products.
    *   **Pros:** Publicly documented API.
    *   **Cons:** Not designed for *all* Amazon product reviews across the marketplace, likely rate-limited, might not be truly real-time at scale. Less ideal for a general marketplace-wide detection system.

**Decision:** Proceed with the assumption of an internal Amazon Review Event Stream (Kinesis). This provides the necessary real-time, high-volume data required for the sprint goal.