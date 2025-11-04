# Real-time Data Ingestion Pipeline Design

**Sprint Task:** Design & Set up Real-time Data Ingestion Pipeline

**1. Implementation Plan:**

*   **Leverage AWS Kinesis Data Streams:** This will be the backbone for real-time ingestion, providing a highly scalable and durable data stream.
*   **Kinesis Stream Configuration:** Set up a Kinesis Data Stream named `amazon-review-ingestion-stream`. The initial shard count will be set to `5`, but this is a configurable parameter that can be adjusted based on the anticipated volume of review data. We will consider `ON_DEMAND` mode for simplicity and auto-scaling, or `PROVISIONED` if specific throughput guarantees are required and well-understood.
*   **Consumer Design:** An AWS Lambda function will be configured as the consumer of the Kinesis stream. Lambda's event-driven model and automatic scaling are well-suited for processing real-time streaming data without managing servers.
*   **Input Mechanism:** The upstream "Amazon Review Event Stream" (as identified in the research task) will be configured to push review events directly to our `amazon-review-ingestion-stream` Kinesis Data Stream.
*   **Output Mechanism:** The Lambda consumer will parse the incoming review data and store it in a NoSQL database, which will be detailed in the "Implement Initial Parsing & Storage" task.

**2. Data Models and Architecture:**

*   **Architecture Diagram (Conceptual):**

    ```
    +--------------------------------+
    | Amazon Review Event Stream     |
    | (Internal Source - Kinesis/Kafka)|
    +--------------------------------+
                    |
                    V
    +--------------------------------+
    | AWS Kinesis Data Stream        |
    | (amazon-review-ingestion-stream)|
    +--------------------------------+
                    |
                    V
    +--------------------------------+
    | AWS Lambda Function            |
    | (review-ingestion-processor)   |
    +--------------------------------+
                    |
                    V
    +--------------------------------+
    | DynamoDB                       |
    | (amazon-reviews-raw)           |
    +--------------------------------+
    ```

*   **Data Model (for Kinesis Record and initial storage):**
    The structure of each review event flowing through Kinesis and into initial storage will be a JSON object, adhering to the following schema:

    ```json
    {
      "review_id": "string",          // Unique identifier for the review
      "reviewer_id": "string",        // Unique identifier for the reviewer
      "product_id": "string",         // Unique identifier for the reviewed product
      "marketplace_id": "string",     // E.g., 'ATVPDKIKX0DER' for Amazon.com
      "star_rating": "integer",       // Review rating (1-5)
      "review_title": "string",       // Title of the review
      "review_text": "string",        // Full content of the review
      "review_date": "ISO 8601 string",// Timestamp of review submission (e.g., "2023-10-27T10:00:00Z")
      "product_category": "string",   // Primary category of the product (e.g., 'Electronics', 'Books')
      "helpful_votes": "integer",     // Number of helpful votes
      "verified_purchase": "boolean", // Indicates if the purchase was verified
      "ingestion_timestamp": "ISO 8601 string" // Added by the ingestion pipeline upon receipt
    }
    ```
    *Note: `product_category` is assumed to be available from the source stream or derivable.*

**3. Assumptions and Technical Decisions:**

*   **Assumption 1:** The "Amazon Review Event Stream" (internal source) can be configured to push data directly into an AWS Kinesis Data Stream in our account, or we have appropriate permissions to consume from an existing internal Kinesis stream.
*   **Assumption 2:** The volume of reviews will initially require 5 shards, with potential for scaling up. We assume Kinesis' `ON_DEMAND` mode can handle burst traffic effectively, otherwise `PROVISIONED` will be used with specific throughput planning.
*   **Technical Decision 1 (Ingestion Technology):** AWS Kinesis Data Streams is chosen for its fully managed, high-throughput, and low-latency capabilities, making it ideal for real-time data ingestion. Its native integration with AWS Lambda simplifies consumer setup.
*   **Technical Decision 2 (Consumer Technology):** AWS Lambda is selected as the Kinesis stream consumer. This provides a serverless, event-driven, and automatically scaling solution, minimizing operational overhead.
*   **Technical Decision 3 (Stream Mode):** We will start with `ON_DEMAND` stream mode for Kinesis for its flexibility and automatic scaling. If cost optimization or very predictable high throughput requirements emerge, we may switch to `PROVISIONED` mode.
*   **Technical Decision 4 (Region):** The ingestion pipeline will be deployed in a specific AWS region (e.g., `us-east-1`) to minimize latency and ensure data residency, aligning with Amazon's internal infrastructure.

**4. Code Snippets/Pseudocode for Key Components:**

*   **CloudFormation Template for Kinesis Stream (`infrastructure/kinesis_stream.yaml`):**

    ```yaml
    AWSTemplateFormatVersion: '2010-09-09'
    Description: AWS CloudFormation template for the Amazon Review Ingestion Kinesis Stream.

    Resources:
      ReviewIngestionStream:
        Type: AWS::Kinesis::Stream
        Properties:
          Name: amazon-review-ingestion-stream
          ShardCount: 5 # Initial shard count, adjust based on expected throughput.
          StreamModeDetails:
            StreamMode: ON_DEMAND # Use ON_DEMAND for automatic capacity scaling.

    Outputs:
      KinesisStreamName:
        Description: The name of the Kinesis Data Stream.
        Value: !GetAtt ReviewIngestionStream.Name
      KinesisStreamARN:
        Description: The ARN of the Kinesis Data Stream.
        Value: !GetAtt ReviewIngestionStream.Arn
    ```

*   **Pseudocode for Lambda Function (Consumer - detailed in next task, but included for context):**
    This pseudocode outlines how the Lambda function will read from Kinesis, parse the data, and prepare it for storage.

    ```python
    import json
    import base64
    from datetime import datetime

    # Assume boto3 and DynamoDB table client are initialized elsewhere (e.g., global scope or in a separate module)
    # import boto3
    # dynamodb_table = boto3.resource('dynamodb').Table('amazon-reviews-raw')

    def lambda_handler(event, context):
        for record in event['Records']:
            # Kinesis data is base64 encoded and then UTF-8 decoded
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            review_data = json.loads(payload)

            # Add ingestion timestamp
            review_data['ingestion_timestamp'] = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

            # --- Placeholder for actual storage logic (will be implemented in a later task) ---
            print(f"Received and parsed review: {review_data.get('review_id')} at {review_data['ingestion_timestamp']}")
            # Example: Store review_data in DynamoDB
            # try:
            #     dynamodb_table.put_item(Item=review_data)
            #     print(f"Successfully stored review: {review_data.get('review_id')}")
            # except Exception as e:
            #     print(f"Error storing review {review_data.get('review_id')}: {e}")
            #     # Implement Dead Letter Queue (DLQ) or retry mechanism here
            # ---------------------------------------------------------------------------------
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed Kinesis records.')
        }

    ```