# Raw Review Data Storage Solution (Task 1.3)

## Overview
This document outlines the implementation plan for storing raw ingested reviews, leveraging AWS S3 as a scalable and durable data lake landing zone, integrated with AWS Kinesis Firehose for automated data delivery from the Kinesis Data Stream.

## Architecture Components & Flow

```mermaid
graph TD
    A[Review Source (Simulated/Scraper)] --> B[Kinesis Data Stream: Raw Reviews];
    B --> C{Kinesis Firehose: RawReviewsToS3FirehoseStream};
    C --> D[AWS S3: Raw Data Landing Zone (s3://review-data-lake/raw/)]
    D --> E[AWS Athena/Glue Catalog];
```

## Implementation Details

1.  **AWS S3 Bucket for Raw Data (`review-data-lake-raw-[account-id]`):**
    *   **Purpose:** Primary durable storage for all raw, unprocessed review events.
    *   **Configuration:**
        *   **Naming:** A unique bucket name (e.g., `review-data-lake-raw-dev-123456789012`) will be used to ensure global uniqueness and indicate environment/account.
        *   **Versioning:** (Optional for MVP, but recommended for production) Enable S3 versioning for data protection and recovery.
        *   **Lifecycle Policies:** (Future consideration) Define policies to transition data to lower-cost storage classes (e.g., Glacier) or expire after a certain period if raw data retention limits are in place.
        *   **Access Control:** IAM policies will govern access to this bucket, granting Kinesis Firehose write permissions.

2.  **AWS Kinesis Firehose Delivery Stream (`RawReviewsToS3FirehoseStream`):**
    *   **Purpose:** A fully managed service that automatically delivers streaming data from Kinesis Data Streams to S3.
    *   **Source:** Configured to read from the `RawReviewsStream` Kinesis Data Stream (created implicitly or explicitly in previous tasks).
    *   **Destination:** The `review-data-lake-raw-[account-id]` S3 bucket.
    *   **S3 Prefixing (Partitioning):** Crucial for data lake performance and cost. Firehose will be configured to use a time-based prefix:
        ```
        raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/
        ```
        This allows for efficient querying by filtering on specific time ranges without scanning the entire dataset.
    *   **Buffering Hints:**
        *   **Buffer Size:** e.g., 5 MB
        *   **Buffer Interval:** e.g., 300 seconds (5 minutes)
        *   Firehose will deliver data to S3 when either the buffer size or interval threshold is met, creating larger, more efficient S3 objects.
    *   **Compression:** Initially set to `UNCOMPRESSED` for raw JSON readability during development. Can be switched to `GZIP` or `SNAPPY` for production to save storage and improve query performance.
    *   **Error Output:** Configured to send records that fail delivery to S3 to an `errors/` prefix within the S3 bucket, allowing for later investigation.
    *   **CloudWatch Logging:** Enabled for Firehose to provide visibility into delivery status and any potential issues.

3.  **IAM Role for Firehose:**
    *   A dedicated IAM role will be created for the Firehose delivery stream.
    *   **Permissions:** This role will grant Firehose permissions to:
        *   Read from the `RawReviewsStream` Kinesis Data Stream (`kinesis:DescribeStream`, `kinesis:GetShardIterator`, `kinesis:GetRecords`).
        *   Write objects to the S3 raw data bucket (`s3:PutObject`, `s3:ListBucket`, etc.).
        *   Write logs to CloudWatch Logs (`logs:PutLogEvents`, `logs:CreateLogGroup`, `logs:CreateLogStream`).

## Data Model

The raw data stored in S3 will directly conform to the `Raw Review Data Model` (JSON format) as defined in `docs/architecture/ingestion_architecture.md`.

## Assumptions and Technical Decisions

*   **AWS Managed Services:** Heavy reliance on AWS managed services (S3, Kinesis Firehose) for scalability, reliability, and reduced operational overhead.
*   **Kinesis Firehose over Custom Lambda:** Firehose is chosen for its simplicity and built-in features for S3 delivery, batching, and error handling, making it suitable for establishing foundational storage quickly. For more complex, real-time transformations *before* raw storage, a custom Lambda could be considered in later sprints.
*   **Time-Based Partitioning:** This is a fundamental decision for optimizing future analytics and querying performance on the S3 data lake.
*   **Uncompressed Raw Data (Initial):** Storing raw JSON without compression initially simplifies debugging and verification. Compression will be a future optimization.
*   **Separate S3 Bucket:** A dedicated S3 bucket for raw data ensures clear separation of concerns and easier management.

## Conceptual Infrastructure as Code (CloudFormation-like Pseudocode)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: AWS resources for raw review data storage using S3 and Kinesis Firehose.

Parameters:
  EnvironmentName:
    Type: String
    Description: Name of the environment (e.g., dev, prod)
    Default: dev

Resources:
  # S3 Bucket for Raw Data Landing Zone
  ReviewDataLakeRawBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "review-data-lake-raw-${EnvironmentName}-${AWS::AccountId}"
      Tags:
        - Key: Project
          Value: FakeReviewDetection
        - Key: Environment
          Value: !Ref EnvironmentName

  # IAM Role for Kinesis Firehose to access Kinesis and S3
  FirehoseDeliveryRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: firehose.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: KinesisFirehoseS3DeliveryPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - s3:PutObject
                Resource:
                  - !GetAtt ReviewDataLakeRawBucket.Arn
                  - !Join ["/", [!GetAtt ReviewDataLakeRawBucket.Arn, "*"]]
              - Effect: Allow
                Action:
                  - kinesis:DescribeStream
                  - kinesis:GetShardIterator
                  - kinesis:GetRecords
                Resource: !Sub arn:aws:kinesis:${AWS::Region}:${AWS::AccountId}:stream/RawReviewsStream
              - Effect: Allow # For CloudWatch Logs
                Action:
                  - logs:PutLogEvents
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/kinesis/firehose/RawReviewsToS3DeliveryLogs:*
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/kinesis/firehose/RawReviewsToS3DeliveryLogs:log-stream:*

  # Kinesis Firehose Delivery Stream for Raw Reviews to S3
  RawReviewsToS3Firehose:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: !Sub "RawReviewsToS3FirehoseStream-${EnvironmentName}"
      DeliveryStreamType: KinesisStreamAsSource
      KinesisStreamSourceConfiguration:
        KinesisStreamARN: !Sub arn:aws:kinesis:${AWS::Region}:${AWS::AccountId}:stream/RawReviewsStream
        RoleARN: !GetAtt FirehoseDeliveryRole.Arn
      ExtendedS3DestinationConfiguration:
        BucketARN: !GetAtt ReviewDataLakeRawBucket.Arn
        RoleARN: !GetAtt FirehoseDeliveryRole.Arn
        # Dynamic partitioning for data lake
        Prefix: !Sub "raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
        # Buffering for S3 object creation
        BufferingHints:
          IntervalInSeconds: 300 # Buffer for 5 minutes
          SizeInMBs: 5         # Buffer up to 5 MB
        CompressionFormat: UNCOMPRESSED # Store raw JSON as-is
        # Error output for failed records
        ErrorOutputPrefix: !Sub "errors/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
        CloudWatchLoggingOptions:
          Enabled: true
          LogGroupName: /aws/kinesis/firehose/RawReviewsToS3DeliveryLogs
          LogStreamName: S3DeliveryLogs
```
