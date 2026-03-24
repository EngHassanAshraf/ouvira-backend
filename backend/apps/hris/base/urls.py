# apps/hris/base/urls.py
from django.urls import path, include

urlpatterns = [
    # UZB: Core modulining URL-larini ulaymiz
    # ENG: Including Core module URLs
    path('core/', include('apps.hris.hris_core.api.urls'))
]