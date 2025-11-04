# Module for Detecting Sudden Review Spikes

## User Story: As a Review Integrity System, I need to detect anomalous review patterns...
## Task 1.3: Develop module for detecting sudden review spikes (Issue #10444)

This document outlines the implementation plan, data models, architecture, and code snippets for the module responsible for detecting sudden, unusual spikes in review volume for a product or seller using the Z-score algorithm.

### 1. Implementation Plan

*   **Data Retrieval:** The module will periodically query the `ReviewVelocityAggregate` table (populated by Task 1.2) to retrieve historical review counts for specific `product_id`s over defined time windows (e.g., hourly, daily).
*   **Baseline Calculation:** For each monitored `product_id`, a rolling mean and standard deviation of review counts will be calculated from a historical window of `ReviewVelocityAggregate` data (e.g., the last 7 days of hourly aggregates).
*   **Z-score Application:** The review count for the most recent time window (the one currently being evaluated) will be compared against its historical baseline (mean and standard deviation) using the Z-score formula:
    `Z = (Current_Count - Historical_Mean) / Historical_Standard_Deviation`
*   **Thresholding:** A pre-configured `z_score_threshold` will be used to determine if the calculated Z-score indicates a significant spike. If `Z > z_score_threshold`, a spike is flagged.
*   **Anomaly Flag Generation:** Upon detecting a spike, an `AnomalyFlag` object (or equivalent data structure) will be generated. This flag will contain details such as the `product_id`, `anomaly_type` ("ReviewVelocitySpike"), `timestamp`, calculated `z_score`, and a `reason` for flagging. This flag will then be published to the central flagging mechanism.
*   **Scheduling:** This module will be scheduled to run after the `ReviewVelocityAggregate` table has been updated for the latest time window.

### 2. Data Models and Architecture

#### 2.1 Input Data (from Task 1.2)

The primary input for this module is the `ReviewVelocityAggregate` table:

```sql
TABLE ReviewVelocityAggregate (
    product_id VARCHAR(255) NOT NULL,
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL, -- e.g., start of the hour/day
    window_duration_minutes INTEGER NOT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    avg_rating_in_window REAL,
    PRIMARY KEY (product_id, time_window_start, window_duration_minutes)
);
```

#### 2.2 Output Data Model: AnomalyFlag

This is the data structure that will be sent to the central flagging mechanism.

```python
class AnomalyFlag:
    product_id: str
    anomaly_type: str  # e.g., "ReviewVelocitySpike"
    timestamp: datetime  # Time when the anomaly was observed (e.g., end of the problematic window)
    score: float       # The Z-score value
    reason: str        # Human-readable reason for flagging
    details: dict      # Additional context like latest_count, baseline_mean, baseline_std_dev
```

#### 2.3 Architecture (High-Level)

```mermaid
graph TD
    A[ReviewVelocityAggregate Table] --> B(Review Spike Detection Module)
    B --> C[Central Flagging Mechanism]
```

### 3. Assumptions and Technical Decisions

*   **Assumption:** The `ReviewVelocityAggregate` table contains sufficient historical data for baseline calculations (at least 2 data points for standard deviation calculation). For new products or initial rollout, a warm-up period or default baseline might be necessary.
*   **Technical Decision:** The Z-score algorithm is chosen for its simplicity, interpretability, and effectiveness in detecting sudden deviations from the norm. It's well-suited for an MVP.
*   **Technical Decision:** The `z_score_threshold` will be a configurable parameter, with an initial value of `3.0`. This threshold can be fine-tuned based on observed false positive/negative rates.
*   **Technical Decision:** The historical baseline period for calculating the mean and standard deviation (e.g., `historical_baseline_days`) will also be configurable, allowing flexibility to adapt to different product review patterns.
*   **Technical Decision:** In cases where the historical standard deviation is zero (meaning all historical review counts are identical), a spike will be detected if the `latest_review_count` is significantly higher than this constant historical mean.

### 4. Code Snippets/Pseudocode for Key Components

```python
import collections
from datetime import datetime, timedelta
import math

# --- Simulated Database Interactions (assuming data from Task 1.2) ---
def fetch_historical_velocity_data(product_id: str, end_time: datetime, window_duration_minutes: int, history_days: int) -> list[dict]:
    """
    Simulates fetching historical review velocity data for a product.
    In a real scenario, this would query ReviewVelocityAggregate.
    """
    print(f"[DB] Fetching historical velocity for {product_id} (last {history_days} days, {window_duration_minutes}-min windows)")
    
    mock_data = []
    # Generate some mock data for the last 'history_days'
    for i in range(history_days * (1440 // window_duration_minutes)): # e.g., 7 days * 24 hours/day
        time_point = end_time - timedelta(minutes=i * window_duration_minutes)
        # Simulate some normal fluctuation, and a potential spike
        review_count = 10 + (math.sin(i / 10) * 5) # Normal
        if i < 5 and product_id == "prod_A": # Recent spike for prod_A
            review_count += 50
        elif i >= 50 and product_id == "prod_B": # Older spike for prod_B
            review_count += 30
        
        mock_data.append({
            "product_id": product_id,
            "time_window_start": time_point.replace(minute=0, second=0, microsecond=0) if window_duration_minutes == 60 else time_point.replace(hour=0, minute=0, second=0, microsecond=0),
            "window_duration_minutes": window_duration_minutes,
            "review_count": max(0, int(review_count)),
            "avg_rating_in_window": 3.5 # Not directly used for spike detection
        })
    # Ensure data is sorted by time_window_start ascending for proper rolling calcs
    return sorted(mock_data, key=lambda x: x["time_window_start"])

def get_latest_velocity_data(product_id: str, time_window_start: datetime, window_duration_minutes: int) -> dict:
    """
    Simulates getting the latest aggregated review velocity data for a product and window.
    """
    print(f"[DB] Fetching latest velocity for {product_id} at {time_window_start} ({window_duration_minutes} min)")
    # This would query ReviewVelocityAggregate for a specific primary key
    # For simulation, let's assume a spike happened recently for prod_A
    if product_id == "prod_A":
        return {
            "product_id": product_id,
            "time_window_start": time_window_start,
            "window_duration_minutes": window_duration_minutes,
            "review_count": 80, # High count for spike
            "avg_rating_in_window": 4.0
        }
    else:
        return {
            "product_id": product_id,
            "time_window_start": time_window_start,
            "window_duration_minutes": window_duration_minutes,
            "review_count": 12, # Normal count
            "avg_rating_in_window": 3.8
        }


def publish_anomaly_flag(flag: dict):
    """
    Simulates publishing an anomaly flag to the central flagging mechanism.
    """
    print(f"[FLAGGING] Published Anomaly: {flag}")

# --- Anomaly Detection Logic ---

def detect_review_spikes(
    product_id: str,
    latest_review_count: int,
    historical_review_counts: list[int],
    z_score_threshold: float = 3.0
) -> (bool, float):
    """
    Detects sudden review spikes using the Z-score algorithm.
    Returns (is_spike_detected, z_score).
    """
    if len(historical_review_counts) < 2:
        print(f"  [SPIKE] Not enough historical data for {product_id} to calculate Z-score.")
        return False, 0.0

    mean_hist = sum(historical_review_counts) / len(historical_review_counts)
    
    # Handle the case of zero standard deviation (all historical counts are the same)
    variance = sum((x - mean_hist) ** 2 for x in historical_review_counts) / len(historical_review_counts)
    std_dev_hist = math.sqrt(variance)

    if std_dev_hist == 0:
        # If all historical values are the same, a spike is detected if current is significantly higher
        if latest_review_count > mean_hist and latest_review_count > 0: # Check for actual increase if mean is 0
             print(f"  [SPIKE] Flat historical data for {product_id}. Latest count {latest_review_count} vs mean {mean_hist}. Considering it a spike if higher.")
             # Assign a high arbitrary Z-score to flag it
             return latest_review_count > mean_hist, 10.0 if latest_review_count > mean_hist else 0.0
        return False, 0.0 # No spike if standard deviation is 0 and current is not higher


    z_score = (latest_review_count - mean_hist) / std_dev_hist
    is_spike = z_score > z_score_threshold

    print(f"  [SPIKE] Product: {product_id}, Latest Count: {latest_review_count}, Mean: {mean_hist:.2f}, Std Dev: {std_dev_hist:.2f}, Z-score: {z_score:.2f}")

    return is_spike, z_score

def run_review_spike_detection(
    product_ids_to_monitor: list[str],
    current_time_window_start: datetime,
    window_duration_minutes: int = 60, # e.g., hourly aggregates
    historical_baseline_days: int = 7, # e.g., use last 7 days of hourly data for baseline
    z_score_threshold: float = 3.0
):
    """
    Main function to orchestrate review spike detection.
    """
    print(f"\n--- Running Review Spike Detection for window starting {current_time_window_start} ---")

    for product_id in product_ids_to_monitor:
        print(f"\n  Processing product_id: {product_id}")
        
        # 1. Get latest review count for the current window
        latest_data = get_latest_velocity_data(product_id, current_time_window_start, window_duration_minutes)
        latest_review_count = latest_data["review_count"] if latest_data else 0

        # 2. Get historical review counts for baseline calculation
        # Fetch data up to the *previous* window to avoid data leakage for the current window's calculation
        history_end_time = current_time_window_start
        historical_raw_data = fetch_historical_velocity_data(product_id, history_end_time, window_duration_minutes, historical_baseline_days)
        historical_review_counts = [d["review_count"] for d in historical_raw_data if d["time_window_start"] < current_time_window_start]

        # 3. Detect spike
        is_spike, z_score = detect_review_spikes(
            product_id,
            latest_review_count,
            historical_review_counts,
            z_score_threshold
        )

        # 4. Generate flagging signal if spike detected
        if is_spike:
            anomaly_flag = {
                "product_id": product_id,
                "anomaly_type": "ReviewVelocitySpike",
                "timestamp": current_time_window_start + timedelta(minutes=window_duration_minutes), # End of the window
                "score": z_score,
                "reason": f"Sudden review spike detected (Z-score: {z_score:.2f} > Threshold: {z_score_threshold:.1f})",
                "details": {
                    "latest_count": latest_review_count,
                    "baseline_mean": sum(historical_review_counts) / len(historical_review_counts) if historical_review_counts else 0,
                    "baseline_std_dev": math.sqrt(sum((x - (sum(historical_review_counts) / len(historical_review_counts)))**2 for x in historical_review_counts) / len(historical_review_counts)) if historical_review_counts else 0
                }
            }
            publish_anomaly_flag(anomaly_flag)
        else:
            print(f"  [SPIKE] No significant spike detected for {product_id}.")

# Example usage (in a real system, this would be scheduled after ingestion for a time window)
# if __name__ == "__main__":
#     now = datetime.now().replace(second=0, microsecond=0)
#     # Align to the start of the current hour for hourly aggregation
#     current_hourly_window_start = now.replace(minute=0) 
#     
#     # Simulate monitoring a few products
#     products = ["prod_A", "prod_B", "prod_C"]
#     run_review_spike_detection(products, current_hourly_window_start)
```