import logging
import requests
from django.conf import settings
from django.http import HttpRequest

logger = logging.getLogger(__name__)

def verify_turnstile(request: HttpRequest, token: str = None) -> bool:
    """
    Verify Cloudflare Turnstile token.
    Bypasses verification if:
    1. DEBUG is True
    2. TEST_MODE is True
    3. X-Turnstile-Bypass header matches TURNSTILE_BYPASS_TOKEN
    """
    # 1. Environment-based bypass
    if getattr(settings, "DEBUG", False) or getattr(settings, "TEST_MODE", False):
        return True
    
    # 2. Header-based bypass (for Postman/Automated testing)
    bypass_token = getattr(settings, "TURNSTILE_BYPASS_TOKEN", None)
    if bypass_token and request.headers.get("X-Turnstile-Bypass") == bypass_token:
        return True

    # 3. Extract token if not provided
    if not token and request:
        token = request.data.get("cf-turnstile-response")

    if not token:
        return False
    
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    
    # Optional: pass remote IP for validation
    from ipware import get_client_ip
    client_ip, _ = get_client_ip(request)
    if client_ip:
        data["remoteip"] = client_ip

    try:
        resp = requests.post(url, data=data, timeout=5)
        result = resp.json()
        success = result.get("success", False)
        if not success:
            logger.warning(f"Turnstile verification failed: {result.get('error-codes')}")
        return success
    except Exception as e:
        logger.error(f"Turnstile verification error: {str(e)}")
        return False
