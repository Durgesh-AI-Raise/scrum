## Task 1.3: Set up data storage for ingested reviews

### Implementation Plan:
This task involves setting up two primary storage solutions using AWS services:

1.  **Raw Data Lake (Amazon S3):**
    *   **Purpose:** Store all incoming raw review data as received from the ingestion connector.
    *   **Benefits:** Provides durable, cost-effective, and scalable storage for historical data, enabling re-processing, auditing, and future analytical needs.
    *   **Mechanism:** An Amazon Kinesis Firehose delivery stream will be configured to automatically consume data from the `amazon-reviews-stream` Kinesis Data Stream and deliver it to S3.
    *   **Data Partitioning:** Data will be stored with a date-based prefix structure to optimize querying and data lifecycle management.

2.  **Processed/Structured Storage (Amazon DynamoDB):**
    *   **Purpose:** Store validated and parsed review data for fast access by the ML pipeline and the investigator dashboard.
    *   **Benefits:** Offers low-latency, high-throughput access suitable for operational data.
    *   **Mechanism:** A subsequent processing Lambda (Task 1.4) will read from Kinesis, validate/parse reviews, and write them to this DynamoDB table.

### Data Models and Architecture (Storage Specifics):

*   **Amazon S3 Raw Data Lake:**
    *   **Bucket Name:** `amazon-reviews-raw-data-lake`
    *   **Object Prefix Structure:** `raw-reviews/year=YYYY/month=MM/day=DD/ingestion_timestamp_review_id.json`
        *   Example: `raw-reviews/year=2024/month=11/day=03/20241103T183000Z_R001.json`
    *   **Content:** Raw JSON review objects as received from the ingestion connector.

*   **Amazon DynamoDB Table:**
    *   **Table Name:** `amazon-reviews-processed`
    *   **Primary Key:**
        *   `review_id` (String) - Partition Key
    *   **Global Secondary Index (GSI):**
        *   **Index Name:** `product_id-review_date-index`
        *   **Partition Key:** `product_id` (String)
        *   **Sort Key:** `review_date` (String - ISO 8601)
        *   **Purpose:** To efficiently query reviews for a specific product, potentially ordered by date.
    *   **Key Attributes (Example):**
        *   `review_id` (String)
        *   `product_id` (String)
        *   `user_id` (String)
        *   `stars` (Number)
        *   `review_title` (String)
        *   `review_body` (String)
        *   `review_date` (String - ISO 8601)
        *   `verified_purchase` (Boolean)
        *   `helpful_votes` (Number)
        *   `reviewer_name` (String)
        *   `ingestion_timestamp` (String - ISO 8601) - When review entered our system.
        *   `processed_timestamp` (String - ISO 8601) - When review was processed by validation/parsing.
        *   `validation_status` (String - e.g., 'VALID', 'INVALID', 'MISSING_FIELD')
        *   `ml_abuse_score` (Number, *will be added later*)
        *   `flagged_reason` (List of Strings, *will be added later*)

### Assumptions and Technical Decisions:
*   **Assumption:** AWS services are suitable for the expected data volume, velocity, and access patterns.
*   **Decision:** Amazon S3 is chosen as the raw data lake due to its scalability, durability, and cost-effectiveness for storing large volumes of unstructured/semi-structured data.
*   **Decision:** Amazon DynamoDB is selected for processed data due to its low-latency reads/writes, high availability, and ability to handle flexible schemas (NoSQL) for the varying review attributes.
*   **Decision:** Kinesis Firehose simplifies the process of moving data from Kinesis Data Streams to S3, reducing the need for custom Lambda functions for this specific transfer.
*   **Decision:** Date-based partitioning in S3 (`year=YYYY/month=MM/day=DD/`) is a best practice for data lakes, optimizing data retrieval and enabling efficient lifecycle management (e.g., archiving older data).
*   **Decision:** A Global Secondary Index (GSI) on `product_id` and `review_date` in DynamoDB is crucial for enabling efficient queries from the ML pipeline and the investigator dashboard that might need to retrieve reviews based on product.

### Conceptual Infrastructure as Code (CloudFormation Snippets):

**1. Amazon S3 Bucket for Raw Data Lake:**
```yaml
# snippet from cloudformation/s3.yaml or similar
Resources:
  AmazonReviewsRawDataLakeBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: amazon-reviews-raw-data-lake
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: ArchiveOldRawReviews
            Status: Enabled
            Transitions:
              - TransitionInDays: 30
                StorageClass: GLACIER_IR # or INTELLIGENT_TIERING
            # ... further rules for deletion etc.
      Tags:
        - Key: Project
          Value: ReviewAbuseDetection
        - Key: Environment
          Value: Dev
```

**2. Amazon Kinesis Firehose Delivery Stream (connecting Kinesis to S3):**
```yaml
# snippet from cloudformation/firehose.yaml or similar
Resources:
  KinesisToS3FirehoseDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: amazon-reviews-to-s3-firehose
      DeliveryStreamType: KinesisStreamAsSource
      KinesisStreamSourceConfiguration:
        KinesisStreamARN: !GetAtt AmazonReviewsStream.Arn # Assumes Kinesis stream is defined elsewhere
        RoleARN: !GetAtt FirehoseRole.Arn # Assumes an IAM role for Firehose is defined
      ExtendedS3DestinationConfiguration:
        BucketARN: !GetAtt AmazonReviewsRawDataLakeBucket.Arn
        Prefix: raw-reviews/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/
        ErrorOutputPrefix: raw-reviews-error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/
        BufferingHints:
          IntervalInSeconds: 300 # Buffer for 5 minutes
          SizeInMBs: 5 # Buffer up to 5 MB
        CompressionFormat: UNCOMPRESSED # Or GZIP, ZIP, SNAPPY, HADOOP_SNAPPY
        EncryptionConfiguration:
          NoEncryptionConfig: NoEncryption
        RoleARN: !GetAtt FirehoseRole.Arn
        CloudWatchLoggingOptions:
          Enabled: true
          LogGroupName: /aws/kinesisfirehose/amazon-reviews-to-s3
          LogStreamName: S3Delivery
```

**3. Amazon DynamoDB Table for Processed Reviews:**
```yaml
# snippet from cloudformation/dynamodb.yaml or similar
Resources:
  AmazonReviewsProcessedTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: amazon-reviews-processed
      AttributeDefinitions:
        - AttributeName: review_id
          AttributeType: S
        - AttributeName: product_id
          AttributeType: S
        - AttributeName: review_date
          AttributeType: S
      KeySchema:
        - AttributeName: review_id
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: 5 # Adjust based on expected read load
        WriteCapacityUnits: 5 # Adjust based on expected write load from processing Lambda
      GlobalSecondaryIndexes:
        - IndexName: product_id-review_date-index
          KeySchema:
            - AttributeName: product_id
              KeyType: HASH
            - AttributeName: review_date
              KeyType: RANGE
          Projection:
            ProjectionType: ALL # Project all attributes to the index
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5
      Tags:
        - Key: Project
          Value: ReviewAbuseDetection
        - Key: Environment
          Value: Dev
```
