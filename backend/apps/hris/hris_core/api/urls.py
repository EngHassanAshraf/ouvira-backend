from django.urls import path
from .views import LocationListCreateApiView

urlpatterns = [
    path('locations/', LocationListCreateApiView.as_view(), name='location-list-create'),
]