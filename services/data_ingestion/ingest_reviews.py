import csv
from datetime import datetime

# This is a placeholder for database interaction.
# In a real application, you would use an ORM like SQLAlchemy or a database client.
class MockDB:
    def __init__(self):
        self.reviews = []

    def add_review(self, review_data):
        self.reviews.append(review_data)
        print(f"MockDB: Added review {review_data['review_id']}")

mock_db = MockDB()

def ingest_review_data(filepath="data/sample_reviews.csv"):
    """
    Ingests review data from a CSV file into the system.
    For MVP, it uses a mock database.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                review_data = {
                    "review_id": row["review_id"],
                    "product_id": row["product_id"],
                    "reviewer_id": row["reviewer_id"],
                    "rating": int(row["rating"]),
                    "review_title": row["review_title"],
                    "review_content": row["review_content"],
                    "review_date": datetime.strptime(row["review_date"], "%Y-%m-%d %H:%M:%S"),
                    "source_url": row.get("source_url", "")
                }
                mock_db.add_review(review_data)
            except Exception as e:
                print(f"Error ingesting row {row.get('review_id', 'N/A')}: {e}")

if __name__ == "__main__":
    # Create a dummy CSV file for demonstration
    dummy_csv_content = """review_id,product_id,reviewer_id,rating,review_title,review_content,review_date,source_url
R1,P1,U1,5,Great product!,This is an amazing product, I love it.,2023-01-15 10:00:00,http://amazon.com/review/R1
R2,P2,U2,1,Horrible!,Terrible product, waste of money.,2023-01-16 11:00:00,http://amazon.com/review/R2
R3,P1,U3,5,Must buy!,Super good, highly recommend!,2023-01-17 12:00:00,http://amazon.com/review/R3
R4,P3,U4,5,Amazing!,Buy this now! discount code XY23,2023-01-18 13:00:00,http://amazon.com/review/R4
"""
    import os
    os.makedirs('data', exist_ok=True)
    with open('data/sample_reviews.csv', 'w') as f:
        f.write(dummy_csv_content)

    ingest_review_data()