from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, date_format, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType

# Define the schema for review data
review_schema = StructType([
    StructField("review_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("reviewer_id", StringType(), True),
    StructField("rating", IntegerType(), True),
    StructField("text", StringType(), True),
    StructField("timestamp", LongType(), True) # Using LongType for Unix timestamp
])

spark = SparkSession.builder \
    .appName("AmazonReviewProcessorAndRawStorage") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.1") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.access.key", "YOUR_AWS_ACCESS_KEY") \
    .config("spark.hadoop.fs.s3a.secret.key", "YOUR_AWS_SECRET_KEY") \
    .getOrCreate()

# Read from Kafka (raw byte value)
kafka_stream = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "amazon_raw_reviews") \
    .load()

# Select the raw value (bytes) and convert to string, add ingestion timestamp
# For raw storage, we store the original raw JSON string directly.
raw_data_for_s3 = kafka_stream.selectExpr("CAST(value AS STRING) as raw_json_data") \
    .withColumn("ingestion_time", current_timestamp()) \
    .withColumn("ingestion_date", date_format(col("ingestion_time"), "yyyy-MM-dd"))

# Write raw data to S3 in JSON format, partitioned by date
# This stores the *original* JSON messages.
query_raw_s3 = raw_data_for_s3 \
    .writeStream \
    .outputMode("append") \
    .format("json") \
    .option("path", "s3a://amazon-review-data-raw/reviews_raw/") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/raw_reviews_s3") \
    .partitionBy("ingestion_date") \
    .start()

# --- Processing for validated data (can be written to another Kafka topic or directly to curated DB) ---
# Parse JSON and apply schema for validation
parsed_reviews = kafka_stream.selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), review_schema).alias("data")) \
    .select("data.*")

# Basic validation: check for nulls in required fields
validated_reviews = parsed_reviews.filter(
    (col("review_id").isNotNull()) &
    (col("product_id").isNotNull()) &
    (col("reviewer_id").isNotNull()) &
    (col("rating").isNotNull()) &
    (col("text").isNotNull()) &
    (col("timestamp").isNotNull())
)

# For now, print validated data to console. In later tasks, this would go to curated storage.
query_validated_console = validated_reviews \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Wait for both streams to terminate
# In a real setup, these would be separate apps or managed differently.
# For this exercise, assume one of them would be commented out
# or run as separate spark-submit jobs.
query_raw_s3.awaitTermination()
# query_validated_console.awaitTermination()