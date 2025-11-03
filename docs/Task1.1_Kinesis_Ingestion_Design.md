**Implementation Plan for Task 1.1: Design and set up real-time review ingestion pipeline**

*   **Choose a technology:** AWS Kinesis Data Streams. This aligns with the previous decision to use Kinesis in Task 1.3 for review submission.
*   **Set up Kinesis Data Stream:** Create a Kinesis Data Stream with an initial shard count suitable for expected throughput. For development, a small number of shards is sufficient, scalable later.
*   **Configure IAM Roles/Permissions:** Ensure that the AWS Lambda function (developed in Task 1.3) has the necessary `kinesis:PutRecord` permissions for the created Kinesis stream.
*   **Define Retention Period:** Set the data retention period for the Kinesis stream. The default 24 hours is suitable for real-time processing, but it can be extended up to 7 days if needed for reprocessing or debugging.
*   **Monitoring:** While basic monitoring setup is Task 1.4, ensure CloudWatch metrics for Kinesis are enabled by default for stream health.

**Data Models and Architecture for Task 1.1**

*   **Architecture Diagram:**

    ```
    +-----------------+        +---------------------+        +---------------------+        +-------------------------+
    | Client (Amazon) | ---->  | API Gateway (HTTPS) | ---->  | AWS Lambda (Review  | ---->  | Kinesis Data Stream     |
    | (New Review)    |        |                     |        | Submission API)     |        | (real-time-review-stream)|
    +-----------------+        +---------------------+        +---------------------+        +-------------------------+
                                                                                                        |
                                                                                                        V
                                                                                            +-------------------------+
                                                                                            | Kinesis Consumers       |
                                                                                            | (e.g., Rule Engine Lambda)|
                                                                                            +-------------------------+
    ```

*   **Data Model (within Kinesis record):** The data format for each review record flowing through Kinesis will be JSON, as defined by the `ReviewInput` Pydantic model from Task 1.3, augmented with `reviewId` and `reviewDate`.

    ```json
    {
        "productId": "string",         // e.g., "B08B3QG5F2"
        "userId": "string",            // e.g., "USER12345"
        "rating": "integer (1-5)",     // e.g., 5
        "title": "string",             // e.g., "Great product!"
        "comment": "string",           // e.g., "I really enjoyed using this item, highly recommend it."
        "marketplace": "string",       // e.g., "US"
        "reviewId": "UUID string",     // e.g., "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        "reviewDate": "ISO 8601 datetime string" // e.g., "2023-10-27T10:30:00.123Z"
    }
    ```

**Assumptions and Technical Decisions for Task 1.1**

*   **Technology Choice:** AWS Kinesis Data Streams is selected for its real-time processing capabilities, scalability, durability, and native integration with other AWS services which will simplify the overall architecture.
*   **Partition Key Strategy:** The `userId` will be used as the Kinesis Partition Key. This ensures that all reviews from a specific user are routed to the same shard and processed in order, which is crucial for heuristics like "repetitive posting from a single account."
*   **Shard Count:** An initial `ShardCount` of 2 (or a similar low number) will be configured for the Kinesis stream in a development environment. This can be easily scaled up based on throughput requirements in production.
*   **Stream Mode:** `ON_DEMAND` mode will be preferred for its automatic scaling and simplified capacity management, eliminating the need to provision and manage shards manually. If `PROVISIONED` mode is chosen for cost optimization at scale, auto-scaling policies would be implemented.
*   **AWS Region:** All AWS resources for this project will be deployed in `us-east-1` (N. Virginia) by default, though this can be made configurable via environment variables.
*   **Error Handling:** Kinesis automatically retries failed `PutRecord` calls. For the Lambda producer, a dead-letter queue (DLQ) could be configured for unrecoverable errors.

**Code Snippets/Pseudocode for Key Components (Task 1.1)**

**CloudFormation Template (or equivalent Terraform/CDK) for Kinesis Data Stream:**

```yaml
# IngestionPipeline.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Kinesis Data Stream for Real-time Review Ingestion and related IAM roles

Resources:
  # Kinesis Data Stream
  RealTimeReviewStream:
    Type: AWS::Kinesis::Stream
    Properties:
      Name: real-time-review-stream
      ShardCount: 2 # Initial shard count, can be adjusted based on load. Consider ON_DEMAND mode for auto-scaling.
      Tags:
        - Key: Project
          Value: AmazonReviewAbuseDetection
        - Key: Environment
          Value: Development
      StreamModeDetails:
        StreamMode: ON_DEMAND # Recommended for automatic scaling and simplified management

  # IAM Policy for Lambda to put records into Kinesis
  KinesisPutRecordPolicy:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      Description: Policy allowing Lambda to put records into the Kinesis review stream
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - kinesis:PutRecord
              - kinesis:PutRecords
            Resource: !GetAtt RealTimeReviewStream.Arn

Outputs:
  RealTimeReviewStreamName:
    Description: Name of the Kinesis Data Stream
    Value: !Ref RealTimeReviewStream
  RealTimeReviewStreamArn:
    Description: ARN of the Kinesis Data Stream
    Value: !GetAtt RealTimeReviewStream.Arn
  KinesisPutRecordPolicyArn:
    Description: ARN of the IAM Managed Policy for Kinesis PutRecord
    Value: !Ref KinesisPutRecordPolicy
