from kafka import KafkaConsumer
import json
from datetime import datetime
# Assuming a database connector is available, e.g., psycopg2 for PostgreSQL

def process_review_message(message_value):
    data = json.loads(message_value)

    # Extract product, reviewer, order, and review data
    product_data = data.get('product', {})
    reviewer_data = data.get('reviewer', {})
    order_data = data.get('order', {})
    review_data = data.get('review', {})

    # Validate essential fields
    if not all([review_data.get('review_id'), product_data.get('product_id'), reviewer_data.get('reviewer_id'), review_data.get('content')]):
        print(f"Skipping invalid review data: {message_value}")
        return

    # Insert/Update Product (upsert logic)
    # Check if product exists, if not, insert
    # db_connector.execute("INSERT INTO Products ... ON CONFLICT (product_id) DO UPDATE SET ...", product_data)

    # Insert/Update Reviewer (upsert logic)
    # db_connector.execute("INSERT INTO Reviewers ... ON CONFLICT (reviewer_id) DO UPDATE SET ...", reviewer_data)

    # Insert/Update Order (upsert logic, if order_id exists)
    # if order_data.get('order_id'):
    #    db_connector.execute("INSERT INTO Orders ... ON CONFLICT (order_id) DO UPDATE SET ...", order_data)

    # Insert Review
    review_id = review_data['review_id']
    product_id = product_data['product_id']
    reviewer_id = reviewer_data['reviewer_id']
    order_id = order_data.get('order_id')
    rating = review_data.get('rating')
    title = review_data.get('title')
    content = review_data['content']
    review_date = datetime.fromisoformat(review_data['review_date'].replace('Z', '+00:00')) if 'review_date' in review_data else datetime.utcnow()

    # db_connector.execute(
    #    "INSERT INTO Reviews (review_id, product_id, reviewer_id, order_id, rating, title, content, review_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
    #    (review_id, product_id, reviewer_id, order_id, rating, title, content, review_date)
    # )
    print(f"Successfully processed review: {review_id}")


# Kafka Consumer setup
# consumer = KafkaConsumer(
#    'amazon_reviews_topic',
#    bootstrap_servers=['kafka_broker_1:9092'],
#    auto_offset_reset='earliest',
#    enable_auto_commit=True,
#    group_id='aris-ingestion-group',
#    value_deserializer=lambda x: x.decode('utf-8')
# )

# for message in consumer:
#    process_review_message(message.value)
