# data_ingestion/historical_backfill_spark_job.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month, dayofmonth, lit, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, ArrayType

# Assuming REVIEW_SCHEMA_DEFINITION is imported or defined here
# from data_lake.schemas.review_schema import REVIEW_SCHEMA_DEFINITION

# Define the PySpark schema directly for use in Spark
pyspark_review_schema = StructType([
    StructField("review_id", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("reviewer_id", StringType(), False),
    StructField("star_rating", IntegerType(), False),
    StructField("review_headline", StringType(), True),
    StructField("review_body", StringType(), False),
    StructField("review_date", StringType(), False), # "YYYY-MM-DDTHH:MM:SSZ"
    StructField("helpful_votes", IntegerType(), False),
    StructField("total_votes", IntegerType(), False),
    StructField("verified_purchase", BooleanType(), False),
    StructField("product_title", StringType(), True),
    StructField("product_category", StringType(), True),
    StructField("reviewer_name", StringType(), True),
    StructField("reviewer_profile_link", StringType(), True),
    StructField("marketplace", StringType(), False),
    StructField("review_url", StringType(), True),
    StructField("image_urls", ArrayType(StringType()), True)
])


def run_historical_backfill(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    file_format: str = "json" # Can be 'csv', 'json', etc.
):
    """
    Executes the historical data backfill Spark job.

    Args:
        spark (SparkSession): The SparkSession object.
        input_path (str): S3 path to the historical raw review data.
        output_path (str): S3 path for the processed review data in the data lake.
        file_format (str): Format of the input historical files (e.g., 'json', 'csv').
    """
    print(f"Starting historical backfill from {input_path} to {output_path}")

    # 1. Read historical data
    if file_format == "json":
        raw_df = spark.read.schema(pyspark_review_schema).json(input_path)
    elif file_format == "csv":
        # Assuming CSV has a header and specific options
        raw_df = spark.read.option("header", "true").option("inferSchema", "false").csv(input_path)
        # Further transformations would be needed here to match CSV columns to schema
        # For simplicity, we assume JSON-like structure or pre-processed CSV.
        # A more robust solution would involve a mapping configuration.
        raise NotImplementedError("CSV parsing and schema mapping for historical data not fully implemented in pseudocode.")
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    print(f"Read {raw_df.count()} records from {input_path}")

    # 2. Apply schema enforcement and transformations
    # This example assumes the raw JSON data closely matches the target schema.
    # In a real scenario, you'd have more complex transformations to align disparate source schemas.
    processed_df = raw_df.select(
        col("review_id").cast(StringType()).alias("review_id"),
        col("product_id").cast(StringType()).alias("product_id"),
        col("reviewer_id").cast(StringType()).alias("reviewer_id"),
        col("star_rating").cast(IntegerType()).alias("star_rating"),
        col("review_headline").cast(StringType()).alias("review_headline"),
        col("review_body").cast(StringType()).alias("review_body"),
        col("review_date").cast(StringType()).alias("review_date"), # Keep as string for partitioning
        col("helpful_votes").cast(IntegerType()).alias("helpful_votes"),
        col("total_votes").cast(IntegerType()).alias("total_votes"),
        col("verified_purchase").cast(BooleanType()).alias("verified_purchase"),
        col("product_title").cast(StringType()).alias("product_title"),
        col("product_category").cast(StringType()).alias("product_category"),
        col("reviewer_name").cast(StringType()).alias("reviewer_name"),
        col("reviewer_profile_link").cast(StringType()).alias("reviewer_profile_link"),
        col("marketplace").cast(StringType()).alias("marketplace"),
        col("review_url").cast(StringType()).alias("review_url"),
        col("image_urls").cast(ArrayType(StringType())).alias("image_urls")
    ).na.fill(0, ["star_rating", "helpful_votes", "total_votes"])\
    .na.fill(False, ["verified_purchase"])\
    .na.fill("UNKNOWN", ["marketplace"]) # Default if missing


    # Add partitioning columns based on review_date
    # Assuming review_date is in "YYYY-MM-DDTHH:MM:SSZ" format
    processed_df = processed_df.withColumn("year", year(to_date(col("review_date"), "yyyy-MM-dd'T'HH:mm:ss'Z' Harris"))\
                               .withColumn("month", month(to_date(col("review_date"), "yyyy-MM-dd'T'HH:mm:ss'Z' Harris"))\
                               .withColumn("day", dayofmonth(to_date(col("review_date"), "yyyy-MM-dd'T'HH:mm:ss'Z' Harris"))

    # 3. Write to data lake in Parquet format, partitioned
    # Using 'overwrite' mode for specific partitions can ensure idempotency
    # However, for initial backfill, 'overwrite' on the whole output_path might be simpler if no existing data.
    # For incremental backfill, you'd calculate specific partitions to overwrite.
    processed_df.write \
        .mode("overwrite")  # Use overwrite for initial backfill of full dataset or specific partitions
        .partitionBy("marketplace", "year", "month", "day") \
        .parquet(output_path)

    print(f"Successfully backfilled data to {output_path}")

if __name__ == '__main__':
    spark = SparkSession.builder \
        .appName("AmazonReviewHistoricalBackfill") \
        .getOrCreate()

    # Example Usage:
    # input_s3_path = "s3a://amazon-reviews-raw-historical/reviews_2020.json"
    # output_s3_path = "s3a://amazon-reviews-data-lake/processed-reviews/"

    # Replace with actual S3 paths
    input_s3_path = "s3a://your-raw-historical-data-bucket/path/to/historical_reviews.json"
    output_s3_path = "s3a://amazon-reviews-data-lake/processed-reviews/"

    run_historical_backfill(spark, input_s3_path, output_s3_path, file_format="json")

    spark.stop()
