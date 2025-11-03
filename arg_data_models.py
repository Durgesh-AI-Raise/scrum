from datetime import datetime

# --- Mock Database and Session for demonstration purposes ---
# In a real application, this would be an ORM like SQLAlchemy connected to a PostgreSQL/MySQL database.
class MockDBSession:
    def __init__(self):
        self.reviews = []
        self.reviewers = []

    def add(self, obj):
        if isinstance(obj, Review):
            self.reviews.append(obj)
        elif isinstance(obj, Reviewer):
            self.reviewers.append(obj)

    def commit(self):
        # In a real DB, this would persist changes. Here, objects are already in lists.
        pass

    def query(self, model):
        if model == Review:
            return MockQuery(self.reviews)
        elif model == Reviewer:
            return MockQuery(self.reviewers)
        return MockQuery([])

class MockQuery:
    def __init__(self, data):
        self._data = data
        self._filters = []
        self._single_result = False

    def filter_by(self, **kwargs):
        self._filters.append(lambda item: all(getattr(item, k) == v for k, v in kwargs.items()))
        return self

    def filter(self, *args):
        # For simplicity, assuming filter args are direct boolean expressions for now
        # In SQLAlchemy, these would be ColumnElement objects.
        self._filters.extend(args)
        return self

    def all(self):
        filtered_data = self._data
        for f in self._filters:
            if callable(f):
                filtered_data = [item for item in filtered_data if f(item)]
            else: # Assuming f is a simple boolean condition
                filtered_data = [item for item in filtered_data if f] # This part needs careful handling for actual expressions
        return filtered_data

    def first(self):
        self._single_result = True
        result = self.all()
        return result[0] if result else None

    def count(self):
        return len(self.all())

# Instantiate a global mock database session
db_session = MockDBSession()

# --- Data Models ---
class Review:
    def __init__(self, review_id: str, reviewer_id: str, product_id: str, review_text: str, review_date: datetime, rating: int):
        self.review_id = review_id
        self.reviewer_id = reviewer_id
        self.product_id = product_id
        self.review_text = review_text
        self.review_date = review_date
        self.rating = rating
        self.spam_flag = False
        self.fabricated_flag = False
        self.suspicious_account_flag = False
        self.status = 'pending' # 'pending', 'approved', 'rejected', 'quarantined'
        self.detection_reason = ''

class Reviewer:
    def __init__(self, reviewer_id: str, username: str = None, email: str = None):
        self.reviewer_id = reviewer_id
        self.username = username
        self.email = email
        self.total_reviews = 0
        self.reviews_last_24h = 0
        self.suspicious_flag = False
        self.detection_reason = ''
