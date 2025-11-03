
import uuid
from datetime import datetime
import copy
from flask import Flask, request, jsonify

# --- Persistence Layer (In-memory AbuseTypeRepository) ---
class AbuseTypeRepository:
    def __init__(self):
        self._db = {}  # In-memory dictionary to simulate database

    def create(self, abuse_type_data):
        abuse_type_id = abuse_type_data.get('id', str(uuid.uuid4()))
        if abuse_type_id in self._db:
            raise ValueError(f"Abuse type with ID {abuse_type_id} already exists.")

        current_time = datetime.utcnow().isoformat() + 'Z' # ISO 8601 format with Z for UTC
        
        # Ensure required fields are present with defaults if not provided
        new_abuse_type = {
            'id': abuse_type_id,
            'name': abuse_type_data.get('name'),
            'description': abuse_type_data.get('description'),
            'severity': abuse_type_data.get('severity'),
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': abuse_type_data.get('is_active', True),
            'metadata': abuse_type_data.get('metadata', {}),
            'detection_rules': abuse_type_data.get('detection_rules', [])
        }
        
        # Basic validation for required fields
        if not all(new_abuse_type[k] is not None for k in ['name', 'description', 'severity']):
            raise ValueError("Missing required fields: name, description, and severity.")
        if new_abuse_type['severity'] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError("Invalid severity value.")

        self._db[abuse_type_id] = copy.deepcopy(new_abuse_type)
        return self._db[abuse_type_id]

    def get_all(self):
        return list(self._db.values())

    def get_by_id(self, abuse_type_id):
        return copy.deepcopy(self._db.get(abuse_type_id))

    def update(self, abuse_type_id, update_data):
        if abuse_type_id not in self._db:
            return None
        
        existing_data = self._db[abuse_type_id]
        for key, value in update_data.items():
            if key not in ['id', 'created_at']: # Don't allow updating immutable fields
                existing_data[key] = value
        
        existing_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Re-validate severity if updated
        if 'severity' in update_data and update_data['severity'] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError("Invalid severity value in update.")

        self._db[abuse_type_id] = copy.deepcopy(existing_data)
        return self._db[abuse_type_id]

    def delete(self, abuse_type_id):
        if abuse_type_id in self._db:
            del self._db[abuse_type_id]
            return True
        return False

# --- API Layer (Flask App) ---
app = Flask(__name__)
abuse_type_repository = AbuseTypeRepository()

@app.route('/api/v1/abuse-types', methods=['POST'])
def create_abuse_type():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body cannot be empty'}), 400
    try:
        new_abuse_type = abuse_type_repository.create(data)
        return jsonify(new_abuse_type), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/v1/abuse-types', methods=['GET'])
def get_all_abuse_types():
    abuse_types = abuse_type_repository.get_all()
    return jsonify(abuse_types), 200

@app.route('/api/v1/abuse-types/<string:abuse_type_id>', methods=['GET'])
def get_abuse_type_by_id(abuse_type_id):
    abuse_type = abuse_type_repository.get_by_id(abuse_type_id)
    if abuse_type:
        return jsonify(abuse_type), 200
    return jsonify({'error': 'Abuse type not found'}), 404

@app.route('/api/v1/abuse-types/<string:abuse_type_id>', methods=['PUT'])
def update_abuse_type(abuse_type_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body cannot be empty'}), 400
    try:
        updated_abuse_type = abuse_type_repository.update(abuse_type_id, data)
        if updated_abuse_type:
            return jsonify(updated_abuse_type), 200
        return jsonify({'error': 'Abuse type not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/v1/abuse-types/<string:abuse_type_id>', methods=['DELETE'])
def delete_abuse_type(abuse_type_id):
    success = abuse_type_repository.delete(abuse_type_id)
    if success:
        return jsonify({'message': f'Abuse type {abuse_type_id} deleted successfully'}), 204
    return jsonify({'error': 'Abuse type not found'}), 404

if __name__ == '__main__':
    # Example usage for testing the API locally
    # To run: python api.py
    # Then use curl or Postman to interact with: http://127.0.0.1:5000/api/v1/abuse-types
    
    # Pre-populate with some data for testing
    try:
        abuse_type_repository.create({
            "id": "a1b2c3d4-e5f6-4789-1234-567890abcdef",
            "name": "Fake Reviews",
            "description": "Reviews created with malicious intent to manipulate product perception, not reflecting a genuine customer experience.",
            "severity": "HIGH",
            "is_active": True,
            "detection_rules": [
                {
                    "rule_id": str(uuid.uuid4()),
                    "rule_name": "High Volume New Accounts",
                    "rule_type": "BEHAVIORAL_ML",
                    "status": "ACTIVE",
                    "configuration": {"model_id": "ml-fake-review-v1", "threshold": 0.8}
                }
            ]
        })
        abuse_type_repository.create({
            "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef0",
            "name": "Incentivized Reviews",
            "description": "Reviews provided in exchange for compensation or free products, violating Amazon's policies on unbiased reviews.",
            "severity": "MEDIUM",
            "is_active": True
        })
    except ValueError as e:
        print(f"Error pre-populating data: {e}")

    app.run(debug=True, port=5000)
