# Amazon Customer Review Data Schemas

## 1. Raw Review Data Schema

This schema is intended for the initial ingestion of raw Amazon review data, typically stored in a data lake (e.g., Amazon S3) as JSON or Parquet files.

```json
{
  "review_id": "String",         // Primary Key: Unique identifier for the review
  "product_id": "String",        // Identifier for the product being reviewed
  "customer_id": "String",       // Identifier for the customer who wrote the review
  "star_rating": "Integer",      // Rating given by the customer (e.g., 1-5)
  "review_headline": "String",   // Title of the review
  "review_body": "String",       // Full text content of the review
  "review_date": "Timestamp",    // Date and time the review was posted (ISO 8601 format)
  "verified_purchase": "Boolean",// Indicates if the review is from a verified purchase
  "product_title": "String",     // Title of the product at the time of review
  "product_category": "String",  // Category of the product
  "ingestion_timestamp": "Timestamp" // When the data was ingested into our system
  // ... potentially other raw fields from Amazon reviews if available
}
```

## 2. Enriched/Processed Review Data Schema

This schema is for structured, processed, and enriched review data, suitable for analytical databases (e.g., Amazon Redshift, Snowflake). It includes fields for detection flags.

```json
{
  "review_id": "String",             // Primary Key, Foreign Key to Raw Review Data
  "product_id": "String",            // Foreign Key to Product Dimension
  "customer_id": "String",           // Foreign Key to Customer Dimension
  "review_date": "Timestamp",        // Date and time the review was posted (useful for partitioning/sorting)
  "star_rating": "Integer",
  "review_headline": "String",
  "review_body": "String",
  "verified_purchase": "Boolean",
  "ingestion_timestamp": "Timestamp", // When the data was ingested into our system

  // Detection Flags (initial set, will evolve)
  "is_velocity_anomaly": "Boolean",   // Default: false; True if flagged by velocity detection
  "velocity_score": "Float",          // Nullable; Score indicating the degree of velocity anomaly
  "is_suspicious_account": "Boolean", // Default: false; True if flagged by account behavior detection
  "account_suspicion_score": "Float"  // Nullable; Score indicating the degree of account suspicion
  // ... other aggregated/processed fields or additional detection flags
}
```

## 3. Product Dimension (Conceptual for Data Warehouse)

```json
{
  "product_id": "String",         // Primary Key
  "product_title": "String",
  "product_category": "String"
  // ... other product-related attributes (e.g., brand, ASIN)
}
```

## 4. Customer Dimension (Conceptual for Data Warehouse)

```json
{
  "customer_id": "String",            // Primary Key
  "customer_creation_date": "Timestamp" // When the customer account was created (if available)
  // ... other customer-related attributes (e.g., anonymized demographics, region)
}
```
