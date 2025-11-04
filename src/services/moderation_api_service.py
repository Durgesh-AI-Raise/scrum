import json
import boto3
import os
from typing import List, Dict, Optional
from datetime import datetime

class ModerationAPI:
    def __init__(self, dynamodb_table_name: str, aws_region: str = 'us-east-1'):
        self.dynamodb_resource = boto3.resource('dynamodb', region_name=aws_region)
        self.reviews_table = self.dynamodb_resource.Table(dynamodb_table_name)
        print(f"Initialized Moderation API for DynamoDB Table: {dynamodb_table_name}")

    def get_flagged_reviews(
        self, 
        status: str = 'FLAGGED', 
        min_confidence: float = 0.0, 
        max_confidence: float = 1.0, 
        limit: int = 20, 
        sort_by: str = 'lastFlaggedAt', # default sort
        sort_order: str = 'DESC', # default order
        last_evaluated_key: Optional[dict] = None
    ) -> (List[Dict], Optional[Dict], int):
        """
        Retrieves flagged reviews from DynamoDB, with filtering, sorting, and pagination.
        Assumes 'FlaggedStatusIndex' GSI exists for efficient querying by status.
        """
        try:
            query_kwargs = {
                'IndexName': 'FlaggedStatusIndex',
                'KeyConditionExpression': boto3.dynamodb.conditions.Key('flaggedStatus').eq(status),
                'FilterExpression': boto3.dynamodb.conditions.Attr('confidenceScore').between(min_confidence, max_confidence),
                'Limit': limit,
                'ScanIndexForward': (sort_order == 'ASC') # True for ASC, False for DESC
            }
            if last_evaluated_key:
                query_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.reviews_table.query(**query_kwargs)
            items = response.get('Items', [])
            last_key = response.get('LastEvaluatedKey')
            
            # If sorting by an attribute not in the GSI's key schema, sort client-side
            if sort_by not in ['flaggedStatus'] and items: # flaggedStatus is the GSI HASH key
                 items.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == 'DESC'))

            return items, last_key, 200

        except self.reviews_table.meta.client.exceptions.ResourceNotFoundException:
            print(f"Error: GSI 'FlaggedStatusIndex' not found. Please ensure it is created for efficient querying.")
            # Fallback to scan if GSI is not found (less efficient)
            scan_kwargs = {
                'FilterExpression': boto3.dynamodb.conditions.Attr('flaggedStatus').eq(status) & \
                                    boto3.dynamodb.conditions.Attr('confidenceScore').between(min_confidence, max_confidence),
                'Limit': limit
            }
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
            
            response = self.reviews_table.scan(**scan_kwargs)
            items = response.get('Items', [])
            last_key = response.get('LastEvaluatedKey')
            if items: # Client-side sort if using scan
                items.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == 'DESC'))
            return items, last_key, 200

        except Exception as e:
            print(f"Error retrieving flagged reviews: {e}")
            return [], None, 500

    def get_review_details(self, review_id: str) -> (Dict, int):
        """Retrieves details for a specific review."""
        try:
            response = self.reviews_table.get_item(Key={'reviewId': review_id})
            item = response.get('Item')
            if item:
                return item, 200
            return {"message": "Review not found"}, 404
        except Exception as e:
            print(f"Error retrieving review details for {review_id}: {e}")
            return {"message": "Internal server error"}, 500

    def update_review_status(self, review_id: str, new_status: str, moderator_id: str) -> (Dict, int):
        """Updates the moderator status of a review."""
        if new_status not in ["ABUSE_CONFIRMED", "FALSE_POSITIVE", "UNDER_INVESTIGATION", "PENDING_REVIEW"]:
            return {"message": "Invalid status provided"}, 400

        try:
            response = self.reviews_table.update_item(
                Key={'reviewId': review_id},
                UpdateExpression="SET moderatorStatus = :ms, lastModeratedAt = :lmat",
                ExpressionAttributeValues={
                    ':ms': new_status,
                    ':lmat': datetime.utcnow().isoformat()
                },
                ReturnValues="UPDATED_NEW"
            )
            return response.get('Attributes'), 200
        except Exception as e:
            print(f"Error updating status for review {review_id}: {e}")
            return {"message": "Internal server error"}, 500

    def trigger_review_action(self, review_id: str, action_type: str, action_details: str, moderator_id: str) -> (Dict, int):
        """Triggers an action for a review and records it."""
        if action_type not in ["REMOVE_REVIEW", "BAN_REVIEWER", "NOTIFY_REVIEWER", "ESCALATE_TO_LEGAL"]:
            return {"message": "Invalid action type provided"}, 400

        action_record = {
            "actionType": action_type,
            "actionDetails": action_details,
            "actionTimestamp": datetime.utcnow().isoformat(),
            "moderatorId": moderator_id
        }

        try:
            response = self.reviews_table.update_item(
                Key={'reviewId': review_id},
                UpdateExpression="SET moderatorActions = list_append(if_not_exists(moderatorActions, :empty_list), :new_action), lastModeratedAt = :lmat",
                ExpressionAttributeValues={
                    ':empty_list': [],
                    ':new_action': [action_record],
                    ':lmat': datetime.utcnow().isoformat()
                },
                ReturnValues="UPDATED_NEW"
            )
            print(f"Recorded action '{action_type}' for review {review_id}.")
            
            # --- Trigger downstream systems (Pseudocode) ---
            # In a real system, this would involve sending messages to SQS/SNS
            # or calling other internal services. For this MVP, we just log.
            if action_type == "REMOVE_REVIEW":
                print(f"[DOWNSTREAM_ACTION] Request to remove review {review_id} from storefront.")
            elif action_type == "BAN_REVIEWER":
                # This would typically require fetching the reviewerId from the review first
                print(f"[DOWNSTREAM_ACTION] Request to ban reviewer associated with review {review_id}.")
            # --- End downstream triggers ---

            return response.get('Attributes'), 200
        except Exception as e:
            print(f"Error triggering action for review {review_id}: {e}")
            return {"message": "Internal server error"}, 500

# Example Usage (for testing the pseudocode classes)
if __name__ == "__main__":
    DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE_NAME', 'AmazonReviews')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    api = ModerationAPI(DYNAMODB_TABLE, AWS_REGION)
    
    # Manual GSI check/creation (should be handled by dynamodb_setup.py normally)
    dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)
    try:
        # Attempt to describe table to see if GSI exists
        table_description = dynamodb_client.describe_table(TableName=DYNAMODB_TABLE)
        gsi_exists = any(gsi['IndexName'] == 'FlaggedStatusIndex' for gsi in table_description.get('Table', {}).get('GlobalSecondaryIndexes', []))
        
        if not gsi_exists:
            print("FlaggedStatusIndex GSI not found. Attempting to create it...")
            dynamodb_client.update_table(
                TableName=DYNAMODB_TABLE,
                AttributeDefinitions=[
                    {'AttributeName': 'flaggedStatus', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexUpdates=[
                    {
                        'Create': {
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
                    }
                ]
            )
            print("Initiated GSI creation for FlaggedStatusIndex.")
            waiter = dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=DYNAMODB_TABLE, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
            print("FlaggedStatusIndex GSI is active.")
        else:
            print("FlaggedStatusIndex GSI already exists.")

    except dynamodb_client.exceptions.ResourceNotFoundException:
        print(f"Table '{DYNAMODB_TABLE}' not found. Please run dynamodb_setup.py first.")
        exit()
    except Exception as e:
        print(f"Error during GSI setup: {e}")

    # Get flagged reviews
    print("\n--- Getting Flagged Reviews ---")
    flagged_reviews, last_key, status = api.get_flagged_reviews(status='FLAGGED', limit=2, sort_by='confidenceScore', sort_order='DESC')
    print(f"Flagged Reviews (Status {status}): {json.dumps(flagged_reviews, indent=2)}")
    print(f"Last Evaluated Key: {last_key}")

    if last_key:
        print("\n--- Getting Next Page of Flagged Reviews ---")
        next_page_reviews, _, status = api.get_flagged_reviews(status='FLAGGED', limit=2, last_evaluated_key=last_key, sort_by='confidenceScore', sort_order='DESC')
        print(f"Next Page Flagged Reviews (Status {status}): {json.dumps(next_page_reviews, indent=2)}")

    # Test updating status and triggering actions if there are flagged reviews
    if flagged_reviews:
        review_id_to_act_on = flagged_reviews[0]['reviewId']
        print(f"\n--- Updating Status for Review ID: {review_id_to_act_on} ---")
        updated_attrs, status = api.update_review_status(review_id_to_act_on, "ABUSE_CONFIRMED", "mod-alice")
        print(f"Update Status Result (Status {status}): {json.dumps(updated_attrs, indent=2)}")

        print(f"\n--- Triggering Action 'REMOVE_REVIEW' for Review ID: {review_id_to_act_on} ---")
        action_attrs, status = api.trigger_review_action(
            review_id_to_act_on, "REMOVE_REVIEW", "Contains profanity as per policy", "mod-alice"
        )
        print(f"Trigger Action Result (Status {status}): {json.dumps(action_attrs, indent=2)}")

        print(f"\n--- Triggering Action 'BAN_REVIEWER' for Review ID: {review_id_to_act_on} ---")
        # Assuming reviewer ID can be derived or is directly available for BAN_REVIEWER
        action_attrs, status = api.trigger_review_action(
            review_id_to_act_on, "BAN_REVIEWER", "Repeated abuse detected", "mod-alice"
        )
        print(f"Trigger Action Result (Status {status}): {json.dumps(action_attrs, indent=2)}")

        # Fetch details again to verify
        print(f"\n--- Fetching Updated Review Details for {review_id_to_act_on} ---")
        final_details, status = api.get_review_details(review_id_to_act_on)
        print(f"Final Details (Status {status}): {json.dumps(final_details, indent=2)}")

