"""
Minimal HS256 JWT implementation using Python stdlib only.

Avoids the system `cryptography` package which may not be available in all
environments. Only supports HMAC-SHA256 (HS256) — sufficient for our use case.
"""
import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any


class ExpiredSignatureError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(text: str) -> bytes:
    padding = (4 - len(text) % 4) % 4
    return base64.urlsafe_b64decode(text + "=" * padding)


def encode(payload: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    """Encode a payload as a signed JWT string."""
    if algorithm != "HS256":
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only HS256 is supported.")

    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64url_encode(json.dumps(payload, separators=(",", ":"), default=_json_default).encode())

    signing_input = f"{header}.{body}"
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(sig)}"


def decode(token: str, secret: str, algorithms: list[str] | None = None) -> dict[str, Any]:
    """
    Decode and verify a JWT string.

    Raises ExpiredSignatureError if the token's 'exp' claim is in the past.
    Raises InvalidTokenError for any other validation failure.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Token must have three segments")

        header_enc, body_enc, sig_enc = parts

        # Verify signature (constant-time comparison)
        signing_input = f"{header_enc}.{body_enc}"
        expected = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected), sig_enc):
            raise InvalidTokenError("Signature verification failed")

        payload = json.loads(_b64url_decode(body_enc).decode())

    except (InvalidTokenError, ExpiredSignatureError):
        raise
    except Exception as exc:
        raise InvalidTokenError(f"Malformed token: {exc}") from exc

    # Check expiry
    exp = payload.get("exp")
    if exp is not None:
        if datetime.utcnow().timestamp() > exp:
            raise ExpiredSignatureError("Token has expired")

    return payload


def _json_default(obj: Any) -> Any:
    """Serialise datetime objects to Unix timestamps."""
    if isinstance(obj, datetime):
        return obj.timestamp()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
