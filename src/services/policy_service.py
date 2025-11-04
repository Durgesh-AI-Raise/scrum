import uuid
from datetime import datetime
import json

# Pseudocode for Policy Service data model and API endpoints
# In a real application, this would be a Flask/FastAPI application
# with a proper database client (e.g., boto3 for DynamoDB).

class AbuseCriteria:
    """
    Represents an abuse detection criterion.
    The 'criteria_details' field is flexible (JSON) to accommodate different rule types.
    """
    def __init__(self, name: str, type: str, criteria_details: dict, id: str = None, is_active: bool = True):
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.type = type
        self.criteria_details = criteria_details
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "criteria_details": self.criteria_details,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

# --- Pseudocode for Policy Service API ---
# This simulates a basic REST API for managing abuse criteria.
# In a production environment, this would be backed by a web framework
# (e.g., Flask, FastAPI) and a database (e.g., DynamoDB).

class PolicyServiceAPI:
    def __init__(self, db_client=None):
        self.criteria_store = {} # In-memory store for simulation; replace with actual DB client
        self.db_client = db_client # Example: boto3 DynamoDB client

    def _save_criteria(self, criteria: AbuseCriteria):
        # Simulate saving to DB
        self.criteria_store[criteria.id] = criteria.to_dict()
        print(f"Criteria saved: {criteria.id}")
        # Example for DynamoDB: self.db_client.put_item(Item=criteria.to_dict())

    def _get_criteria_by_id(self, criteria_id: str):
        # Simulate fetching from DB
        return self.criteria_store.get(criteria_id)
        # Example for DynamoDB: return self.db_client.get_item(Key={'id': criteria_id}).get('Item')

    def _get_all_criteria(self):
        # Simulate fetching all from DB
        return list(self.criteria_store.values())
        # Example for DynamoDB: return self.db_client.scan().get('Items', [])

    def create_criteria(self, data: dict) -> (dict, int):
        """API endpoint: POST /criteria"""
        # Basic validation
        if not all(k in data for k in ['name', 'type', 'criteria_details']):
            return {"message": "Missing required fields"}, 400

        try:
            new_criteria = AbuseCriteria(
                name=data['name'],
                type=data['type'],
                criteria_details=data['criteria_details'],
                is_active=data.get('is_active', True)
            )
            self._save_criteria(new_criteria)
            return new_criteria.to_dict(), 201
        except Exception as e:
            return {"message": f"Failed to create criteria: {e}"}, 500

    def get_criteria(self, criteria_id: str) -> (dict, int):
        """API endpoint: GET /criteria/<id>"""
        criteria = self._get_criteria_by_id(criteria_id)
        if criteria:
            return criteria, 200
        return {"message": "Criteria not found"}, 404

    def get_all_active_criteria(self) -> (list, int):
        """API endpoint: GET /criteria (for detection service)"""
        all_criteria = self._get_all_criteria()
        active_criteria = [c for c in all_criteria if c.get('is_active', False)]
        return active_criteria, 200

    def update_criteria(self, criteria_id: str, data: dict) -> (dict, int):
        """API endpoint: PUT /criteria/<id>"""
        criteria_dict = self._get_criteria_by_id(criteria_id)
        if not criteria_dict:
            return {"message": "Criteria not found"}, 404

        # Update fields
        for key, value in data.items():
            if key in ['name', 'type', 'criteria_details', 'is_active']:
                criteria_dict[key] = value
        criteria_dict['updated_at'] = datetime.utcnow().isoformat()
        
        # Simulate update in DB
        self.criteria_store[criteria_id] = criteria_dict

        return {"message": "Criteria updated", "criteria": criteria_dict}, 200

    def delete_criteria(self, criteria_id: str) -> (dict, int):
        """API endpoint: DELETE /criteria/<id>"""
        if criteria_id in self.criteria_store:
            del self.criteria_store[criteria_id]
            print(f"Criteria deleted: {criteria_id}")
            return {"message": "Criteria deleted"}, 204
        return {"message": "Criteria not found"}, 404

# Example Usage (for testing the pseudocode classes)
if __name__ == "__main__":
    api = PolicyServiceAPI()

    # Create criteria
    print("--- Creating Criteria ---")
    crit1_data = {
        "name": "Profanity Keyword",
        "type": "KEYWORD_PATTERN",
        "criteria_details": {"keywords": ["swearword", "badword"], "match_type": "exact_phrase"},
        "is_active": True
    }
    crit1, status = api.create_criteria(crit1_data)
    print(f"Created Crit 1 (Status {status}): {crit1}")

    crit2_data = {
        "name": "Rapid Reviewer",
        "type": "REVIEW_FREQUENCY",
        "criteria_details": {"max_reviews": 3, "time_window_minutes": 5},
        "is_active": True
    }
    crit2, status = api.create_criteria(crit2_data)
    print(f"Created Crit 2 (Status {status}): {crit2}")

    # Get a specific criteria
    print("\n--- Getting Crit 1 ---")
    fetched_crit1, status = api.get_criteria(crit1['id'])
    print(f"Fetched Crit 1 (Status {status}): {fetched_crit1}")

    # Get all active criteria
    print("\n--- Getting All Active Criteria ---")
    all_active, status = api.get_all_active_criteria()
    print(f"All Active Criteria (Status {status}): {all_active}")

    # Update a criteria
    print("\n--- Updating Crit 1 ---")
    update_data = {"is_active": False}
    updated_crit1, status = api.update_criteria(crit1['id'], update_data)
    print(f"Updated Crit 1 (Status {status}): {updated_crit1}")

    # Get all active criteria again (Crit 1 should be gone)
    print("\n--- Getting All Active Criteria (After Update) ---")
    all_active_after_update, status = api.get_all_active_criteria()
    print(f"All Active Criteria (Status {status}): {all_active_after_update}")

    # Delete a criteria
    print("\n--- Deleting Crit 2 ---")
    delete_result, status = api.delete_criteria(crit2['id'])
    print(f"Delete Crit 2 (Status {status}): {delete_result}")
