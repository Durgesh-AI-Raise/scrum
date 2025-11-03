import uuid
from .auth_service import AuthService # Needed for simulating password hashing

class UserService:
    # In a real application, this would interact with a database
    # For now, we simulate user data
    _users_db = {
        "analyst": {
            "user_id": "mock_user_id_123",
            "username": "analyst",
            "password_hash": AuthService.hash_password("password123"),
            "email": "analyst@example.com",
            "role_id": "analyst_role_uuid"
        },
        "admin": {
            "user_id": "mock_admin_id_456",
            "username": "admin",
            "password_hash": AuthService.hash_password("adminpass"),
            "email": "admin@example.com",
            "role_id": "admin_role_uuid"
        }
    }

    _roles_db = {
        "analyst_role_uuid": {"role_id": "analyst_role_uuid", "role_name": "Trust & Safety Analyst", "description": "Can view and flag reviews"},
        "admin_role_uuid": {"role_id": "admin_role_uuid", "role_name": "Admin", "description": "Can manage users and roles"}
    }

    @staticmethod
    def create_user(username, password_hash, email, role_id):
        new_user_id = str(uuid.uuid4())
        UserService._users_db[username] = {
            "user_id": new_user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "role_id": role_id
        }
        print(f"Simulated: Creating user {username} with role {role_id}")
        return new_user_id

    @staticmethod
    def get_user_by_username(username):
        user_data = UserService._users_db.get(username)
        if user_data:
            role = UserService._roles_db.get(user_data["role_id"])
            user_data["role_name"] = role["role_name"] if role else "Unknown"
        return user_data
    
    @staticmethod
    def get_role_by_id(role_id):
        return UserService._roles_db.get(role_id)

    @staticmethod
    def get_role_by_name(role_name):
        for role_id, role_data in UserService._roles_db.items():
            if role_data["role_name"] == role_name:
                return role_data
        return None

    @staticmethod
    def create_role(role_name, description=None):
        new_role_id = str(uuid.uuid4())
        UserService._roles_db[new_role_id] = {
            "role_id": new_role_id,
            "role_name": role_name,
            "description": description
        }
        print(f"Simulated: Creating role {role_name}")
        return new_role_id

    @staticmethod
    def assign_user_role(user_id, role_id):
        for username, user_data in UserService._users_db.items():
            if user_data["user_id"] == user_id:
                if role_id in UserService._roles_db:
                    user_data["role_id"] = role_id
                    print(f"Simulated: Assigning role {role_id} to user {user_id}")
                    return True
                return False # Role not found
        return False # User not found