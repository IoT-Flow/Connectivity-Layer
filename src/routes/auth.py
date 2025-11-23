"""
Authentication routes
"""

from flask import Blueprint, request, jsonify, current_app
from src.models import User, db
from src.middleware.security import security_headers_middleware
from datetime import datetime, timezone

# Create blueprint for auth routes
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/login", methods=["POST"])
@security_headers_middleware()
def login():
    """User login endpoint
    ---
    tags:
      - Authentication
    summary: User login
    description: Authenticate user and receive user information
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - username
              - password
            properties:
              username:
                type: string
                example: testuser
              password:
                type: string
                example: password123
    responses:
      200:
        description: Login successful
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                message:
                  type: string
                  example: Login successful
                token:
                  type: string
                  example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                user:
                  type: object
      401:
        description: Invalid credentials
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "error": "Missing credentials",
                "message": "username and password are required"
            }), 400
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                "error": "Authentication failed",
                "message": "Invalid username or password"
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                "error": "Account inactive",
                "message": "This account has been deactivated"
            }), 401
        
        # Verify password
        if not user.check_password(password):
            return jsonify({
                "error": "Authentication failed",
                "message": "Invalid username or password"
            }), 401
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"User logged in: {username} (ID: {user.user_id})")
        
        # Return user info
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            "error": "Login failed",
            "message": "An error occurred during login"
        }), 500


@auth_bp.route("/register", methods=["POST"])
@security_headers_middleware()
def register():
    """User registration endpoint
    ---
    tags:
      - Authentication
    summary: Register new user
    description: Create a new user account
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - username
              - email
              - password
            properties:
              username:
                type: string
                minLength: 3
                example: john_doe
              email:
                type: string
                format: email
                example: john@example.com
              password:
                type: string
                minLength: 6
                example: secure_password123
    responses:
      201:
        description: User created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                message:
                  type: string
                user:
                  type: object
      400:
        description: Invalid input
    """
    try:
        data = request.get_json()
        
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
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"User registered: {username} (ID: {user.user_id})")
        
        return jsonify({
            "status": "success",
            "message": "Registration successful",
            "user": user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            "error": "Registration failed",
            "message": "An error occurred during registration"
        }), 500


@auth_bp.route("/logout", methods=["POST"])
@security_headers_middleware()
def logout():
    """User logout endpoint"""
    # In a stateless API, logout is typically handled client-side
    # by removing the token. This endpoint is here for completeness.
    return jsonify({
        "status": "success",
        "message": "Logout successful"
    }), 200
