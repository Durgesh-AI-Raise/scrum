### US1.1: Data Ingestion Pipeline

**Sprint Goal:** Establish the foundational data ingestion for the Amazon Review Integrity Engine (ARIE).

---

#### Task 1.1.1: Design review data storage schema

*   **Implementation Plan:**
    *   Define the fields required for raw review data: `review_id`, `reviewer_id`, `product_id`, `stars`, `review_text`, `review_timestamp`, `purchase_date`, `purchase_details`, `review_source`, and `ingestion_timestamp`.
    *   Choose a data storage solution suitable for high-volume, potentially unstructured or semi-structured data.
    *   Consider partitioning strategies for efficient querying and data retention.
*   **Data Models/Architecture:**
    *   **`reviews`** (Raw Review Data): Data Lake (S3 + Parquet) or NoSQL Document Store (e.g., MongoDB, DynamoDB).
    *   Schema: Defined in `docs/arie_data_models.md` under **1. `reviews` (Raw Review Data)**.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Data Lake (S3 + Parquet) for historical and raw new data storage due to its scalability, cost-effectiveness, and suitability for large volumes of semi-structured data. A NoSQL database is also a viable option if more granular document-level operations are prioritized.
    *   **Assumption:** `review_id`, `reviewer_id`, and `product_id` are universally unique identifiers.
    *   **Assumption:** `purchase_details` can be semi-structured (JSON).

---

#### Task 1.1.2: Implement ETL for historical review data

*   **Implementation Plan:**
    *   **Extraction:** Connect to Amazon's existing databases (e.g., relational databases like RDS PostgreSQL, or data warehouses like Redshift).
    *   **Transformation:**
        *   Cleanse data (handle nulls, inconsistent formats).
        *   Map existing schema to the `reviews` data model.
        *   Standardize timestamps to ISO 8601 UTC.
        *   Add `ingestion_timestamp` upon loading into ARIE.
    *   **Loading:** Write transformed data to the chosen Data Lake storage (e.g., S3 in Parquet format). Implement batch processing for large historical datasets.
    *   **Orchestration:** Use a workflow management tool (e.g., Apache Airflow, AWS Step Functions) to schedule and monitor the ETL jobs.
*   **Data Models/Architecture:**
    *   Source: Amazon's existing databases.
    *   Target: S3 Data Lake (Parquet files).
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Apache Spark for ETL due to its distributed processing capabilities for large datasets and native support for various data sources/sinks.
    *   **Decision:** Data will be stored in Parquet format in S3 for columnar storage benefits, which improves query performance and reduces storage costs.
    *   **Assumption:** Access to Amazon's internal databases is granted with appropriate credentials and network configurations.
    *   **Assumption:** Historical data volume requires batch processing, not real-time streaming, for initial ingestion.
*   **Code Snippets/Pseudocode:**

    ```python
    # Pseudocode for historical ETL using Apache Spark
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import current_timestamp, lit, to_timestamp
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, MapType, FloatType

    def historical_etl(source_db_conn_str, source_table, s3_output_path, db_user, db_password):
        spark = SparkSession.builder \
            .appName("HistoricalReviewETL") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.2.19") \
            .getOrCreate()

        # 1. Extract from a relational database (e.g., PostgreSQL)
        df = spark.read \
            .format("jdbc") \
            .option("url", source_db_conn_str) \
            .option("dbtable", source_table) \
            .option("user", db_user) \
            .option("password", db_password) \
            .load()

        # Define a schema for purchase_details if it's not a direct JSON string in source
        # For simplicity, assuming it might be constructed or is nullable
        purchase_details_schema = StructType([
            StructField("price", FloatType(), True),
            StructField("currency", StringType(), True)
        ])

        # 2. Transform
        transformed_df = df.select(
            col("legacy_review_id").alias("review_id"),
            col("customer_id").alias("reviewer_id"),
            col("product_asin").alias("product_id"),
            col("star_rating").cast(IntegerType()).alias("stars"),
            col("review_body").alias("review_text"),
            to_timestamp(col("submission_date"), "yyyy-MM-dd HH:mm:ss").alias("review_timestamp"), # Example date format
            to_timestamp(col("purchase_dt"), "yyyy-MM-dd").alias("purchase_date"), # Example date format, nullable
            # Assuming 'purchase_details_json_string_column' if available, otherwise constructing a null map
            lit(None).cast(MapType(StringType(), StringType())).alias("purchase_details"), # Placeholder for purchase details
            lit("Amazon.com").alias("review_source"), # Default for historical data source
            current_timestamp().alias("ingestion_timestamp")
        )

        # 3. Load to S3 in Parquet format, partitioned by ingestion date for efficient querying
        transformed_df.write \
            .mode("overwrite") \
            .partitionBy("ingestion_timestamp") \
            .parquet(s3_output_path)

        spark.stop()

    # Example usage (placeholders for sensitive info):
    # db_url = "jdbc:postgresql://<host>:<port>/<database>"
    # db_table = "amazon_reviews_legacy"
    # s3_path = "s3a://arie-raw-data/reviews/historical/"
    # user = "your_db_user"
    # password = "your_db_password"
    # historical_etl(db_url, db_table, s3_path, user, password)
    ```

---

#### Task 1.1.3: Implement real-time streaming for new review data

*   **Implementation Plan:**
    *   **Source:** Identify the source of new review data (e.g., Kafka topic, Kinesis stream, message queue).
    *   **Ingestion Pipeline:** Use a streaming processing framework (e.g., Apache Flink, Spark Streaming, AWS Kinesis Data Firehose) to consume messages.
    *   **Transformation:** Apply similar cleansing, mapping, and timestamp standardization as the historical ETL. Add `ingestion_timestamp`.
    *   **Loading:** Write processed data to the Data Lake (S3 in Parquet format), potentially micro-batching for efficiency.
*   **Data Models/Architecture:**
    *   Source: Real-time message queue/stream (e.g., Kafka, Kinesis).
    *   Target: S3 Data Lake (Parquet files).
*   **Assumptions/Technical Decisions:**
    *   **Decision:** Apache Flink for real-time streaming due to its low-latency processing capabilities, robust state management, and exactly-once processing guarantees for critical data. AWS Kinesis Data Firehose could also be used for simpler ingestion to S3 if complex transformations/state are not immediately required.
    *   **Assumption:** New review data is available through a high-throughput, low-latency streaming service (e.g., Kafka or Kinesis).
    *   **Assumption:** Data volume necessitates distributed streaming processing for continuous ingestion.
*   **Code Snippets/Pseudocode:**

    ```python
    # Pseudocode for real-time streaming ingestion using Apache Flink (PyFlink)
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    from pyflink.common.serialization import SimpleStringSchema
    from pyflink.datastream.formats.json import JsonRowDeserializationSchema
    from pyflink.common.typeinfo import Types
    from pyflink.datastream.functions import MapFunction
    from datetime import datetime, timezone
    import json

    class ReviewDataTransformer(MapFunction):
        def map(self, value):
            # 'value' is a Row object parsed from JSON, assuming source JSON matches target schema broadly
            # Perform necessary transformations, type conversions, and standardization
            purchase_details = value.get_field_as("purchase_details") # Assuming it comes as a map or dict

            return {
                "review_id": value.get_field_as("review_id"),
                "reviewer_id": value.get_field_as("reviewer_id"),
                "product_id": value.get_field_as("product_id"),
                "stars": int(value.get_field_as("stars")),
                "review_text": value.get_field_as("review_text"),
                "review_timestamp": datetime.fromisoformat(value.get_field_as("review_timestamp").replace('Z', '+00:00')).isoformat(timespec='seconds') + 'Z',
                "purchase_date": datetime.fromisoformat(value.get_field_as("purchase_date").replace('Z', '+00:00')).isoformat(timespec='seconds') + 'Z' if value.get_field_as("purchase_date") else None,
                "purchase_details": json.dumps(purchase_details) if purchase_details else None, # Store as JSON string or directly as MapType
                "review_source": value.get_field_as("source_application"), # Example mapping from source field
                "ingestion_timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
            }

    def real_time_streaming_pipeline(kafka_bootstrap_servers, kafka_topic, s3_output_path):
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(1) # Configure parallelism appropriately for production

        # Define the schema for deserializing Kafka messages from JSON
        json_row_type_info = Types.ROW_NAMED(
            ["review_id", "reviewer_id", "product_id", "stars", "review_text",
             "review_timestamp", "purchase_date", "purchase_details", "source_application"],
            [Types.STRING(), Types.STRING(), Types.STRING(), Types.INT(), Types.STRING(),
             Types.STRING(), Types.STRING(), Types.MAP(Types.STRING(), Types.STRING()), Types.STRING()]
        )
        json_deserialization_schema = JsonRowDeserializationSchema.builder().type_info(json_row_type_info).build()

        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(kafka_bootstrap_servers) \
            .set_topics(kafka_topic) \
            .set_starting_offsets_initializer(KafkaOffsetsInitializer.latest()) \
            .set_value_deserializer(json_deserialization_schema) \
            .build()

        ds = env.from_source(kafka_source, "kafka-reviews-source", SimpleStringSchema())

        # Apply transformation
        transformed_ds = ds.map(ReviewDataTransformer(), output_type=Types.MAP(Types.STRING(), Types.STRING()))

        # For sinking to S3 in Parquet format, PyFlink typically integrates with Table API/SQL or custom sinks.
        # A direct Python DataStream sink to S3 Parquet is complex for a simple snippet.
        # In a real Flink setup, one would use:
        # 1. Flink Table API with a filesystem connector (e.g., 'parquet')
        #    e.g., env.add_source(...).to_table().execute_insert("INSERT INTO my_s3_table ...")
        # 2. Custom RichSinkFunction to write to S3 in Parquet, potentially using ParquetWriter.

        # Pseudocode for S3 sink (conceptual):
        # transformed_ds.add_sink(S3ParquetSinkFunction(s3_output_path, partition_by_ingestion_date=True))
        print(f"Flink pipeline configured to read from {kafka_topic} and process for S3 sink at {s3_output_path}")

        env.execute("Real-time Review Ingestion Pipeline")

    # Example usage:
    # kafka_servers = "localhost:9092"
    # kafka_topic_name = "new-amazon-reviews"
    # s3_realtime_path = "s3a://arie-raw-data/reviews/realtime/"
    # real_time_streaming_pipeline(kafka_servers, kafka_topic_name, s3_realtime_path)
    ```

---

#### Task 1.1.4: Set up data validation and error handling for ingestion

*   **Implementation Plan:**
    *   **Schema Validation:** Enforce schema checks (e.g., using Apache Avro/Parquet schema for Data Lake, JSON schema validation for NoSQL).
    *   **Data Type Validation:** Ensure fields conform to expected data types (e.g., `stars` is an integer between 1 and 5, timestamps are valid ISO 8601).
    *   **Mandatory Field Checks:** Verify the presence and non-nullability of critical fields like `review_id`, `reviewer_id`, `product_id`.
    *   **Duplicate Detection:** Implement mechanisms to detect and handle duplicate reviews (e.g., based on `review_id` for idempotency).
    *   **Error Logging:** Log all validation failures with details (record ID, error type, field, raw message).
    *   **Dead Letter Queue (DLQ):** For streaming data, push failed records that cannot be processed to a DLQ for later investigation and reprocessing without blocking the main pipeline.
    *   **Alerting:** Set up alerts for high volumes of errors, schema mismatches, or pipeline failures.
*   **Data Models/Architecture:**
    *   Validation logic integrated directly into ETL/streaming jobs.
    *   DLQ (e.g., Kafka topic, SQS queue, or S3 bucket for error files) for erroneous records.
    *   Monitoring system (e.g., Prometheus, Grafana, CloudWatch) for metrics and alerts on data quality.
*   **Assumptions/Technical Decisions:**
    *   **Decision:** For batch (historical) data, use data quality frameworks (e.g., Great Expectations, Deequ) to define and enforce rules before loading.
    *   **Decision:** For streaming data, custom validation logic will be implemented within the Flink application. Records failing validation will be routed to a dedicated Kafka topic (DLQ) for errors, along with detailed error messages.
    *   **Assumption:** A comprehensive logging and monitoring infrastructure is already in place or will be established to capture validation failures and trigger alerts.
*   **Code Snippets/Pseudocode:**

    ```python
    # Pseudocode for data validation in a streaming context (e.g., Flink MapFunction or ProcessFunction)
    from datetime import datetime, timezone
    import json

    def validate_review_record(review_data_map):
        errors = []
        is_valid = True

        # 1. Check for mandatory fields
        required_fields = ["review_id", "reviewer_id", "product_id", "stars", "review_text", "review_timestamp"]
        for field in required_fields:
            if field not in review_data_map or review_data_map[field] is None:
                errors.append(f"Missing or null required field: {field}")
                is_valid = False

        # If mandatory fields are missing, further validation might be pointless or cause errors
        if not is_valid:
            return False, errors

        # 2. Data Type and Value Range Validation
        try:
            stars = int(review_data_map["stars"])
            if not (1 <= stars <= 5):
                errors.append(f"Invalid 'stars' value: {review_data_map['stars']}. Must be an integer between 1 and 5.")
                is_valid = False
        except (ValueError, TypeError):
            errors.append(f"Invalid 'stars' data type: {review_data_map['stars']}. Must be an integer.")
            is_valid = False

        try:
            # Standardize 'Z' to '+00:00' for Python's datetime.fromisoformat in older versions if necessary
            datetime.fromisoformat(review_data_map["review_timestamp"].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            errors.append(f"Invalid 'review_timestamp' format: {review_data_map['review_timestamp']}. Must be ISO 8601.")
            is_valid = False

        if review_data_map.get("purchase_date"):
            try:
                datetime.fromisoformat(review_data_map["purchase_date"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append(f"Invalid 'purchase_date' format: {review_data_map['purchase_date']}. Must be ISO 8601 or null.")
                is_valid = False

        # Add more specific validation rules:
        # - Review text length (e.g., min/max characters)
        # - Product ID / Reviewer ID format (regex validation)
        # - Check for excessively long strings that might indicate malformed data

        return is_valid, errors

    # Example of integrating into a Flink process (conceptual):
    # class ValidatingReviewProcessor(ProcessFunction):
    #     def process_element(self, value, ctx: ProcessFunction.Context):
    #         is_valid, errors = validate_review_record(value)
    #         if is_valid:
    #             # Emit to main output stream
    #             ctx.output(self.main_output_tag, value)
    #         else:
    #             # Create an error record
    #             error_record = {
    #                 "original_data": value,
    #                 "validation_errors": errors,
    #                 "error_timestamp": datetime.now(timezone.utc).isoformat()
    #             }
    #             # Emit to side output (DLQ)
    #             ctx.output(self.dlq_output_tag, json.dumps(error_record))

    # In the main Flink pipeline:
    # main_stream, dlq_stream = my_source_stream.process(ValidatingReviewProcessor()).split()
    # dlq_stream.add_sink(KafkaSinkForDLQ())
    # main_stream.add_sink(S3ParquetSink())
    ```
