### Real-time Review Ingestion Pipeline Design

**1. Data Model (Kafka Message Schema for `raw_reviews` topic):**
```json
{
    "review_id": "string",
    "product_id": "string",
    "reviewer_id": "string",
    "rating": "integer",
    "title": "string",
    "content": "string",
    "review_date": "timestamp", // ISO 8601 format
    "source": "string",
    "metadata": {}
}
```

**2. DynamoDB `reviews` Table Schema:**
- `review_id` (Primary Key - String)
- `product_id` (String - GSI: `product_id-index`)
- `reviewer_id` (String - GSI: `reviewer_id-index`)
- `rating` (Number)
- `title` (String)
- `content` (String)
- `review_date` (String - ISO 8601)
- `source` (String)
- `metadata` (Map)
- `ingestion_timestamp` (String - ISO 8601, timestamp when stored in DB)
- `is_flagged` (Boolean - Default `False`, GSI: `FlaggedReviewsIndex`)
- `flag_reason` (String - Nullable)
- `flag_details` (Map - Nullable)

**3. Kafka `processed_review_events` Message Schema:**
(Used for downstream monitoring, lighter payload)
```json
{
    "review_id": "string",
    "product_id": "string",
    "reviewer_id": "string",
    "review_date": "timestamp",
    "ingestion_timestamp": "timestamp"
}
```

**4. Architecture Overview:**

```
[External Review Source]
       | (JSON)
       v
[Review Ingestion Service (Kafka Producer)]
       |
       v
[Kafka Topic: raw_reviews]
       |
       v
[Review Processor Service (Kafka Consumer)]
       |
       v
[DynamoDB: reviews table]
       |
       v (lighter events)
[Kafka Topic: processed_review_events]
```

**5. Technical Decisions:**
- **Kafka:** Chosen for real-time, high-throughput message queuing.
- **DynamoDB:** Chosen for scalable, flexible NoSQL storage for review data.
- **GSIs:** `product_id-index`, `reviewer_id-index`, `FlaggedReviewsIndex` for efficient querying.
- **Decoupling:** `raw_reviews` for raw data, `processed_review_events` for monitoring to optimize data flow.
