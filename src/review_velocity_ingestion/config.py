# Configuration for Review Velocity Data Ingestion Service

# Kafka broker(s) connection string
KAFKA_BROKERS = ['localhost:9092'] 

# Kafka topic for raw review events
KAFKA_TOPIC = 'review_events'

# PostgreSQL database connection string
DB_CONNECTION_STRING = 'postgresql://user:password@localhost:5432/review_integrity_db'

# Time window for aggregation in hours (e.g., 1 for hourly aggregation)
TIME_WINDOW_HOURS = 1

# Thresholds for positive and negative reviews
POSITIVE_RATING_THRESHOLD = 4 # Ratings >= this are considered positive
NEGATIVE_RATING_THRESHOLD = 2 # Ratings <= this are considered negative

# Buffer size before flushing to DB (number of processed events)
FLUSH_BUFFER_SIZE = 1000

# Flush interval in seconds if buffer size is not met
FLUSH_INTERVAL_SECONDS = 60