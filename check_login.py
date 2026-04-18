import requests
BASE = "http://localhost:8000"
BYPASS = "kJ8mP2xQnR5vY9wL3tA6bN1cE4hG7fD0"
r = requests.post(
    f"{BASE}/api/v1/auth/login/",
    json={"identifier": "root", "password": "Admin123!", "cf_turnstile_response": BYPASS},
    headers={"Content-Type": "application/json", "X-Tenant": "shawahid"}
)
print("Status:", r.status_code)
print("Body:", r.text[:300])
