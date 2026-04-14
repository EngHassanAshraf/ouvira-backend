# Ouvira Recruitment — Demo Testing Flow

> **Caveman guide.** Follow steps in order. Each step feeds IDs into next.
> Pre-req: server running on `localhost:8000`, collection + environment imported.

---

## SETUP (do once before demo)

1. Import `Ouvira_ERP_API.postman_collection.json`
2. Import `Ouvira_ERP.postman_environment.json`
3. Select environment **Ouvira ERP**
4. Verify `base_url = http://localhost:8000`, `tenant = shawahid`

---

## PHASE 0 — Auth (2 min)

| # | Folder | Request | What to show |
|---|--------|---------|--------------|
| 1 | Auth | **Login** | Send → 200, `access_token` auto-saved in env vars |
| 2 | Account | **Get My Profile** | `user_id` auto-saved |
| 3 | Company | **List Companies** | `company_id` auto-saved |

> **Talking point:** Token auto-saved by test script — all subsequent requests use `{{access_token}}` automatically.

---

## PHASE 1 — Hiring Request Workflow (5 min)

### 1.1 Basic CRUD
| # | Request | What to show |
|---|---------|--------------|
| 4 | **Create Hiring Request** | 201, `hiring_request_id` saved |
| 5 | **Get Hiring Request** | Full object, status = `draft` |
| 6 | **Update Hiring Request (draft only)** | PATCH vacancies → 200 |

### 1.2 Approval Workflow
| # | Request | What to show |
|---|---------|--------------|
| 7 | **Submit Hiring Request** | status → `submitted` |
| 8 | **Approve Hiring Request** | body: `role_type: "hr_employee"` → status → `approved` |

### 1.3 GAP-01 — Approval Flow Timeline ⭐
| # | Request | What to show |
|---|---------|--------------|
| 9 | **Approval Flow Timeline (GAP-01)** | Array of approval steps with timestamps, approver names, status badges |

> **Talking point:** Full chain visible — who approved, when, what role. Was missing before.

### 1.4 GAP-02 — Bulk Actions ⭐
| # | Request | What to show |
|---|---------|--------------|
| 10 | **Create Hiring Request** × 2 more | Get IDs 2 and 3 |
| 11 | **Bulk Approve Hiring Requests (GAP-02)** | body: `ids: [2,3]` → `success: [2,3]`, `failed: []` |
| 12 | **Bulk Delete Hiring Requests (GAP-02)** | body: `ids: [2,3]` → bulk soft-delete |

### 1.5 GAP-10 — Multi-field Filtering ⭐
| # | Request | What to show |
|---|---------|--------------|
| 13 | **List Hiring Requests — Filtered** | `?status=submitted&department=1` → filtered results |

---

## PHASE 2 — Job Advertisement Workflow (3 min)

| # | Request | What to show |
|---|---------|--------------|
| 14 | **Create Job Advertisement** | 201, `job_ad_id` saved |
| 15 | **Publish Job Advertisement** | status → `published` |
| 16 | **List Job Advertisements — Filtered** | `?status=published&city=cairo&platforms=linkedin` |
| 17 | **Bulk Close Job Advertisements (GAP-02)** | body: `ids: [job_ad_id]` → closed |
| 18 | **Reopen Job Advertisement** | status → `draft` again |

---

## PHASE 3 — Candidates & Applications (5 min)

### 3.1 Candidate
| # | Request | What to show |
|---|---------|--------------|
| 19 | **Create Candidate** | 201, `candidate_id` saved |

### 3.2 Application + new `job_board` field (GAP-06) ⭐
| # | Request | What to show |
|---|---------|--------------|
| 20 | **Create Application** | body includes `"job_board": "linkedin"` → 201 |
| 21 | **List Applications — Filtered (GAP-10)** | `?job_board=linkedin&classification=none` |

### 3.3 GAP-03 — Import CVs ⭐
| # | Request | What to show |
|---|---------|--------------|
| 22 | **Import CVs from Excel/CSV (GAP-03)** | Upload sample `.xlsx` → response: `added`, `shortlist_1`, `shortlist_2`, `rejected`, `errors[]` |

> **Talking point:** Bulk onboard candidates from spreadsheet. Per-row error reporting.

### 3.4 GAP-04 — Sync from Job Boards ⭐
| # | Request | What to show |
|---|---------|--------------|
| 23 | **Sync from Job Boards (GAP-04)** | body: `platforms: ["linkedin","bayt"]` → `synced: 12`, `skipped_duplicates: 3` |

### 3.5 Pipeline + Bulk Edit
| # | Request | What to show |
|---|---------|--------------|
| 24 | **Move to Stage** | `status: "phone_screening"` |
| 25 | **Bulk Edit Applications (GAP-02)** | `ids: [1,2,3], classification: "shortlist_1"` |

---

## PHASE 4 — Interviews + Scoring (3 min)

| # | Request | What to show |
|---|---------|--------------|
| 26 | **Schedule Interview** | `interview_type: "phone"`, `interview_id` saved |
| 27 | **Record Phone Interview Result (GAP-07 + GAP-13)** ⭐ | body: `scoring_data: [{interviewer_id,score,note}]`, `call_status: "suitable"` → `average_score` auto-computed |
| 28 | **Schedule Personal Interview** | `interview_type: "personal"`, 2 interviewers |
| 29 | **Record Personal Interview Result (GAP-13)** ⭐ | 2 interviewers scored → `average_score` = mean |

> **Talking point:** Per-interviewer scoring. Average auto-computed. `call_status` for phone screens.

---

## PHASE 5 — Documents (1 min)

| # | Request | What to show |
|---|---------|--------------|
| 30 | **Upload Document** | `doc_type: "id_copy"` |
| 31 | **Upload Birth Certificate (GAP-09)** ⭐ | `doc_type: "birth_certificate"` — new type |
| 32 | **Verify Document** | `status: "approved"` |

---

## PHASE 6 — Job Offer (2 min)

| # | Request | What to show |
|---|---------|--------------|
| 33 | **Create Job Offer (GAP-08)** ⭐ | body includes `"offer_validity_date": "2026-06-15"` — new field |
| 34 | **Accept Offer** | Creates employee record in hris_core |

---

## PHASE 7 — Onboarding (1 min)

| # | Request | What to show |
|---|---------|--------------|
| 35 | **Create Onboarding (GAP-11)** ⭐ | body: `session_date`, `session_location`, `assigned_mentor`, `attended`, `engagement_level: 4`, `survey_link`, `survey_responses` |
| 36 | **Update Onboarding** | PATCH `engagement_level: 5`, `survey_responses: {...}` |

> **Talking point:** Replaced free-form JSON blob with structured fields.

---

## PHASE 8 — Post-Probation Workflow (3 min)

| # | Request | What to show |
|---|---------|--------------|
| 37 | **Create Post-Probation Evaluation** | scores 1–5, `average_score` auto-computed, `workflow_status: "draft"` |
| 38 | **Submit to Manager** | status → `submitted_to_manager` |
| 39 | **Manager Approve** | note → status → `manager_approved` |
| 40 | **HR Confirm** | note → status → `hr_confirmed` |
| 41 | **Record Final Decision** | `decision: "confirmed"`, `rationale` → status → `final_decision` |

> **Talking point:** Full 4-step approval chain. Each step locked until previous completes.

---

## PHASE 9 — Audit Logs (2 min)

| # | Request | What to show |
|---|---------|--------------|
| 42 | **Hiring Request Audit Log** | All actions on hiring requests — who, what, when |
| 43 | **Hiring Request Audit Log — Filtered** | `?action_type=approved&from_date=2026-01-01` |
| 44 | **Job Advertisement Audit Log** | Scoped to job ads |
| 45 | **Application Audit Log** | Scoped to applications |

> **Talking point:** Per-entity audit trail. Filterable. Paginated. Compliance-ready.

---

## SUMMARY TABLE — All 13 Gaps Demonstrated

| GAP | Feature | Step(s) |
|-----|---------|---------|
| GAP-01 | Approval flow timeline | 9 |
| GAP-02 | Bulk actions | 11–12, 17, 25 |
| GAP-03 | Import CVs | 22 |
| GAP-04 | Sync from job boards | 23 |
| GAP-05 | Audit log endpoints | 42–45 |
| GAP-06 | `job_board` field | 20–21 |
| GAP-07 | `call_status` on interview | 27 |
| GAP-08 | `offer_validity_date` | 33 |
| GAP-09 | `birth_certificate` doc type | 31 |
| GAP-10 | Multi-field filtering | 13, 16, 21 |
| GAP-11 | Structured onboarding | 35–36 |
| GAP-12 | Post-probation workflow | 37–41 |
| GAP-13 | Per-interviewer scoring | 27–29 |

---

## TIPS

- **IDs auto-save** via test scripts — no manual copy-paste needed
- If a step fails with 400, check the previous step ran and saved its ID
- For Import CVs (step 22), prepare a sample `candidates.xlsx` with columns: `first_name`, `last_name`, `email`, `phone` (optional: `classification`, `linkedin_url`)
- Total demo time: ~25 min
