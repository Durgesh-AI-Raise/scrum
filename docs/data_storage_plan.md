# Initial Data Storage Setup - S3 and Kinesis Firehose

## Implementation Plan:
*   Create a dedicated AWS S3 bucket to serve as the raw data landing zone for review data.
*   Configure an AWS Kinesis Firehose delivery stream to consume data from the `ReviewDataStream` (Kinesis Data Stream).
*   The Firehose will deliver the data to the S3 bucket.
*   Implement an S3 prefix structure for partitioning data by ingestion timestamp (year/month/day/hour).

## Data Models and Architecture:
*   **Architecture:** `Review Data Source -> Kinesis Data Stream (ReviewDataStream) -> Kinesis Firehose -> S3 Bucket (Raw Data Lake)`
*   **Data Model:** Data in S3 will be individual JSON objects, conforming to `review_data_schema.json`.

## Assumptions and Technical Decisions:
*   **Assumption:** AWS S3 provides sufficient scalability, durability, and cost-effectiveness for raw review data storage.
*   **Decision:** Use AWS Kinesis Firehose for streamlined integration with Kinesis Data Streams and automated delivery to S3.
*   **Decision:** Data will be stored in JSON format for flexibility and compatibility with data lake query services.
*   **Decision:** Implement time-based partitioning (`raw/reviews/year=/month=/day=/hour=/`) in S3 for optimized querying.

## Conceptual Terraform for AWS Resources:

```terraform
# --- S3 Bucket for Raw Review Data ---
resource "aws_s3_bucket" "raw_review_data_bucket" {
  bucket = "your-company-review-data-raw-bucket-unique-name" # Replace with a globally unique bucket name
  acl    = "private"

  versioning {
    enabled = true # Enable versioning for data recovery
  }

  tags = {
    Name        = "Raw Review Data Storage"
    Environment = "Dev"
  }
}

# --- IAM Role for Kinesis Firehose to write to S3 ---
resource "aws_iam_role" "firehose_s3_delivery_role" {
  name = "firehose_s3_delivery_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "firehose_s3_delivery_policy" {
  name = "firehose_s3_delivery_policy"
  role = aws_iam_role.firehose_s3_delivery_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ],
        Effect   = "Allow",
        Resource = [
          aws_s3_bucket.raw_review_data_bucket.arn,
          "${aws_s3_bucket.raw_review_data_bucket.arn}/*"
        ]
      },
      {
        Action   = ["kinesis:DescribeStream", "kinesis:GetShardIterator", "kinesis:GetRecords"],
        Effect   = "Allow",
        Resource = "arn:aws:kinesis:us-east-1:123456789012:stream/ReviewDataStream" # Replace with your account ID
      },
      {
         Action = ["kms:Decrypt"],
         Effect = "Allow",
         Resource = "arn:aws:kms:us-east-1:123456789012:key/your-kms-key-id" # If Kinesis Stream is encrypted
      }
    ]
  })
}

# --- Kinesis Firehose Delivery Stream for S3 ---
resource "aws_kinesis_firehose_delivery_stream" "review_data_to_s3_firehose" {
  name        = "review-data-to-s3-firehose"
  destination = "s3"

  s3_configuration {
    role_arn          = aws_iam_role.firehose_s3_delivery_role.arn
    bucket_arn        = aws_s3_bucket.raw_review_data_bucket.arn
    prefix            = "raw/reviews/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "error/reviews/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}/"

    buffering_hints {
      interval_in_seconds = 60 # Buffer for 60 seconds
      size_in_mbs         = 5  # Buffer up to 5 MB
    }

    # Optional: You can enable compression or encryption here
    compression_format  = "UNCOMPRESSED"
    # encryption_configuration {
    #   kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/your-kms-key-id"
    # }
  }

  # Source configuration for Kinesis Data Stream
  kinesis_stream_source_configuration {
    kinesis_stream_arn = "arn:aws:kinesis:us-east-1:123456789012:stream/ReviewDataStream" # Replace with your account ID
    role_arn           = aws_iam_role.firehose_s3_delivery_role.arn # Firehose needs permission to read from Kinesis
  }

  tags = {
    Name        = "Review Data Firehose"
    Environment = "Dev"
  }
}
```
