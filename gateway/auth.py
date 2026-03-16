"""
Authentication middleware for the gateway.
"""

import hmac
import hashlib
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from .config import config

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Verify the API key from the request header.

    Returns the validated API key or raises HTTPException.
    """
    expected_key = config.api_key

    if not expected_key:
        # No API key configured - allow all requests in development
        if config.debug:
            return "debug-mode"
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: CMO_GATEWAY_API_KEY not set"
        )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return api_key


def verify_slack_signature(
    request_body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str
) -> bool:
    """
    Verify Slack webhook signature.

    Args:
        request_body: Raw request body bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        signing_secret: Slack app signing secret

    Returns:
        True if signature is valid
    """
    # Check timestamp to prevent replay attacks (within 5 minutes)
    import time
    current_time = int(time.time())
    request_time = int(timestamp)

    if abs(current_time - request_time) > 300:  # 5 minutes
        return False

    # Compute expected signature
    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    expected_sig = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_sig)
