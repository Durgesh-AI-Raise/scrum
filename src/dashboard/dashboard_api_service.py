import json
import os
import boto3
import base64
from decimal import Decimal
from botocore.exceptions import ClientError

dynamodb_client = boto3.client('dynamodb')

# Environment variables (to be set in Lambda configuration)
REVIEWS_TABLE_NAME = os.environ.get('REVIEWS_TABLE_NAME', 'aris-all-reviews')
GSI_NAME = os.environ.get('GSI_NAME', 'FlaggedReviewsByScoreIndex')

class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder that converts Decimal objects to floats.
    Necessary for DynamoDB numbers.
    """
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def convert_dynamodb_item_to_json(item):
    """
    Recursively converts a DynamoDB item (with type wrappers) to a plain Python dict,
    handling nested lists and maps, and converting Decimals.
    """
    if not isinstance(item, dict):
        return item # Base case for simple types

    converted_item = {}
    for k, v in item.items():
        if isinstance(v, dict) and len(v) == 1:
            if 'S' in v:
                converted_item[k] = v['S']
            elif 'N' in v:
                converted_item[k] = Decimal(v['N'])
            elif 'BOOL' in v:
                converted_item[k] = v['BOOL']
            elif 'L' in v:
                converted_item[k] = [convert_dynamodb_item_to_json(elem) for elem in v['L']]
            elif 'M' in v:
                converted_item[k] = convert_dynamodb_item_to_json(v['M'])
            else:
                converted_item[k] = v # Fallback for unknown types
        else: # Handle already converted or complex structures
            converted_item[k] = v
    return converted_item

def lambda_handler(event, context):
    query_params = event.get('queryStringParameters', {})
    min_abuse_score = float(query_params.get('minAbuseScore', 0.0))
    sort_by = query_params.get('sortBy', 'abuseScore') # 'abuseScore' or 'reviewDate'
    sort_order = query_params.get('sortOrder', 'desc') # 'asc' or 'desc'
    limit = int(query_params.get('limit', 20))
    last_key_encoded = query_params.get('lastKey')

    scan_index_forward = (sort_order == 'asc')

    query_kwargs = {
        'TableName': REVIEWS_TABLE_NAME,
        'IndexName': GSI_NAME,
        'KeyConditionExpression': 'isFlagged = :flagged_status AND abuseScore >= :min_score',
        'ExpressionAttributeValues': {
            ':flagged_status': {'BOOL': True},
            ':min_score': {'N': str(Decimal(str(min_abuse_score)))} # Ensure Decimal for comparison
        },
        'ScanIndexForward': scan_index_forward,
        'Limit': limit
    }

    if last_key_encoded:
        try:
            # Decode and load LastEvaluatedKey
            decoded_key_str = base64.b64decode(last_key_encoded).decode('utf-8')
            query_kwargs['ExclusiveStartKey'] = json.loads(decoded_key_str, parse_float=Decimal)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error decoding lastKey: {e}. Ignoring lastKey.")

    try:
        response = dynamodb_client.query(**query_kwargs)
        items = []
        for item in response.get('Items', []):
            converted_item = convert_dynamodb_item_to_json(item)
            items.append(converted_item)

        next_token = None
        if 'LastEvaluatedKey' in response:
            # Encode LastEvaluatedKey for pagination. Use DecimalEncoder.
            next_token = base64.b64encode(json.dumps(response['LastEvaluatedKey'], cls=DecimalEncoder).encode('utf-8')).decode('utf-8')

        # Additional sorting for reviewDate if not primarily sorted by GSI
        if sort_by == 'reviewDate':
            items.sort(key=lambda x: x.get('reviewDate', ''), reverse=(sort_order == 'desc'))


        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*', # Enable CORS for front-end
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'reviews': items,
                'nextToken': next_token
            }, cls=DecimalEncoder)
        }
    except ClientError as e:
        print(f"Error fetching flagged reviews from DynamoDB: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': "An internal server error occurred."})
        }