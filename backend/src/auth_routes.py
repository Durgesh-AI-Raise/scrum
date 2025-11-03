from flask import Blueprint, request, jsonify, current_app
from .auth_service import AuthService, jwt
from .user_service import UserService # Import UserService
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)

# Middleware for protected routes
def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Authorization token missing"}), 401
        
        token_parts = token.split(" ")
        if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
            return jsonify({"message": "Invalid token format"}), 401

        decoded_token = AuthService.decode_token(token_parts[1])
        if "error" in decoded_token:
            return jsonify({"message": decoded_token["error"]}), 401
        
        request.user = decoded_token # Attach user info to request
        return func(*args, **kwargs)
    return wrapper

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role_name = data.get('role_name', 'Trust & Safety Analyst') # Default role

    if not all([username, password, email]):
        return jsonify({"message": "Missing data"}), 400

    if UserService.get_user_by_username(username):
        return jsonify({"message": "Username already exists"}), 409

    hashed_password = AuthService.hash_password(password)
    
    role = UserService.get_role_by_name(role_name)
    if not role:
        # Create the role if it doesn't exist (for initial setup simplicity)
        role_id = UserService.create_role(role_name)
    else:
        role_id = role["role_id"]

    user_id = UserService.create_user(username, hashed_password, email, role_id)

    return jsonify({"message": "User registered successfully", "user_id": user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({"message": "Missing username or password"}), 400

    user = UserService.get_user_by_username(username)

    if user and AuthService.verify_password(user["password_hash"], password):
        access_token = AuthService.create_access_token(user["user_id"], user["role_name"])
        return jsonify({"access_token": access_token, "role": user["role_name"]}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/test-protected', methods=['GET'])
@jwt_required
def protected_test():
    return jsonify({"message": f"Welcome, {request.user['role']}! Your user ID is {request.user['user_id']}"}), 200