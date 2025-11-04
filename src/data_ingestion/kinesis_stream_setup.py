import boto3
import json

def setup_kinesis_streams(region='us-east-1', raw_stream_name='aris-raw-reviews', processed_stream_name='aris-processed-reviews', shard_count=5):
    """
    Sets up the necessary Kinesis Data Streams for ARIS.
    This script is illustrative and would typically be part of an IaC solution (e.g., CloudFormation, Terraform).
    """
    kinesis_client = boto3.client('kinesis', region_name=region)

    streams_to_create = [raw_stream_name, processed_stream_name]

    for stream_name in streams_to_create:
        try:
            print(f"Attempting to create Kinesis Stream: {stream_name}")
            response = kinesis_client.create_stream(
                StreamName=stream_name,
                ShardCount=shard_count
            )
            print(f"Kinesis Stream '{stream_name}' created successfully: {response}")
        except kinesis_client.exceptions.ResourceInUseException:
            print(f"Kinesis Stream '{stream_name}' already exists.")
        except Exception as e:
            print(f"Error creating Kinesis Stream '{stream_name}': {e}")

    print("\nKinesis Stream Setup Complete.")

if __name__ == "__main__":
    # In a real environment, you'd configure region, stream names, and shard count
    # via environment variables or a configuration file.
    setup_kinesis_streams()

    # --- Illustrative DynamoDB Table Setup for aris-all-reviews and GSI ---
    # This part would also typically be in IaC, but shown here for completeness
    print("\n--- Illustrative DynamoDB Table Setup ---")
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    table_name = 'aris-all-reviews'
    gsi_name = 'FlaggedReviewsByScoreIndex'

    try:
        print(f"Attempting to create DynamoDB table: {table_name}")
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'reviewId', 'KeyType': 'HASH'} # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'reviewId', 'AttributeType': 'S'},
                {'AttributeName': 'isFlagged', 'AttributeType': 'BOOL'},
                {'AttributeName': 'abuseScore', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            GlobalSecondaryIndexes=[
                {
                    'IndexName': gsi_name,
                    'KeySchema': [
                        {'AttributeName': 'isFlagged', 'KeyType': 'HASH'},
                        {'AttributeName': 'abuseScore', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL' # Project all attributes for dashboard queries
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ]
        )
        print(f"DynamoDB table '{table_name}' and GSI '{gsi_name}' creation initiated. Please wait for active status.")
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"DynamoDB table '{table_name}' already exists.")
    except Exception as e:
        print(f"Error creating DynamoDB table '{table_name}': {e}")

    # --- Illustrative DynamoDB Table Setup for aris-reviewer-activity ---
    table_name_activity = 'aris-reviewer-activity'
    try:
        print(f"\nAttempting to create DynamoDB table: {table_name_activity}")
        dynamodb_client.create_table(
            TableName=table_name_activity,
            KeySchema=[
                {'AttributeName': 'reviewerId', 'KeyType': 'HASH'} # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'reviewerId', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"DynamoDB table '{table_name_activity}' creation initiated. Please wait for active status.")
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"DynamoDB table '{table_name_activity}' already exists.")
    except Exception as e:
        print(f"Error creating DynamoDB table '{table_name_activity}': {e}")