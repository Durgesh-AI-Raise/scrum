# ARIS Review Data Model

## `reviews` Collection Schema (MongoDB/Document Store)

This document outlines the proposed data model for storing review-related data within the ARIS platform. The schema is designed to be flexible, supporting future extensions for IP/device tracking, anomaly detection flags, and abuse classification.

### Fields:

```json
{
  "reviewId": "uuid-v4-string",           // Primary Key, unique identifier for the review (e.g., from source system)
  "reviewerId": "string",                 // Indexed: Unique identifier for the reviewer
  "productId": "string",                  // Indexed: Unique identifier for the product
  "starRating": "integer",                // The star rating given by the reviewer (1-5)
  "reviewText": "string",                 // The actual textual content of the review
  "timestamp": "ISO-8601-string",         // Indexed: Timestamp when the review was originally submitted
  "ingestionTimestamp": "ISO-8601-string",// Timestamp when the review was ingested into ARIS

  // --- Future Fields (to be populated by subsequent tasks) ---

  "ipAddress": "string",                  // (From Task 2.3) IP address from which the review was submitted
  "deviceFingerprint": "string",          // (From Task 2.3) A unique identifier generated from device characteristics
  "deviceMetadata": {                     // (From Task 2.3) Structured metadata derived from device information
    "userAgent": "string",                // Full User-Agent string
    "browser": "string",                  // Parsed browser name (e.g., "Chrome", "Firefox")
    "os": "string",                       // Parsed operating system (e.g., "Windows", "iOS", "Android")
    "deviceType": "string"                // Parsed device type (e.g., "Desktop", "Mobile", "Tablet")
  },
  "anomalyFlags": [                       // (From Task 3.3) Array of detected behavioral anomalies for this review/reviewer
    {
      "ruleId": "string",                 // Unique ID of the rule that triggered this flag (e.g., "RULE001")
      "name": "string",                   // Human-readable name of the anomaly rule
      "description": "string",            // Brief description of the anomaly
      "detectedOn": "ISO-8601-string",    // Timestamp when this anomaly was detected
      "severity": "string",               // Severity level (e.g., "low", "medium", "high")
      "metricValue": "float/int",         // The value of the metric that exceeded the threshold
      "threshold": "float/int"            // The threshold defined in the rule
    }
  ],
  "abuseCategory": {                      // (From Task 4.2) The final classified abuse category for the review
    "categoryId": "string",               // Unique ID of the abuse category (e.g., "ABUSE001")
    "categoryName": "string",             // Human-readable name of the abuse category
    "confidence": "float"                 // Confidence score of the classification (0.0 to 1.0)
  }
}
```

### Indexes:

*   `reviewId`: Unique index (primary key)
*   `reviewerId`: Standard index for querying reviewer-specific data
*   `productId`: Standard index for querying product-specific data
*   `timestamp`: Standard index for time-series queries and range-based lookups
