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
        logger.info(
            "Bypassing Turnstile verification | DEBUG: %s | TEST_MODE: %s",
            getattr(settings, "DEBUG", False),
            getattr(settings, "TEST_MODE", False),
        )
        return True

    # 2. Header-based bypass (for Postman/Automated testing)
    bypass_token = getattr(settings, "TURNSTILE_BYPASS_TOKEN", None)
    if bypass_token and request.headers.get("X-Turnstile-Bypass") == bypass_token:
        logger.info(
            'Bypassing Turnstile verification | bypass_token: <REDACTED> | request.headers.get("X-Turnstile-Bypass"): %s',
            request.headers.get("X-Turnstile-Bypass"),
        )
        return True

    # 3. Request-based bypass (for Postman/Automated testing)
    if request.data.get("cf_turnstile_response") == settings.TURNSTILE_BYPASS_TOKEN:
        logger.info("Bypassing Turnstile verification | cf_turnstile_response: %s", request.data.get("cf_turnstile_response"))
        return True

    # 4. Extract token if not provided
    if not token and request:
        logger.info("Extracting token from request")
        token = request.data.get("cf_turnstile_response")

    if not token:
        logger.info("No token provided | token: %s", token)
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
        logger.info("Turnstile verification data: %s", data)
        data["remoteip"] = client_ip

    try:
        resp = requests.post(url, data=data, timeout=5)
        logger.info("Turnstile verification response: %s", resp)
        result = resp.json()
        logger.info("Turnstile verification result: %s", result)
        success = result.get("success", False)
        if not success:
            logger.warning(f"Turnstile verification failed: {result.get('error-codes')}")
        return success
    except Exception as e:
        logger.error(f"Turnstile verification error: {str(e)}")
        return False
