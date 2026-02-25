"""
PBKDF2-SHA256 password hashing using Python stdlib only.

Avoids the system bcrypt/cryptography packages which may not be available in all
environments. PBKDF2-SHA256 with a random 32-byte salt and 260,000 iterations
matches OWASP 2023 recommendations.
"""
import hashlib
import hmac
import os
import base64

_ALGORITHM = "sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 32
_SEPARATOR = "$"
_PREFIX = "pbkdf2sha256"


def hash_password(password: str) -> str:
    """
    Hash a plain-text password.

    Returns a portable string in the form:
    ``pbkdf2sha256$<iterations>$<salt_b64>$<hash_b64>``
    """
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode(), salt, _ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode()
    dk_b64 = base64.b64encode(dk).decode()
    return f"{_PREFIX}{_SEPARATOR}{_ITERATIONS}{_SEPARATOR}{salt_b64}{_SEPARATOR}{dk_b64}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plain-text password against a stored PBKDF2 hash.

    Returns False (not an exception) for any malformed or mismatched hash.
    """
    try:
        prefix, iterations_str, salt_b64, dk_b64 = stored_hash.split(_SEPARATOR)
        if prefix != _PREFIX:
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        expected_dk = base64.b64decode(dk_b64)
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac(_ALGORITHM, plain_password.encode(), salt, iterations)
    return hmac.compare_digest(candidate, expected_dk)
