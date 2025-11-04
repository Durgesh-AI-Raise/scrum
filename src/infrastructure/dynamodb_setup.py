import boto3
import os

def create_reviews_table(dynamodb_client, table_name: str):
    try:
        table = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'reviewId', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'reviewId', 'AttributeType': 'S'},
                {'AttributeName': 'reviewerId', 'AttributeType': 'S'}, # For GSI
                {'AttributeName': 'flaggedStatus', 'AttributeType': 'S'} # For GSI
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ReviewerIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'reviewerId', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'FlaggedStatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'flaggedStatus', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED' # Using provisioned for predictable costs in this example
            # ProvisionedThroughput={
            #     'ReadCapacityUnits': 5,
            #     'WriteCapacityUnits': 5
            # }
        )
        print(f"Creating table '{table_name}'...")
        table.wait_until_exists()
        print(f"Table '{table_name}' created successfully.")
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"Table '{table_name}' already exists.")
    except Exception as e:
        print(f"Error creating table '{table_name}': {e}")

if __name__ == "__main__":
    DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE_NAME', 'AmazonReviews')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)
    create_reviews_table(dynamodb_client, DYNAMODB_TABLE)
