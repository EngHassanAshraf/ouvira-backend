import requests
from django.conf import settings

def verify_turnstile(token: str, remote_ip: str = None) -> bool:
    if getattr(settings, "TEST_MODE", True):
        return True
    
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        resp = requests.post(url, data=data, timeout=5)
        result = resp.json()
        return result.get("success", False)
    except Exception:
        return False
