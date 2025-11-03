### Task 1.1: Design data ingestion architecture.

*   **Implementation Plan:** Design a scalable and fault-tolerant architecture for ingesting Amazon product reviews using AWS services.
*   **Data Models and Architecture:**
    *   **Source:** Amazon Product Reviews (hypothetical API/stream)
    *   **Streaming Layer:** AWS Kinesis Data Streams (`amazon-review-data-stream`) for real-time ingestion.
    *   **Storage Layer (Raw Data Lake):** AWS S3 (`amazon-raw-review-data-lake-prod`) for cost-effective, durable storage of raw data.
    *   **Processing Layer:** AWS Lambda (triggered by Kinesis) for initial parsing.
    *   **Monitoring & Logging:** AWS CloudWatch.
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** An Amazon API or data feed for new product reviews exists and can be integrated.
    *   **Decision:** AWS ecosystem is chosen for its robust managed services.
    *   **Decision:** Kinesis Data Streams for real-time, ordered, and durable streaming.
    *   **Decision:** S3 for raw data lake due to scalability and cost-effectiveness.
*   **Code Snippets/Pseudocode (Infrastructure as Code - Terraform/CloudFormation style):**
    ```
    # AWS CloudFormation/Terraform pseudo-code for architecture setup:

    # Kinesis Data Stream
    resource "aws_kinesis_stream" "review_stream" {
      name        = "amazon-review-data-stream"
      shard_count = 5 # Example shard count, can be scaled
      retention_period = 24 # hours
    }

    # S3 Bucket for Raw Data Lake
    resource "aws_s3_bucket" "raw_review_data_lake" {
      bucket = "amazon-raw-review-data-lake-prod"
      acl    = "private"
      versioning {
        enabled = true
      }
      server_side_encryption_configuration {
        rule {
          apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
          }
        }
      }
    }

    # IAM Role for Lambda/Kinesis Producer (Conceptual)
    resource "aws_iam_role" "review_data_producer_role" {
      name = "amazon-review-data-producer-role"
      assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
              Service = "lambda.amazonaws.com"
            }
          },
        ]
      })
    }

    resource "aws_iam_role_policy_attachment" "kinesis_put_records" {
      role       = aws_iam_role.review_data_producer_role.name
      policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisPutRecord"
    }
    ```