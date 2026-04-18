from django.urls import path
from .views import InternalLoginView, InternalLogoutView, InternalMeView

app_name = "internal_auth"

urlpatterns = [
    path("login/",  InternalLoginView.as_view(),  name="internal-login"),
    path("logout/", InternalLogoutView.as_view(), name="internal-logout"),
    path("me/",     InternalMeView.as_view(),     name="internal-me"),
]
