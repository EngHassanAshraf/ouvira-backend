from django.urls import path

from .views import UserProfileView, UserListView, SessionTestAPIView

app_name = "account"

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="user-list"),
    # Internal / dev — restrict in production via permission class
    path("session-tests/", SessionTestAPIView.as_view(), name="session-test"),
]
