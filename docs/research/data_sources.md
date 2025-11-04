# Research on Amazon Review Data Sources

## Findings:

1.  **Public Datasets:** Several public datasets are available on platforms like Kaggle (e.g., Amazon Reviews dataset by J. McAuley), which provide historical review data. These are typically in CSV or JSON format.
2.  **Amazon Product Advertising API (PA-API):** Primarily for product information, not comprehensive real-time review streams. Access is limited and focused on product-centric data.
3.  **Third-Party Scrapers/APIs:** Various services offer scraped Amazon review data. These often come with costs and compliance considerations regarding Amazon's Terms of Service. Not recommended for internal, real-time ingestion in a production system due to reliability, legality, and cost.

## Conclusion for MVP:

Given the constraints and for establishing a foundational system, we will proceed with:
*   **Simulated Real-time Ingestion:** For Sprint 1, we will simulate real-time ingestion by either replaying records from a public Amazon review dataset (e.g., a sample JSON file) or generating mock review data programmatically.
*   **Data Format:** Assume incoming review data will be in JSON format, facilitating easy parsing and schema definition.

## Data Schema Expectation:

Each review record is expected to contain (at minimum):
*   `review_id` (String)
*   `product_id` (String)
*   `reviewer_id` (String)
*   `overall_rating` (Integer, 1-5)
*   `review_content` (String)
*   `review_title` (String, optional)
*   `review_date` (Timestamp)
*   `verified_purchase` (Boolean, optional)
*   `helpful_votes` (Integer, optional)
*   `reviewer_ip_address` (String, optional, for abuse detection)
*   `source_platform` (String, e.g., "Amazon")
