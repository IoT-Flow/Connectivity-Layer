"""
Unit Tests for Password Utilities - PBKDF2-SHA256 (TDD)
Tests the password hashing implementation for security compliance
"""

import pytest
from src.utils.password import (
    hash_password,
    verify_password,
    needs_rehash,
    PBKDF2_ITERATIONS,
    PBKDF2_KEYLEN,
    PBKDF2_DIGEST,
)


@pytest.mark.unit
class TestHashPassword:
    """Tests for hash_password function"""

    def test_hash_password_returns_correct_format(self):
        """Should return hash in pbkdf2_sha256 format"""
        password = "test123"
        hashed = hash_password(password)

        assert hashed.startswith("pbkdf2_sha256$")
        parts = hashed.split("$")
        assert len(parts) == 4
        assert parts[0] == "pbkdf2_sha256"

    def test_hash_password_uses_correct_iterations(self):
        """Should use correct number of iterations"""
        password = "test123"
        hashed = hash_password(password)

        parts = hashed.split("$")
        iterations = int(parts[1])
        assert iterations == PBKDF2_ITERATIONS
        assert iterations == 210000

    def test_hash_password_generates_unique_hashes(self):
        """Should generate unique hashes for same password (different salts)"""
        password = "samepassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts = different hashes

    def test_hash_password_generates_unique_salts(self):
        """Should generate unique salts"""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        salt1 = hash1.split("$")[2]
        salt2 = hash2.split("$")[2]

        assert salt1 != salt2

    def test_hash_password_rejects_empty_password(self):
        """Should reject empty password"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_rejects_non_string(self):
        """Should reject non-string password"""
        with pytest.raises(ValueError, match="Password must be a string"):
            hash_password(123)

    def test_hash_password_handles_long_passwords(self):
        """Should handle very long passwords"""
        password = "a" * 10000
        hashed = hash_password(password)

        assert hashed.startswith("pbkdf2_sha256$")
        assert verify_password(password, hashed)

    def test_hash_password_handles_special_characters(self):
        """Should handle passwords with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_hash_password_handles_unicode(self):
        """Should handle Unicode passwords"""
        password = "пароль密码🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed)


@pytest.mark.unit
class TestVerifyPassword:
    """Tests for verify_password function"""

    def test_verify_password_correct(self):
        """Should verify correct password"""
        password = "mypassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Should reject incorrect password"""
        password = "mypassword"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Should be case sensitive"""
        password = "MyPassword"
        hashed = hash_password(password)

        assert verify_password("mypassword", hashed) is False

    def test_verify_password_rejects_empty_password(self):
        """Should reject empty password"""
        hashed = hash_password("test123")

        assert verify_password("", hashed) is False

    def test_verify_password_handles_malformed_hash(self):
        """Should handle malformed hash gracefully"""
        assert verify_password("test123", "invalid_hash") is False
        assert verify_password("test123", "pbkdf2_sha256$invalid") is False

    def test_verify_password_supports_werkzeug_format(self):
        """Should support werkzeug hash format (for migration)"""
        from werkzeug.security import generate_password_hash as werkzeug_hash

        password = "test123"
        werkzeug_hashed = werkzeug_hash(password)

        assert verify_password(password, werkzeug_hashed) is True
        assert verify_password("wrong", werkzeug_hashed) is False

    def test_verify_password_rejects_none(self):
        """Should handle None values"""
        assert verify_password(None, "hash") is False
        assert verify_password("password", None) is False

    def test_verify_password_handles_wrong_algorithm(self):
        """Should handle hash with wrong algorithm"""
        assert verify_password("test123", "md5$abcd$1234") is False


@pytest.mark.unit
class TestNeedsRehash:
    """Tests for needs_rehash function"""

    def test_needs_rehash_current_pbkdf2(self):
        """Should return False for current PBKDF2 hash"""
        password = "test123"
        hashed = hash_password(password)

        assert needs_rehash(hashed) is False

    def test_needs_rehash_werkzeug_hash(self):
        """Should return True for werkzeug hash"""
        from werkzeug.security import generate_password_hash as werkzeug_hash

        password = "test123"
        hashed = werkzeug_hash(password)

        assert needs_rehash(hashed) is True

    def test_needs_rehash_old_pbkdf2_low_iterations(self):
        """Should return True for old PBKDF2 with low iterations"""
        # Manually create hash with low iterations
        old_hash = "pbkdf2_sha256$10000$saltsalt$hashhash"

        assert needs_rehash(old_hash) is True

    def test_needs_rehash_malformed_hash(self):
        """Should return True for malformed hash"""
        assert needs_rehash("invalid_hash") is True
        assert needs_rehash("pbkdf2_sha256$invalid") is True

    def test_needs_rehash_current_iterations(self):
        """Should return False for hash with current iterations"""
        password = "test123"
        hashed = hash_password(password)

        assert needs_rehash(hashed) is False

    def test_needs_rehash_none(self):
        """Should handle None value"""
        assert needs_rehash(None) is True

    def test_needs_rehash_empty_string(self):
        """Should handle empty string"""
        assert needs_rehash("") is True


@pytest.mark.unit
class TestSecurityProperties:
    """Tests for security properties"""

    def test_uses_sha256_digest(self):
        """Should use SHA-256 as digest algorithm"""
        assert PBKDF2_DIGEST == "sha256"

    def test_uses_owasp_compliant_iterations(self):
        """Should use at least 100,000 iterations (OWASP 2023)"""
        assert PBKDF2_ITERATIONS >= 100000
        assert PBKDF2_ITERATIONS == 210000

    def test_uses_sufficient_key_length(self):
        """Should use at least 32 bytes key length"""
        assert PBKDF2_KEYLEN >= 32

    def test_generates_32_byte_salt(self):
        """Should generate 32-byte salt (256 bits)"""
        import base64

        password = "test123"
        hashed = hash_password(password)

        salt_b64 = hashed.split("$")[2]
        salt_bytes = base64.b64decode(salt_b64)

        assert len(salt_bytes) == 32  # 256 bits

    def test_timing_attack_resistance(self):
        """Should be resistant to timing attacks"""
        import time

        password = "correctpassword"
        hashed = hash_password(password)

        # Measure time for correct password
        times_correct = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password(password, hashed)
            times_correct.append(time.perf_counter() - start)

        # Measure time for incorrect password
        times_incorrect = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password("wrongpassword", hashed)
            times_incorrect.append(time.perf_counter() - start)

        # Times should be similar (constant-time comparison)
        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)

        # Allow 50% variance (timing attacks need <1% to be exploitable)
        ratio = max(avg_correct, avg_incorrect) / min(avg_correct, avg_incorrect)
        assert ratio < 1.5, f"Timing difference too large: {ratio}"


@pytest.mark.unit
class TestMigrationSupport:
    """Tests for migration from werkzeug to PBKDF2"""

    def test_can_verify_werkzeug_hashes(self):
        """Should be able to verify werkzeug hashes during migration"""
        from werkzeug.security import generate_password_hash as werkzeug_hash

        password = "migratepassword"
        old_hash = werkzeug_hash(password)

        # Should verify successfully
        assert verify_password(password, old_hash) is True

        # Should indicate needs rehash
        assert needs_rehash(old_hash) is True

    def test_creates_new_pbkdf2_hash_when_rehashing(self):
        """Should create new PBKDF2 hash when rehashing needed"""
        from werkzeug.security import generate_password_hash as werkzeug_hash

        password = "oldpassword"
        old_hash = werkzeug_hash(password)

        # Verify old hash works
        assert verify_password(password, old_hash) is True

        # Create new hash
        new_hash = hash_password(password)

        # New hash should work
        assert verify_password(password, new_hash) is True

        # New hash should not need rehash
        assert needs_rehash(new_hash) is False


@pytest.mark.unit
class TestPerformance:
    """Tests for performance requirements"""

    def test_hash_password_performance(self):
        """Should hash password in reasonable time (<500ms)"""
        import time

        password = "test123"

        start = time.time()
        hash_password(password)
        duration = time.time() - start

        assert duration < 0.5, f"Hashing took {duration}s, expected <0.5s"

    def test_verify_password_performance(self):
        """Should verify password in reasonable time (<500ms)"""
        import time

        password = "test123"
        hashed = hash_password(password)

        start = time.time()
        verify_password(password, hashed)
        duration = time.time() - start

        assert duration < 0.5, f"Verification took {duration}s, expected <0.5s"


@pytest.mark.unit
class TestBackwardCompatibility:
    """Tests for backward compatibility with werkzeug"""

    def test_generate_password_hash_alias(self):
        """Should support generate_password_hash alias"""
        from src.utils.password import generate_password_hash

        password = "test123"
        hashed = generate_password_hash(password)

        assert hashed.startswith("pbkdf2_sha256$")

    def test_check_password_hash_alias(self):
        """Should support check_password_hash alias"""
        from src.utils.password import check_password_hash, generate_password_hash

        password = "test123"
        hashed = generate_password_hash(password)

        assert check_password_hash(hashed, password) is True
        assert check_password_hash(hashed, "wrong") is False
