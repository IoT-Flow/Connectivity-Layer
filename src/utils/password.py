"""
Password Utilities - PBKDF2-SHA256
Secure password hashing using PBKDF2 with SHA-256

Format: pbkdf2_sha256$iterations$salt$hash

OWASP Recommendations (2023):
- Use PBKDF2 with at least 100,000 iterations for SHA-256
- Use a unique random salt for each password (32 bytes minimum)
- Use a 32-byte (256-bit) derived key length
"""

import hashlib
import secrets
import base64
from typing import Tuple

# PBKDF2 Configuration (OWASP 2023 recommendations)
PBKDF2_ITERATIONS = 210000  # OWASP 2023 recommendation for PBKDF2-SHA256
PBKDF2_KEYLEN = 32  # 256 bits
PBKDF2_DIGEST = "sha256"
SALT_LENGTH = 32  # 256 bits


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256

    Args:
        password: Plain text password

    Returns:
        Hashed password in format: pbkdf2_sha256$iterations$salt$hash

    Raises:
        ValueError: If password is not a string or is empty
    """
    # Input validation
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    if not password:
        raise ValueError("Password cannot be empty")

    # Generate random salt
    salt = secrets.token_bytes(SALT_LENGTH)
    salt_b64 = base64.b64encode(salt).decode("utf-8")

    # Derive key using PBKDF2
    key = hashlib.pbkdf2_hmac(PBKDF2_DIGEST, password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=PBKDF2_KEYLEN)
    hash_b64 = base64.b64encode(key).decode("utf-8")

    # Return in standardized format
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    Supports both PBKDF2-SHA256 and bcrypt (for migration)

    Args:
        password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    # Input validation
    if not password or not isinstance(password, str):
        return False

    if not hashed_password or not isinstance(hashed_password, str):
        return False

    try:
        # Check if it's a PBKDF2 hash
        if hashed_password.startswith("pbkdf2_sha256$"):
            return _verify_pbkdf2(password, hashed_password)

        # Check if it's a bcrypt hash (for migration compatibility)
        if (
            hashed_password.startswith("$2b$")
            or hashed_password.startswith("$2a$")
            or hashed_password.startswith("$2y$")
        ):
            try:
                import bcrypt

                return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
            except ImportError:
                # If bcrypt not available, return False
                return False

        # Check if it's a werkzeug hash (pbkdf2:sha256:... or scrypt:...)
        if hashed_password.startswith("pbkdf2:") or hashed_password.startswith("scrypt:"):
            from werkzeug.security import check_password_hash as werkzeug_check

            return werkzeug_check(hashed_password, password)

        # Unknown hash format
        return False
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def _verify_pbkdf2(password: str, hashed_password: str) -> bool:
    """
    Verify PBKDF2-SHA256 hash

    Args:
        password: Plain text password
        hashed_password: PBKDF2 hashed password

    Returns:
        True if password matches
    """
    try:
        # Parse hash format: pbkdf2_sha256$iterations$salt$hash
        parts = hashed_password.split("$")

        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False

        iterations = int(parts[1])
        salt_b64 = parts[2]
        original_hash_b64 = parts[3]

        # Validate iterations
        if iterations <= 0:
            return False

        # Decode salt
        salt = base64.b64decode(salt_b64)

        # Derive key with same parameters
        computed_key = hashlib.pbkdf2_hmac(
            PBKDF2_DIGEST, password.encode("utf-8"), salt, iterations, dklen=PBKDF2_KEYLEN
        )

        # Decode original hash
        original_hash = base64.b64decode(original_hash_b64)

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(original_hash, computed_key)

    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed
    Returns True if:
    - Hash is not PBKDF2-SHA256
    - Hash uses outdated number of iterations
    - Hash is malformed

    Args:
        hashed_password: Password hash to check

    Returns:
        True if hash needs to be regenerated
    """
    if not hashed_password or not isinstance(hashed_password, str):
        return True

    # Check if it's bcrypt (needs migration to PBKDF2)
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$") or hashed_password.startswith("$2y$"):
        return True

    # Check if it's werkzeug format (needs migration)
    if hashed_password.startswith("pbkdf2:") or hashed_password.startswith("scrypt:"):
        return True

    # Check if it's PBKDF2
    if not hashed_password.startswith("pbkdf2_sha256$"):
        return True

    try:
        parts = hashed_password.split("$")

        if len(parts) != 4:
            return True

        iterations = int(parts[1])

        # Need rehash if iterations are less than current recommended
        if iterations < PBKDF2_ITERATIONS:
            return True

        return False
    except Exception:
        return True


# Backward compatibility aliases
def generate_password_hash(password):
    """Alias for hash_password (werkzeug compatibility)"""
    return hash_password(password)


def check_password_hash(pwhash, password):
    """Alias for verify_password with reversed parameters (werkzeug compatibility)"""
    return verify_password(password, pwhash)
