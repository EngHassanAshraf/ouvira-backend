import requests
import json
import time

BASE_URL = "http://localhost:8000"
TENANT = "shawahid"

def log_api_call(name, resp):
    print(f"[{name}] {resp.status_code} {resp.url}")
    if resp.status_code not in [200, 201]:
        print(f"ERROR BODY: {resp.text[:500]}")
    return resp

def get_data(resp):
    try:
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data
    except:
        return None

def test_recruitment():
    print("--- FULL Recruitment API Lifecycle Verification ---")
    headers = {"X-Tenant": TENANT}
    
    # 1. Login
    login_data = {"identifier": "root", "password": "Admin123!"}
    resp = log_api_call("LOGIN", requests.post(f"{BASE_URL}/api/auth/login/", json=login_data, headers=headers))
    if resp.status_code != 200: return
    access_token = resp.json().get("access")
    headers["Authorization"] = f"Bearer {access_token}"

    # 2. Get Dynamic IDs
    resp = log_api_call("LIST_COMPANIES", requests.get(f"{BASE_URL}/api/company/", headers=headers))
    companies = get_data(resp)
    company = next((c for c in companies if c["name"] == "Shawahid Test Co"), None)
    if not company: return
    company_id = company["id"]

    resp = log_api_call("LIST_DEPTS", requests.get(f"{BASE_URL}/api/hris/core/departments/", headers=headers))
    depts = get_data(resp)
    dept = next((d for d in depts if d["name"] == "Engineering"), None)
    if not dept: return
    dept_id = dept["id"]

    resp = log_api_call("LIST_TITLES", requests.get(f"{BASE_URL}/api/hris/core/job-titles/", headers=headers))
    titles = get_data(resp)
    title = next((t for t in titles if t["title"] == "Software Engineer"), None)
    if not title: return
    title_id = title["id"]

    # 3. Create Hiring Request
    hr_data = {"company": company_id, "job_title": title_id, "department": dept_id, "vacancies": 1, "purpose": "Verification Run"}
    resp = log_api_call("CREATE_HR", requests.post(f"{BASE_URL}/api/hris/recruitment/hiring-requests/", json=hr_data, headers=headers))
    if resp.status_code not in [200, 201]: return
    hr_id = resp.json()["id"]

    # 4. Submit
    log_api_call("SUBMIT_HR", requests.post(f"{BASE_URL}/api/hris/recruitment/hiring-requests/{hr_id}/submit/", headers=headers))

    # 5. Approve
    for role in ["employee", "hr_employee", "direct_manager"]:
        log_api_call(f"APPROVE_{role}", requests.post(f"{BASE_URL}/api/hris/recruitment/hiring-requests/{hr_id}/approve/", 
                                                  json={"role_type": role, "note": "OK"}, headers=headers))

    # 6. Check Ad
    time.sleep(1)
    resp = log_api_call("CHECK_AD", requests.get(f"{BASE_URL}/api/hris/recruitment/job-advertisements/", headers=headers))
    ads = get_data(resp)
    ad = next((a for a in ads if a["hiring_request"] == hr_id), None)
    if not ad: return
    ad_id = ad["id"]

    # 7. Publish
    log_api_call("PUBLISH_AD", requests.post(f"{BASE_URL}/api/hris/recruitment/job-advertisements/{ad_id}/publish/", 
                                         json={"deadline": "2026-12-31", "platforms": ["internal"]}, headers=headers))

    # 8. Candidate
    cand_data = {"first_name": "Verified", "last_name": "Cand", "email": f"vcand.{int(time.time())}@test.com", "company": company_id}
    resp = log_api_call("CREATE_CAND", requests.post(f"{BASE_URL}/api/hris/recruitment/candidates/", json=cand_data, headers=headers))
    if resp.status_code != 201: return
    cand_id = resp.json()["id"]

    # 9. Application
    resp = log_api_call("CREATE_APP", requests.post(f"{BASE_URL}/api/hris/recruitment/applications/", 
                                                json={"candidate": cand_id, "job_advertisement": ad_id}, headers=headers))
    if resp.status_code != 201: return
    app_id = resp.json()["id"]

    # 10. Document Verification (NEW)
    doc_data = {
        "candidate": cand_id,
        "doc_type": "id_copy",
        "file": None # DRF testing usually requires MultiPart if file is present, but let's check if optional
    }
    # Using a dummy text file if possible, or skip actual file upload for now to verify endpoint presence
    print("[DOC] Verification endpoint check...")
    resp = log_api_call("LIST_DOCS", requests.get(f"{BASE_URL}/api/hris/recruitment/documents/", headers=headers))

    # 11. Move to Interview
    log_api_call("MOVE_STAGE", requests.post(f"{BASE_URL}/api/hris/recruitment/applications/{app_id}/move-to-stage/", 
                                           json={"status": "interview"}, headers=headers))

    # 12. Schedule Interview
    iv_data = {"application": app_id, "interview_type": "personal", "interview_date": "2026-05-01T10:00:00Z", "interviewers": [1]}
    resp = log_api_call("SCHEDULE_IV", requests.post(f"{BASE_URL}/api/hris/recruitment/interviews/", json=iv_data, headers=headers))
    if resp.status_code not in [200, 201]: return
    iv_id = resp.json()["id"]

    # 13. Record Result
    log_api_call("RECORD_RESULT", requests.post(f"{BASE_URL}/api/hris/recruitment/interviews/{iv_id}/record-result/", 
                                             json={"scoring_data": {"test": 10}}, headers=headers))

    # 14. Offer
    resp = log_api_call("CREATE_OFFER", requests.post(f"{BASE_URL}/api/hris/recruitment/offers/", 
                                                  json={"application": app_id, "salary": 20000, "start_date": "2026-06-01"}, headers=headers))
    if resp.status_code not in [200, 201]: return
    offer_id = resp.json()["id"]

    # 15. Accept (Bridge)
    unique_nid = str(int(time.time()))[-10:]
    hire_data = {"employee_id": f"VEMP-{int(time.time())}", "national_id": unique_nid, "gender": "M", "date_of_birth": "1990-01-01"}
    log_api_call("ACCEPT_OFFER", requests.post(f"{BASE_URL}/api/hris/recruitment/offers/{offer_id}/accept/", json=hire_data, headers=headers))

    # 16. Onboarding (NEW)
    onboard_data = {
        "candidate": cand_id,
        "tasks": {"workspace": True, "email": False},
        "status": "in_progress"
    }
    resp = log_api_call("CREATE_ONBOARDING", requests.post(f"{BASE_URL}/api/hris/recruitment/onboarding/", json=onboard_data, headers=headers))
    if resp.status_code in [200, 201]:
        onboard_id = resp.json()["id"]
        log_api_call("GET_ONBOARDING", requests.get(f"{BASE_URL}/api/hris/recruitment/onboarding/{onboard_id}/", headers=headers))

    # 17. Final Check
    print("\n--- Final Bridge Verification ---")
    time.sleep(1)
    resp = log_api_call("VERIFY_HRIS", requests.get(f"{BASE_URL}/api/hris/core/employees/", headers=headers))
    emps = get_data(resp)
    if emps is not None:
        found = any(e["employee_id"] == hire_data["employee_id"] for e in emps)
        if found:
            print("[SUCCESS] Recruitment flow verified and bridge is operational!")
        else:
            print(f"[FAILURE] Employee {hire_data['employee_id']} not found in hris_core.")
    else:
        print("[FAILURE] Could not retrieve employees from hris_core.")

    print("\n--- ALL TESTS COMPLETED ---")

if __name__ == "__main__":
    test_recruitment()
