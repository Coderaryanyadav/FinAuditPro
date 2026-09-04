"""RFC 6238 compliant zero-dependency Time-based One-Time Password (TOTP) generator and verifier."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse


def generate_totp_secret() -> str:
    """Generate a 160-bit (20-byte) cryptographically secure Base32 secret string."""
    raw_bytes = secrets.token_bytes(20)
    return base64.b32encode(raw_bytes).decode("utf-8").replace("=", "")


def generate_totp_code(secret: str, interval: int = 30) -> str:
    """Generate the current 6-digit TOTP token for the given Base32 secret."""
    # Pad secret with '=' if necessary
    s = secret.strip().upper()
    missing_padding = len(s) % 8
    if missing_padding:
        s += "=" * (8 - missing_padding)

    key = base64.b32decode(s, casefold=True)
    counter = int(time.time()) // interval
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1000000:06d}"


def verify_totp_token(secret: str, token: str, window: int = 1, interval: int = 30) -> bool:
    """Verify a 6-digit TOTP token allowing a +/- 1 step drift window (total 90s tolerance)."""
    if not secret or not token:
        return False

    token_str = str(token).strip()
    if len(token_str) != 6 or not token_str.isdigit():
        return False

    s = secret.strip().upper()
    missing_padding = len(s) % 8
    if missing_padding:
        s += "=" * (8 - missing_padding)

    try:
        key = base64.b32decode(s, casefold=True)
    except Exception:
        return False

    current_counter = int(time.time()) // interval
    for offset_i in range(-window, window + 1):
        counter = current_counter + offset_i
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
        candidate = f"{code % 1000000:06d}"
        if hmac.compare_digest(candidate, token_str):
            return True

    return False


def get_totp_uri(secret: str, username: str, issuer: str = "FinAuditPro") -> str:
    """Generate standard otpauth:// provisioning URI for QR code scanning in Google/Apple Authenticator."""
    label = urllib.parse.quote(f"{issuer}:{username}")
    params = urllib.parse.urlencode(
        {
            "secret": secret.strip().upper().replace("=", ""),
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": "6",
            "period": "30",
        }
    )
    return f"otpauth://totp/{label}?{params}"
