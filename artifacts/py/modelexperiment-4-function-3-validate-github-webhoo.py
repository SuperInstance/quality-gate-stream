"""
PLATO Room: modelexperiment
Tile: **4. Function 3: `validate_github_webhook`**
Domain: modelexperiment
"""

import hmac
import hashlib

def validate_github_webhook(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Validate a GitHub webhook payload using HMAC-SHA256.
    signature_header format: 'sha256=...'
    Returns True if valid, False otherwise.
    """
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[7:]  # remove 'sha256='
    mac = hmac.new(secret.encode(), payload_body, hashlib.sha256)
    calculated_signature = mac.hexdigest()

    return hmac.compare_digest(calculated_signature, expected_signature)

import hmac
import hashlib

def validate_github_webhook(payload, sig_header, secret_key):
    """
    Validates GitHub webhook signature.
    sig_header should look like 'sha256=hexdigest'.
    secret_key is the webhook secret.
    Returns boolean.
    """
    if not sig_header or not sig_header.startswith('sha256='):
        return False

    received_sig = sig_header[7:]
    computed = hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, received_sig)

