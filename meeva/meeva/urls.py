
from django.urls import path, include

urlpatterns = [
    path('meevaadmin/', include('admin.urls')),  # Custom admin panel
]
