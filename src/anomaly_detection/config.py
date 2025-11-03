# Configuration for Review Velocity Anomaly Detection Service

# PostgreSQL database connection string
DB_CONNECTION_STRING = 'postgresql://user:password@localhost:5432/review_integrity_db'

# Time window for aggregation in hours (must match ingestion service)
TIME_WINDOW_HOURS = 1

# Number of historical time windows to consider for baseline calculation
LOOKBACK_WINDOWS_COUNT = 7 * 24 # e.g., 7 days of hourly data

# Z-score threshold for flagging an anomaly
Z_SCORE_THRESHOLD = 3.0

# Interval in seconds for the anomaly detection service to run
DETECTION_INTERVAL_SECONDS = 3600 # Run hourly