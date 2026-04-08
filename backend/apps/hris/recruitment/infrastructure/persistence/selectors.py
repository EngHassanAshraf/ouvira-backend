"""
selectors.py — Persistence Layer
---------------------------------
Centralises complex, reusable QuerySets for the Recruitment module.

Rules:
  - NO business logic here — only data retrieval.
  - ViewSets call these selectors instead of building querysets inline.
  - Services call these selectors when they need rich, pre-fetched objects.
"""

from ...models import (
    HiringRequest,
    JobAdvertisement,
    Candidate,
    JobApplication,
    Interview,
    CandidateDocument,
    JobOffer,
)


# ─── Hiring Request ────────────────────────────────────────────────────────────

def get_hiring_requests_for_company(company_id):
    return (
        HiringRequest.objects.filter(company_id=company_id)
        .select_related("job_title", "department", "created_by")
        .prefetch_related("approvals")
        .order_by("-created_at")
    )


def get_hiring_request_by_id(request_id):
    return (
        HiringRequest.objects.select_related("job_title", "department", "created_by")
        .prefetch_related("approvals")
        .get(id=request_id)
    )


# ─── Job Advertisement ─────────────────────────────────────────────────────────

def get_advertisements_for_company(company_id, status=None):
    qs = JobAdvertisement.objects.filter(
        hiring_request__company_id=company_id
    ).select_related("hiring_request__job_title", "hiring_request__department")
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-created_at")


# ─── Candidate ─────────────────────────────────────────────────────────────────

def get_candidates_for_company(company_id, search=None):
    qs = Candidate.objects.filter(company_id=company_id)
    if search:
        qs = qs.filter(
            first_name__icontains=search
        ) | qs.filter(last_name__icontains=search) | qs.filter(email__icontains=search)
    return qs.order_by("last_name", "first_name")


# ─── Job Application (Pipeline / Kanban) ───────────────────────────────────────

def get_applications_for_advertisement(advertisement_id):
    """Returns all applications for a single job ad — used for the Kanban board."""
    return (
        JobApplication.objects.filter(job_advertisement_id=advertisement_id)
        .select_related("candidate", "job_advertisement")
        .order_by("-applied_at")
    )


def get_applications_for_company(company_id, status=None):
    qs = JobApplication.objects.filter(
        candidate__company_id=company_id
    ).select_related("candidate", "job_advertisement")
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-applied_at")


# ─── Interview ─────────────────────────────────────────────────────────────────

def get_interviews_for_application(application_id):
    return (
        Interview.objects.filter(application_id=application_id)
        .select_related("application__candidate")
        .prefetch_related("interviewers")
        .order_by("interview_date")
    )


# ─── Candidate Documents ───────────────────────────────────────────────────────

def get_documents_for_candidate(candidate_id):
    return CandidateDocument.objects.filter(candidate_id=candidate_id).order_by("doc_type")


# ─── Job Offer ─────────────────────────────────────────────────────────────────

def get_offers_for_company(company_id):
    return (
        JobOffer.objects.filter(application__candidate__company_id=company_id)
        .select_related("application__candidate", "application__job_advertisement")
        .order_by("-created_at")
    )
