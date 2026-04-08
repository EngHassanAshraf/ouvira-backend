from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    HiringRequestViewSet,
    JobAdvertisementViewSet,
    CandidateViewSet,
    JobApplicationViewSet,
    InterviewViewSet,
    CandidateDocumentViewSet,
    JobOfferViewSet,
    OnboardingViewSet,
)

app_name = "recruitment"

router = DefaultRouter()
router.register(r"hiring-requests", HiringRequestViewSet, basename="hiring-request")
router.register(r"job-advertisements", JobAdvertisementViewSet, basename="job-advertisement")
router.register(r"candidates", CandidateViewSet, basename="candidate")
router.register(r"applications", JobApplicationViewSet, basename="application")
router.register(r"interviews", InterviewViewSet, basename="interview")
router.register(r"documents", CandidateDocumentViewSet, basename="document")
router.register(r"offers", JobOfferViewSet, basename="offer")
router.register(r"onboarding", OnboardingViewSet, basename="onboarding")

urlpatterns = [
    path("", include(router.urls)),
]
