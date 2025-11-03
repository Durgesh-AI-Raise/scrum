import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager

auth_bp = Blueprint('auth', __name__)

# Mock user store for MVP (replace with DB in future)
users = {
    "analyst1": {"password": "password123", "roles": ["analyst"]},
    "admin1": {"password": "adminpassword", "roles": ["admin"]}
}

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    user = users.get(username)

    if not user or user['password'] != password:
        return jsonify({"msg": "Bad username or password"}), 401

    # Create access token with identity and custom claims (e.g., roles)
    access_token = create_access_token(identity=username, additional_claims={"roles": user["roles"]})
    return jsonify(access_token=access_token)

# Example of a protected route (can be used for testing, or actual endpoints in other blueprints)
@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
