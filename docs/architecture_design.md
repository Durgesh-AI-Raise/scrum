# Sprint Goal: Establish foundational data ingestion for Amazon product reviews and reviewer profiles.

## Overall Architecture for Data Ingestion

The proposed architecture follows a lambda-like approach, combining real-time streaming with batch processing capabilities for robust data ingestion.

```mermaid
graph TD
    A[Amazon Data Sources: Reviews, Profiles] --> B(Data Connectors);
    B --> C[Raw Kafka Topics];
    C --> D[Spark Streaming Processors];
    D --> E[Raw Data Lake (S3)];
    D --> F[Curated Data Warehouse (PostgreSQL)];
    F --> G[Downstream Analytics & Abuse Detection];
```

**Components:**

*   **Amazon Data Sources:** External sources providing review and reviewer profile data (assumed to be APIs, data dumps, or scrape-able public pages).
*   **Data Connectors:** Services/scripts responsible for fetching data from the sources and publishing it to Kafka.
*   **Raw Kafka Topics:** Apache Kafka serves as a reliable, scalable message bus to decouple data producers (connectors) from consumers (processors). Separate topics for raw reviews and raw profiles.
*   **Spark Streaming Processors:** Apache Spark Structured Streaming jobs consume data from Kafka, perform parsing, schema validation, and initial transformations.
*   **Raw Data Lake (S3):** Amazon S3 (or equivalent object storage) used to store raw, untransformed data. This provides a low-cost, highly durable storage for re-processing if needed. Data is stored as JSON and partitioned by ingestion date.
*   **Curated Data Warehouse (PostgreSQL):** A relational database (PostgreSQL chosen for its maturity, ACID properties, and ease of integration) to store structured, validated, and potentially slightly transformed data. This serves as the primary source for downstream analytics and abuse detection systems.
*   **Downstream Analytics & Abuse Detection:** Future components that will consume data from the Curated Data Warehouse.

---

## 1) Sprint Backlog: Implementation Plan, Data Models, Architecture, Assumptions, Technical Decisions, and Code Snippets

---

### **US1.1: Data Ingestion for Reviews**

#### **Task 1: Design data ingestion pipeline architecture**
*   **Implementation Plan:** Design a scalable and fault-tolerant data ingestion pipeline leveraging Apache Kafka for message queuing, Apache Spark for real-time processing, and AWS S3 for raw data storage. A relational database (PostgreSQL) will be used for the curated layer.
*   **Data Models & Architecture:**
    *   **Source:** Amazon product reviews (assumed via API/file dumps/web scraping).
    *   **Ingestion:** Python connector -> Kafka topic (`amazon_raw_reviews`).
    *   **Processing:** Spark Streaming job (parsing, validation).
    *   **Storage:** Raw JSON in S3 (raw data lake), structured data in PostgreSQL (curated data warehouse).
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** We can access Amazon review data, either via an API, file dumps, or by web scraping public data. For MVP, we simulate this.
    *   **Decision:** Apache Kafka for robust message queuing. Apache Spark for distributed, real-time data processing. AWS S3 for cost-effective raw data storage. PostgreSQL for structured curated data.

#### **Task 2: Implement initial review data connector**
*   **Implementation Plan:** Develop a Python script to simulate fetching Amazon product review data and publish it as JSON messages to a Kafka topic (`amazon_raw_reviews`).
*   **Data Models & Architecture:**
    *   **Output Data Schema (JSON):**
        ```json
        {
          "review_id": "string",
          "product_id": "string",
          "reviewer_id": "string",
          "rating": "integer (1-5)",
          "text": "string",
          "timestamp": "integer (Unix epoch)"
        }
        ```
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** Kafka broker is accessible at `localhost:9092` for development.
    *   **Decision:** Use `kafka-python` library for simplicity.

*   **Code Snippet (`data_ingestion/review_connector.py`):**
    ```python
    from kafka import KafkaProducer
    import json
    import time
    import random

    def get_amazon_reviews():
        """
        Placeholder for fetching reviews from Amazon source.
        In a real scenario, this would involve API calls,
        web scraping, or reading from a data dump.
        """
        reviews = []
        for i in range(1, 11): # Simulate 10 reviews
            reviews.append({
                "review_id": f"R{i}",
                "product_id": f"P{random.randint(100, 200)}",
                "reviewer_id": f"U{random.randint(1, 5)}",
                "rating": random.randint(1, 5),
                "text": f"This is a review for product P{random.randint(100, 200)}. It was {random.choice(['great', 'good', 'okay', 'bad', 'terrible'])}.",
                "timestamp": int(time.time() - random.randint(0, 30*24*60*60)) # Last 30 days
            })
        return reviews

    def produce_reviews_to_kafka(topic, reviews_data):
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'], # Replace with actual Kafka broker
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        for review in reviews_data:
            producer.send(topic, review)
            print(f"Sent review: {review['review_id']}")
        producer.flush()
        producer.close()

    if __name__ == "__main__":
        review_topic = "amazon_raw_reviews"
        reviews = get_amazon_reviews()
        produce_reviews_to_kafka(review_topic, reviews)
    ```

#### **Task 3: Develop data parsing and schema validation for review data**
#### **Task 4: Set up a basic data storage solution for raw review data**
*   **Implementation Plan:** Develop a PySpark Structured Streaming job that consumes raw JSON review data from the `amazon_raw_reviews` Kafka topic. It will perform schema validation against the defined review schema and then store the raw (unvalidated but parsed) data into an S3 bucket (raw data lake) in JSON format, partitioned by date. Validated data will be available for further processing.
*   **Data Models & Architecture:**
    *   **Review Data Spark Schema (`StructType`):**
        ```python
        StructType([
            StructField("review_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("reviewer_id", StringType(), True),
            StructField("rating", IntegerType(), True),
            StructField("text", StringType(), True),
            StructField("timestamp", LongType(), True)
        ])
        ```
    *   **Raw Data Lake Storage:** S3 path: `s3a://amazon-review-data-raw/reviews_raw/ingestion_date=YYYY-MM-DD/`
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** AWS S3 bucket `amazon-review-data-raw` exists and Spark has necessary IAM permissions.
    *   **Decision:** Combine parsing, validation, and raw storage into a single Spark job for efficiency. Use `checkpointLocation` for fault tolerance in Spark Structured Streaming.
    *   **Decision:** Store raw data as JSON in S3 for schema evolution flexibility and easy human readability.

*   **Code Snippet (`data_ingestion/review_processor_and_raw_storage.py`):**
    ```python
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
    ```

---

### **US1.2: Reviewer Profile Data Integration**

#### **Task 1: Identify sources for reviewer profile data**
*   **Implementation Plan:** Research Amazon public APIs (if available), consider web scraping public reviewer profiles, or simulate data based on expected attributes. For MVP, we'll simulate.
*   **Data Models & Architecture:**
    *   **Potential Sources:** Amazon Public API, web scraping, internal Amazon services.
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** Initial data will be simulated for core attributes to establish the pipeline. Later, we'll integrate with actual sources.
    *   **Decision:** Start with publicly available/simulated attributes.

#### **Task 2: Design data model for reviewer profiles**
*   **Implementation Plan:** Define a comprehensive schema for reviewer profiles, including core identifiers and behavioral metrics.
*   **Data Models & Architecture:**
    *   **Reviewer Profile Schema (JSON):**
        ```json
        {
          "reviewer_id": "string",
          "profile_name": "string",
          "join_date": "integer (Unix epoch)",
          "total_reviews": "integer",
          "helpful_votes_count": "integer",
          "is_prime_member": "boolean",
          "country": "string"
        }
        ```
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** `reviewer_id` is the primary key for profiles and links to review data.
    *   **Decision:** Use a flexible JSON schema to accommodate future attribute additions.

#### **Task 3: Implement connector for reviewer profile data**
*   **Implementation Plan:** Develop a Python script to simulate fetching reviewer profile data and publish it as JSON messages to a Kafka topic (`amazon_raw_profiles`).
*   **Data Models & Architecture:**
    *   **Output Data Schema (JSON):** (Same as Task 2)
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** Kafka broker is accessible at `localhost:9092`.
    *   **Decision:** Use `kafka-python` for consistency with review connector.

*   **Code Snippet (`data_ingestion/profile_connector.py`):**
    ```python
    from kafka import KafkaProducer
    import json
    import time
    import random

    def get_amazon_reviewer_profiles():
        """
        Placeholder for fetching reviewer profiles.
        Simulates fetching some profile data.
        """
        profiles = []
        for i in range(1, 6): # Simulate 5 profiles
            profiles.append({
                "reviewer_id": f"U{i}",
                "profile_name": f"ReviewerUser{i}",
                "join_date": int(time.time() - random.randint(1, 365*24*60*60)), # Random join date
                "total_reviews": random.randint(1, 100),
                "helpful_votes_count": random.randint(0, 500),
                "is_prime_member": random.choice([True, False]),
                "country": random.choice(["USA", "UK", "Germany"])
            })
        return profiles

    def produce_profiles_to_kafka(topic, profiles_data):
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'], # Replace with actual Kafka broker
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        for profile in profiles_data:
            producer.send(topic, profile)
            print(f"Sent profile: {profile['reviewer_id']}")
        producer.flush()
        producer.close()

    if __name__ == "__main__":
        profile_topic = "amazon_raw_profiles"
        profiles = get_amazon_reviewer_profiles()
        produce_profiles_to_kafka(profile_topic, profiles)
    ```

#### **Task 4: Develop data parsing and validation for reviewer profile data**
#### **Task 5: Integrate reviewer profile data into storage solution**
*   **Implementation Plan:** Develop a PySpark Structured Streaming job that consumes raw JSON profile data from the `amazon_raw_profiles` Kafka topic. It will perform schema validation against the defined profile schema and then upsert the validated, structured data into a PostgreSQL table (`reviewer_profiles`) in the curated data warehouse.
*   **Data Models & Architecture:**
    *   **Reviewer Profile Spark Schema (`StructType`):**
        ```python
        StructType([
            StructField("reviewer_id", StringType(), True),
            StructField("profile_name", StringType(), True),
            StructField("join_date", LongType(), True),
            StructField("total_reviews", IntegerType(), True),
            StructField("helpful_votes_count", IntegerType(), True),
            StructField("is_prime_member", BooleanType(), True),
            StructField("country", StringType(), True)
        ])
        ```
    *   **Curated Data Warehouse Storage (PostgreSQL):**
        *   **Database:** `amazon_abuse_detection`
        *   **Table:** `reviewer_profiles`
        *   **SQL DDL (Conceptual):**
            ```sql
            CREATE TABLE reviewer_profiles (
                reviewer_id VARCHAR(255) PRIMARY KEY,
                profile_name VARCHAR(255),
                join_date BIGINT,
                total_reviews INT,
                helpful_votes_count INT,
                is_prime_member BOOLEAN,
                country VARCHAR(100),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ```
*   **Assumptions & Technical Decisions:**
    *   **Assumption:** PostgreSQL database `amazon_abuse_detection` is set up and accessible.
    *   **Decision:** Use `foreachBatch` in Spark Structured Streaming for writing to PostgreSQL, allowing for more granular control over database interactions (though for simplicity, `append` mode is demonstrated, a true upsert would require a `MERGE` statement within the batch).

*   **Code Snippet (`data_ingestion/profile_processor_and_storage.py`):**
    ```python
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import from_json, col, current_timestamp
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, BooleanType

    # Define the schema for reviewer profile data
    profile_schema = StructType([
        StructField("reviewer_id", StringType(), True),
        StructField("profile_name", StringType(), True),
        StructField("join_date", LongType(), True),
        StructField("total_reviews", IntegerType(), True),
        StructField("helpful_votes_count", IntegerType(), True),
        StructField("is_prime_member", BooleanType(), True),
        StructField("country", StringType(), True)
    ])

    spark = SparkSession.builder \
        .appName("AmazonReviewerProfileProcessorAndStorage") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,org.postgresql:postgresql:42.5.0") \
        .getOrCreate()

    # Read from Kafka
    kafka_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "amazon_raw_profiles") \
        .load()

    # Parse JSON and apply schema
    parsed_profiles = kafka_stream.selectExpr("CAST(value AS STRING) as json_string") \
        .select(from_json(col("json_string"), profile_schema).alias("data")) \
        .select("data.*")

    # Basic validation: check for nulls in required fields
    validated_profiles = parsed_profiles.filter(
        (col("reviewer_id").isNotNull()) &
        (col("profile_name").isNotNull())
    ).withColumn("last_updated", current_timestamp()) # Add a last_updated timestamp

    # Function to write micro-batches to PostgreSQL
    def upsert_to_postgresql(df, epoch_id):
        # For simplicity, we are using 'append' mode.
        # For a true upsert, you would typically:
        # 1. Write to a temporary staging table.
        # 2. Execute a MERGE (or equivalent INSERT ON CONFLICT) statement
        #    from the staging table into the target table.
        # This requires more complex JDBC interactions or a custom Spark connector.
        # For this MVP, 'append' is used, assuming distinct records or
        # that downstream processing handles duplicates/updates.
        df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://localhost:5432/amazon_abuse_detection") \
            .option("dbtable", "reviewer_profiles") \
            .option("user", "admin") \
            .option("password", "password") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
        print(f"Processed batch {epoch_id} and appended to reviewer_profiles.")


    # Write validated profiles to PostgreSQL
    query = validated_profiles \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(upsert_to_postgresql) \
        .option("checkpointLocation", "/tmp/spark_checkpoint/profiles_pg") \
        .start()

    query.awaitTermination()
    