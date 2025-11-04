# Data Ingestion for Review Velocity and Rating Distribution

## User Story: As a Review Integrity System, I need to detect anomalous review patterns...
## Task 1.2: Implement data ingestion for review velocity and rating distribution (Issue #10448)

This document details the implementation plan for ingesting and processing review data to support anomaly detection for review velocity and rating distribution.

### 1. Implementation Plan

*   **Data Sources:** Raw review data is assumed to reside in Amazon.com's primary review database (e.g., a relational database or a NoSQL store optimized for transactional writes).
*   **Ingestion Method (MVP):** For the initial implementation, a scheduled batch processing approach will be used. A Python script (or AWS Lambda function) will be triggered periodically (e.g., hourly, daily) to fetch recent raw review data.
*   **Aggregation Logic:**
    *   **Review Velocity:** Review counts will be aggregated per `product_id` and potentially `seller_id` within defined rolling time windows (e.g., 1-hour, 24-hour, 7-day). The script will count reviews and calculate average ratings within these windows.
    *   **Rating Distribution:** For each `product_id`, the counts of each star rating (1-5) will be aggregated for a specific recent period (e.g., last 7 days or last `N` reviews). This provides a snapshot of the rating distribution.
*   **Data Storage:** The aggregated data will be stored in dedicated tables within a managed database (e.g., PostgreSQL or DynamoDB) to facilitate quick retrieval by the anomaly detection modules.
*   **Error Handling & Monitoring:** Basic logging will be implemented for ingestion failures. CloudWatch metrics or similar monitoring tools will track the success rate and latency of ingestion jobs.

### 2. Data Models and Architecture

#### 2.1 Raw Review Data (Conceptual)

This is the assumed structure of the raw review data from Amazon.com's existing systems.

```sql
TABLE Reviews (
    review_id UUID PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    -- ... other relevant fields like helpfulness_votes, title, etc.
);
```

#### 2.2 Aggregated Review Velocity Data Model

This table will store aggregated review counts and average ratings over specific time windows.

```sql
TABLE ReviewVelocityAggregate (
    product_id VARCHAR(255) NOT NULL,
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL, -- e.g., start of the hour/day
    window_duration_minutes INTEGER NOT NULL, -- e.g., 60 for hourly, 1440 for daily
    review_count INTEGER NOT NULL DEFAULT 0,
    avg_rating_in_window REAL, -- Average rating in this window
    PRIMARY KEY (product_id, time_window_start, window_duration_minutes)
);
```

#### 2.3 Aggregated Rating Distribution Data Model

This table will store the counts for each star rating within a defined aggregation period for a product.

```sql
TABLE RatingDistributionAggregate (
    product_id VARCHAR(255) NOT NULL,
    aggregation_period VARCHAR(50) NOT NULL, -- e.g., 'last_24h', 'last_7d', 'recent_100_reviews'
    rating_1_count INTEGER NOT NULL DEFAULT 0,
    rating_2_count INTEGER NOT NULL DEFAULT 0,
    rating_3_count INTEGER NOT NULL DEFAULT 0,
    rating_4_count INTEGER NOT NULL DEFAULT 0,
    rating_5_count INTEGER NOT NULL DEFAULT 0,
    total_reviews_in_period INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (product_id, aggregation_period)
);
```

#### 2.4 Architecture (High-Level)

```mermaid
graph TD
    A[Amazon.com Raw Review Database] --> B(Data Ingestion Service/Lambda)
    B --> C[ReviewVelocityAggregate Table]
    B --> D[RatingDistributionAggregate Table]
    C -- Query --> E[Anomaly Detection Module (Velocity)]
    D -- Query --> F[Anomaly Detection Module (Distribution)]
```

### 3. Assumptions and Technical Decisions

*   **Assumption:** The raw review database is queryable with appropriate performance for the chosen ingestion frequency.
*   **Assumption:** `product_id` is a reliable key for aggregating review data.
*   **Technical Decision (MVP):** Use Python for the ingestion script due to its rich data processing libraries and ease of deployment as a scheduled job or serverless function.
*   **Technical Decision:** Initially, `window_duration_minutes` for velocity will be 60 (hourly) and 1440 (daily). `aggregation_period` for distribution will be 'last_7d'. These can be extended later.
*   **Technical Decision:** Upsert (insert or update) operations will be used when storing aggregated data to handle existing entries gracefully and ensure data freshness.

### 4. Code Snippets/Pseudocode for Key Components

```python
from datetime import datetime, timedelta
import collections

# --- Simulated Database Interactions ---

def fetch_raw_reviews_from_db(start_time: datetime, end_time: datetime) -> list[dict]:
    """
    Simulates fetching raw reviews from a database within a given time range.
    In a real scenario, this would involve SQL queries or NoSQL API calls.
    """
    print(f"[DB] Fetching reviews from {start_time} to {end_time}")
    # Example: Simulate some review data for testing
    mock_reviews = [
        {"product_id": "prod_A", "rating": 5, "review_date": end_time - timedelta(minutes=15)},
        {"product_id": "prod_A", "rating": 4, "review_date": end_time - timedelta(minutes=30)},
        {"product_id": "prod_B", "rating": 1, "review_date": end_time - timedelta(minutes=45)},
        {"product_id": "prod_C", "rating": 5, "review_date": end_time - timedelta(hours=2, minutes=10)},
        {"product_id": "prod_A", "rating": 5, "review_date": end_time - timedelta(days=2)},
        {"product_id": "prod_A", "rating": 1, "review_date": end_time - timedelta(days=2, hours=1)},
    ]
    return [r for r in mock_reviews if start_time <= r["review_date"] < end_time]

def store_velocity_aggregates(velocity_data: list[dict]):
    """
    Simulates storing aggregated review velocity data into the database.
    """
    print(f"[DB] Storing {len(velocity_data)} velocity aggregates.")
    for item in velocity_data:
        print(f"  [DB Save] ReviewVelocityAggregate: {item}")

def store_distribution_aggregates(distribution_data: list[dict]):
    """
    Simulates storing aggregated rating distribution data into the database.
    """
    print(f"[DB] Storing {len(distribution_data)} distribution aggregates.")
    for item in distribution_data:
        print(f"  [DB Save] RatingDistributionAggregate: {item}")

# --- Aggregation Logic ---

def aggregate_review_velocity(reviews: list[dict], window_duration_minutes: int) -> list[dict]:
    """
    Aggregates review counts and average ratings per product within time windows.
    """
    velocity_aggregates = collections.defaultdict(lambda: {"review_count": 0, "total_rating": 0, "num_ratings": 0})
    
    for review in reviews:
        product_id = review["product_id"]
        review_date = review["review_date"]
        
        # Determine the start of the current time window
        if window_duration_minutes == 60: # Hourly
            window_start = review_date.replace(minute=0, second=0, microsecond=0)
        elif window_duration_minutes == 1440: # Daily
            window_start = review_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Handle other window durations or round down to nearest window_duration_minutes
            raise ValueError("Unsupported window_duration_minutes")

        key = (product_id, window_start, window_duration_minutes)
        velocity_aggregates[key]["review_count"] += 1
        velocity_aggregates[key]["total_rating"] += review["rating"]
        velocity_aggregates[key]["num_ratings"] += 1

    result = []
    for (product_id, window_start, duration), data in velocity_aggregates.items():
        result.append({
            "product_id": product_id,
            "time_window_start": window_start,
            "window_duration_minutes": duration,
            "review_count": data["review_count"],
            "avg_rating_in_window": data["total_rating"] / data["num_ratings"] if data["num_ratings"] > 0 else 0.0
        })
    return result

def aggregate_rating_distribution(reviews: list[dict], aggregation_period_name: str) -> list[dict]:
    """
    Aggregates rating counts (1-5 stars) per product for a given period.
    """
    distribution_aggregates = collections.defaultdict(lambda: {f"rating_{i}_count": 0 for i in range(1, 6)} | {"total_reviews_in_period": 0})

    for review in reviews:
        product_id = review["product_id"]
        rating = review["rating"]
        
        if 1 <= rating <= 5:
            distribution_aggregates[product_id][f"rating_{rating}_count"] += 1
            distribution_aggregates[product_id]["total_reviews_in_period"] += 1

    result = []
    for product_id, data in distribution_aggregates.items():
        result.append({
            "product_id": product_id,
            "aggregation_period": aggregation_period_name,
            **data,
            "last_updated": datetime.now()
        })
    return result

# --- Main Ingestion Process ---

def run_data_ingestion():
    """
    Orchestrates the data ingestion process for review velocity and rating distribution.
    This function would typically be called by a scheduler (e.g., cron, AWS EventBridge).
    """
    current_time = datetime.now()

    # 1. Ingest for Hourly Review Velocity (e.g., last 1 hour)
    print("\n--- Running Hourly Velocity Ingestion ---")
    start_time_hourly = current_time - timedelta(hours=1)
    hourly_reviews = fetch_raw_reviews_from_db(start_time_hourly, current_time)
    velocity_aggregates_hourly = aggregate_review_velocity(hourly_reviews, 60)
    store_velocity_aggregates(velocity_aggregates_hourly)

    # 2. Ingest for Daily Review Velocity (e.g., last 24 hours)
    print("\n--- Running Daily Velocity Ingestion ---")
    start_time_daily = current_time - timedelta(days=1)
    daily_reviews = fetch_raw_reviews_from_db(start_time_daily, current_time)
    velocity_aggregates_daily = aggregate_review_velocity(daily_reviews, 1440)
    store_velocity_aggregates(velocity_aggregates_daily)

    # 3. Ingest for Rating Distribution (e.g., last 7 days)
    print("\n--- Running 7-Day Rating Distribution Ingestion ---")
    start_time_7days = current_time - timedelta(days=7)
    reviews_for_distribution = fetch_raw_reviews_from_db(start_time_7days, current_time)
    distribution_aggregates = aggregate_rating_distribution(reviews_for_distribution, "last_7d")
    store_distribution_aggregates(distribution_aggregates)

# To run the ingestion process (in a real system, this would be scheduled):
# if __name__ == "__main__":
#     run_data_ingestion()
```
