from flask import Blueprint, request, jsonify
from .user_service import UserService
from .auth_routes import jwt_required # Import jwt_required and role_required
from functools import wraps

user_bp = Blueprint('user', __name__)

# Helper for role-based authorization
def role_required(required_role):
    def decorator(func):
        @wraps(func)
        @jwt_required
        def wrapper(*args, **kwargs):
            if hasattr(request, 'user') and request.user.get('role') == required_role:
                return func(*args, **kwargs)
            return jsonify({"message": "Permission denied"}), 403
        return wrapper
    return decorator

@user_bp.route('/roles', methods=['POST'])
@role_required('Admin') # Only admin can create roles
def create_role():
    data = request.get_json()
    role_name = data.get('role_name')
    description = data.get('description')
    if not role_name:
        return jsonify({"message": "Role name is required"}), 400
    
    if UserService.get_role_by_name(role_name):
        return jsonify({"message": "Role name already exists"}), 409

    role_id = UserService.create_role(role_name, description)
    return jsonify({"message": "Role created successfully", "role_id": role_id}), 201

@user_bp.route('/roles', methods=['GET'])
@role_required('Admin') # Only admin can view roles
def get_all_roles():
    return jsonify(list(UserService._roles_db.values())), 200

@user_bp.route('/users', methods=['GET'])
@role_required('Admin') # Only admin can view users
def get_all_users():
    # Return users without password hashes
    users_safe = []
    for user in UserService._users_db.values():
        user_copy = user.copy()
        user_copy.pop("password_hash", None)
        role = UserService.get_role_by_id(user_copy["role_id"])
        user_copy["role_name"] = role["role_name"] if role else "Unknown"
        users_safe.append(user_copy)
    return jsonify(users_safe), 200

@user_bp.route('/users/<user_id>/role', methods=['PUT'])
@role_required('Admin') # Only admin can assign roles
def assign_role_to_user(user_id):
    data = request.get_json()
    role_id = data.get('role_id')
    if not role_id:
        return jsonify({"message": "Role ID is required"}), 400
    
    if UserService.assign_user_role(user_id, role_id):
        return jsonify({"message": "User role updated successfully"}), 200
    return jsonify({"message": "User or Role not found"}), 404