### Task 1.3: Set up a secure data lake/database for storing raw review data.

*   **Implementation Plan:** Leverage AWS S3 for a secure and scalable data lake. This involves creating an S3 bucket, configuring appropriate bucket policies for access control, enabling encryption at rest, and setting up versioning for data durability.
*   **Data Models and Architecture:**
    *   **Storage:** AWS S3 (`amazon-raw-review-data-lake-prod`)
    *   **Data Format:** Raw JSON files, as received from the Kinesis stream.
    *   **Access Control:** IAM Roles and Policies for fine-grained access.
    *   **Encryption:** Server-Side Encryption with S3-managed keys (SSE-S3) or KMS-managed keys (SSE-KMS).
*   **Assumptions and Technical Decisions:**
    *   **Assumption:** AWS S3 is chosen for its scalability, durability, and cost-effectiveness for raw data storage.
    *   **Decision:** Data will be stored in its raw JSON format to maintain fidelity and allow for schema evolution.
    *   **Decision:** Server-Side Encryption (SSE-S3) will be enabled by default for all objects in the bucket to ensure data security at rest.
    *   **Decision:** Bucket policies and IAM roles will be used to control access, restricting write access to the ingestion pipeline and read access to authorized processing services.
    *   **Decision:** Versioning will be enabled to protect against accidental deletions and enable data recovery.
*   **Code Snippets/Pseudocode (Infrastructure as Code - Terraform/CloudFormation style):**
    ```
    # AWS CloudFormation/Terraform pseudo-code for S3 setup (revisiting and detailing from 1.1)

    resource "aws_s3_bucket" "raw_review_data_lake" {
      bucket = "amazon-raw-review-data-lake-prod"
      acl    = "private" # Restrict public access

      versioning {
        enabled = true # Enable versioning for data durability
      }

      server_side_encryption_configuration {
        rule {
          apply_server_side_encryption_by_default {
            sse_algorithm = "AES256" # SSE-S3 encryption
          }
        }
      }

      # Optional: Add bucket policy for access control (example for a Lambda writer)
      # resource "aws_s3_bucket_policy" "raw_review_data_lake_policy" {
      #   bucket = aws_s3_bucket.raw_review_data_lake.id
      #   policy = jsonencode({
      #     Version = "2012-10-17",
      #     Statement = [
      #       {
      #         Effect = "Allow",
      #         Principal = {
      #           AWS = "arn:aws:iam::<ACCOUNT_ID>:role/lambda_kinesis_processor_role" # Replace with actual Lambda role ARN
      #         },
      #         Action = [
      #           "s3:PutObject",
      #           "s3:GetObject"
      #         ],
      #         Resource = [
      #           "${aws_s3_bucket.raw_review_data_lake.arn}/*"
      #         ]
      #       }
      #     ]
      #   })
      # }
    }

    # IAM Role for Kinesis Consumer / S3 Writer (Conceptual for a Lambda processing Kinesis)
    resource "aws_iam_role" "kinesis_processor_s3_writer_role" {
      name = "kinesis-processor-s3-writer-role"
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

    resource "aws_iam_role_policy_attachment" "s3_put_object_policy" {
      role       = aws_iam_role.kinesis_processor_s3_writer_role.name
      policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess" # For simplicity, narrow down in production
    }

    resource "aws_iam_role_policy_attachment" "kinesis_read_only_policy" {
      role       = aws_iam_role.kinesis_processor_s3_writer_role.name
      policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisReadOnlyAccess" # For simplicity, narrow down in production
    }
    ```