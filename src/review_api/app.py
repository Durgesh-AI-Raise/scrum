from flask import Flask, request, jsonify
import boto3
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'reviews')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

@app.route('/reviews/<string:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    try:
        response = table.get_item(Key={'review_id': review_id})
        item = response.get('Item')
        if not item:
            return jsonify({'message': 'Review not found'}), 404
        return jsonify(item), 200
    except Exception as e:
        logging.error(f"Error getting review by ID {review_id}: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/products/<string:product_id>/reviews', methods=['GET'])
def get_reviews_by_product_id(product_id):
    try:
        # Pagination parameters
        last_evaluated_key = request.args.get('last_evaluated_key')
        limit = int(request.args.get('limit', 20)) # Default limit 20

        query_kwargs = {
            'IndexName': 'product_id-index',
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('product_id').eq(product_id),
            'Limit': limit
        }
        if last_evaluated_key:
            query_kwargs['ExclusiveStartKey'] = {'review_id': last_evaluated_key, 'product_id': product_id} # Need both for GSI

        response = table.query(**query_kwargs)
        reviews = response.get('Items', [])
        
        result = {
            'reviews': reviews
        }
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = response['LastEvaluatedKey']['review_id']

        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error getting reviews for product {product_id}: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/reviewers/<string:reviewer_id>/reviews', methods=['GET'])
def get_reviews_by_reviewer_id(reviewer_id):
    try:
        # Pagination parameters
        last_evaluated_key = request.args.get('last_evaluated_key')
        limit = int(request.args.get('limit', 20)) # Default limit 20

        query_kwargs = {
            'IndexName': 'reviewer_id-index',
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('reviewer_id').eq(reviewer_id),
            'Limit': limit
        }
        if last_evaluated_key:
            query_kwargs['ExclusiveStartKey'] = {'review_id': last_evaluated_key, 'reviewer_id': reviewer_id} # Need both for GSI

        response = table.query(**query_kwargs)
        reviews = response.get('Items', [])
        
        result = {
            'reviews': reviews
        }
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = response['LastEvaluatedKey']['review_id']

        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error getting reviews for reviewer {reviewer_id}: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
