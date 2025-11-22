from functools import wraps
from flask import request, jsonify, current_app
import hashlib
import time
import os
from src.models import Device


def hash_api_key(api_key):
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def authenticate_device(f):
    """Decorator to authenticate device using API key"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return (
                jsonify(
                    {
                        "error": "API key required",
                        "message": "Please provide API key in X-API-Key header",
                    }
                ),
                401,
            )

        # Find device by API key
        device = Device.query.filter_by(api_key=api_key).first()

        if not device:
            current_app.logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            return (
                jsonify(
                    {
                        "error": "Invalid API key",
                        "message": "The provided API key is not valid",
                    }
                ),
                401,
            )

        # Auto-activate device on first data submission
        if device.status == "inactive":
            from src.models import db
            from datetime import datetime, timezone
            
            device.status = "active"
            device.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            current_app.logger.info(
                f"Device auto-activated: {device.name} (ID: {device.id}) - "
                f"First telemetry submission received"
            )
        
        # Check if device is in maintenance mode
        if device.status == "maintenance":
            return (
                jsonify(
                    {
                        "error": "Device in maintenance",
                        "message": "Device is currently in maintenance mode",
                    }
                ),
                403,
            )

        # Update last seen timestamp
        device.update_last_seen()

        # Add device to request context
        request.device = device

        return f(*args, **kwargs)

    return decorated_function


def rate_limit_device(max_requests=60, window=60, per_device=True):
    """Advanced rate limiting decorator (currently disabled)"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, "device") and per_device:
                return jsonify({"error": "Authentication required"}), 401

            # Determine rate limit key
            if per_device and hasattr(request, "device"):
                limit_key = f"rate_limit:device:{request.device.id}"
            else:
                # Global rate limiting for registration endpoints
                limit_key = f"rate_limit:global:{request.remote_addr}"

            current_time = int(time.time())
            window_key = f"{limit_key}:{current_time // window}"

            try:
                # Rate limiting currently disabled
                # Can be implemented with database or nginx if needed
                current_app.logger.debug(f"Rate limiting bypassed for {window_key}")
                return f(*args, **kwargs)

            except Exception as e:
                # Log error but don't block request
                current_app.logger.error(f"Rate limiting error: {str(e)}")
                return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_json_payload(required_fields=None):
    """Decorator to validate JSON payload"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return (
                    jsonify(
                        {
                            "error": "Invalid content type",
                            "message": "Content-Type must be application/json",
                        }
                    ),
                    400,
                )

            data = request.get_json()
            if not data:
                return (
                    jsonify(
                        {
                            "error": "Invalid JSON",
                            "message": "Request body must contain valid JSON",
                        }
                    ),
                    400,
                )

            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return (
                        jsonify(
                            {
                                "error": "Missing required fields",
                                "message": f'Required fields: {", ".join(missing_fields)}',
                            }
                        ),
                        400,
                    )

            request.validated_json = data
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_request_middleware():
    """Middleware to log all requests"""

    def middleware(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Log request
            current_app.logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

            # Execute the request
            response = f(*args, **kwargs)

            # Log response time
            execution_time = time.time() - start_time
            current_app.logger.info(f"Response: {request.method} {request.path} completed in {execution_time:.3f}s")

            return response

        return decorated_function

    return middleware


ADMIN_TOKEN = os.environ.get("IOTFLOW_ADMIN_TOKEN", "test")


def require_admin_token(f):
    """Decorator to require a valid admin token for admin endpoints"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("admin "):
            return jsonify({"error": "Admin token required"}), 401
        token = auth_header.split(" ", 1)[1]
        if token != ADMIN_TOKEN:
            return jsonify({"error": "Invalid admin token"}), 403
        return f(*args, **kwargs)

    return decorated_function


def require_admin_jwt(f):
    """Decorator to require a valid JWT token with admin privileges"""
    import jwt
    from src.models import User
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return jsonify({
                "error": "Authorization required",
                "message": "Please provide a valid JWT token"
            }), 401
        
        # Check if it's a Bearer token
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Invalid authorization format",
                "message": "Authorization header must be 'Bearer <token>'"
            }), 401
        
        # Extract token
        token = auth_header.split(" ", 1)[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check if user is admin
            if not payload.get('is_admin', False):
                return jsonify({
                    "error": "Admin access required",
                    "message": "This action requires administrator privileges"
                }), 403
            
            # Verify user exists and is active
            user = User.query.filter_by(user_id=payload.get('user_id')).first()
            if not user:
                return jsonify({
                    "error": "User not found",
                    "message": "The user associated with this token no longer exists"
                }), 401
            
            if not user.is_active:
                return jsonify({
                    "error": "Account inactive",
                    "message": "This account has been deactivated"
                }), 401
            
            if not user.is_admin:
                return jsonify({
                    "error": "Admin access required",
                    "message": "This action requires administrator privileges"
                }), 403
            
            # Store user in request context
            request.current_user = user
            
            return f(*args, **kwargs)
        
        except jwt.ExpiredSignatureError:
            return jsonify({
                "error": "Token expired",
                "message": "Your authentication token has expired"
            }), 401
        
        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Invalid token",
                "message": "The provided token is invalid"
            }), 401
        
        except Exception as e:
            current_app.logger.error(f"Admin JWT validation error: {str(e)}")
            return jsonify({
                "error": "Authentication failed",
                "message": "An error occurred during authentication"
            }), 401
    
    return decorated_function
