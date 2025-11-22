"""
User management routes
"""

from flask import Blueprint, request, jsonify, current_app
from src.models import User, db
from src.middleware.auth import require_admin_token, require_admin_jwt
from src.middleware.security import security_headers_middleware
from datetime import datetime, timezone

# Create blueprint for user routes
user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@user_bp.route("", methods=["POST"])
@security_headers_middleware()
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({
                "error": "Missing required fields",
                "message": "username, email, and password are required"
            }), 400
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({
                "error": "Username already exists",
                "message": f"User with username '{username}' already exists"
            }), 409
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                "error": "Email already exists",
                "message": f"User with email '{email}' already exists"
            }), 409
        
        # Create new user
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)
        
        # Set optional fields
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"User created: {username} (ID: {user.user_id})")
        
        return jsonify({
            "status": "success",
            "message": "User created successfully",
            "user": user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating user: {str(e)}")
        return jsonify({
            "error": "User creation failed",
            "message": "An error occurred while creating the user"
        }), 500


@user_bp.route("/<user_id>", methods=["GET"])
@security_headers_middleware()
def get_user(user_id):
    """Get user by ID
    ---
    tags:
      - Users
    summary: Get user details
    description: Get details of a specific user by ID
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: string
        description: User UUID
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    try:
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({
                "error": "User not found",
                "message": f"No user found with ID: {user_id}"
            }), 404
        
        return jsonify({
            "status": "success",
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error getting user: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve user",
            "message": "An error occurred while retrieving the user"
        }), 500


@user_bp.route("", methods=["GET"])
@security_headers_middleware()
@require_admin_jwt
def list_users():
    """List all users (Admin only)
    ---
    tags:
      - Users
    summary: List users (Admin only)
    description: Get list of all users with pagination. Requires admin privileges.
    security:
      - BearerAuth: []
    parameters:
      - name: limit
        in: query
        schema:
          type: integer
          default: 100
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of users
      401:
        description: Unauthorized - invalid or missing token
      403:
        description: Forbidden - admin privileges required
    """
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get users
        users = User.query.limit(limit).offset(offset).all()
        
        return jsonify({
            "status": "success",
            "users": [user.to_dict() for user in users],
            "meta": {
                "total": User.query.count(),
                "limit": limit,
                "offset": offset
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error listing users: {str(e)}")
        return jsonify({
            "error": "Failed to list users",
            "message": "An error occurred while listing users"
        }), 500


@user_bp.route("/<user_id>", methods=["PUT"])
@security_headers_middleware()
def update_user(user_id):
    """Update user information
    ---
    tags:
      - Users
    summary: Update user
    description: Update user information
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              username:
                type: string
              email:
                type: string
              password:
                type: string
              is_active:
                type: boolean
    responses:
      200:
        description: User updated
      404:
        description: User not found
    """
    try:
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({
                "error": "User not found",
                "message": f"No user found with ID: {user_id}"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields
        if 'email' in data:
            # Check if email is already taken by another user
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.user_id != user_id:
                return jsonify({
                    "error": "Email already exists",
                    "message": f"Email '{data['email']}' is already in use"
                }), 409
            user.email = data['email']
        
        if 'username' in data:
            # Check if username is already taken by another user
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.user_id != user_id:
                return jsonify({
                    "error": "Username already exists",
                    "message": f"Username '{data['username']}' is already in use"
                }), 409
            user.username = data['username']
        
        if 'password' in data:
            user.set_password(data['password'])
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"User updated: {user.username} (ID: {user.user_id})")
        
        return jsonify({
            "status": "success",
            "message": "User updated successfully",
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            "error": "User update failed",
            "message": "An error occurred while updating the user"
        }), 500


@user_bp.route("/<user_id>", methods=["DELETE"])
@security_headers_middleware()
@require_admin_jwt
def delete_user(user_id):
    """Delete or deactivate a user (Admin only)
    ---
    tags:
      - Users
    summary: Delete user (Admin only)
    description: Deactivate a user account (soft delete). Requires admin privileges.
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: User deactivated successfully
      401:
        description: Unauthorized - invalid or missing token
      403:
        description: Forbidden - admin privileges required
      404:
        description: User not found
      200:
        description: User deactivated
      404:
        description: User not found
    """
    try:
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({
                "error": "User not found",
                "message": f"No user found with ID: {user_id}"
            }), 404
        
        # Soft delete - deactivate instead of deleting
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"User deactivated: {user.username} (ID: {user.user_id})")
        
        return jsonify({
            "status": "success",
            "message": "User deactivated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        return jsonify({
            "error": "User deletion failed",
            "message": "An error occurred while deleting the user"
        }), 500
