# Review and Reviewer Data Models

## Review Data Model (MongoDB Collection: `reviews`)
```json
{
  "review_id": "string",            // Primary key, unique ID from source
  "product_id": "string",           // ID of the product reviewed
  "reviewer_id": "string",          // Foreign key to Reviewer, ID of the reviewer
  "rating": "integer",              // 1-5 star rating
  "title": "string",                // Title of the review
  "content": "string",              // Full text content of the review
  "review_date": "ISO_8601_string", // Original date of the review (e.g., "2023-10-26T14:30:00Z")
  "source_url": "string",           // URL to the original review
  "ingestion_timestamp": "ISO_8601_string", // When this record was ingested into our system
  "flagged": "boolean",             // Default: false. True if system flags it as suspicious
  "flagging_reason": "string"       // Optional, reason for flagging
}
```

## Reviewer Data Model (MongoDB Collection: `reviewers`)
```json
{
  "reviewer_id": "string",          // Primary key, unique ID from source
  "username": "string",             // Reviewer's display name
  "account_age_days": "integer",    // Account age in days
  "purchase_history_product_ids": ["string"], // List of product IDs purchased (simplified)
  "ip_address_last_known": "string",// Last known IP address associated with a review
  "device_info_last_known": "string",// Last known device info (e.g., user-agent)
  "total_reviews_count": "integer", // Total number of reviews submitted by this reviewer
  "last_review_timestamp": "ISO_8601_string", // Timestamp of the reviewer's most recent review
  "flagged": "boolean",             // Default: false. True if reviewer account is flagged
  "flagging_reason": "string"       // Optional, reason for flagging reviewer account
}
```
