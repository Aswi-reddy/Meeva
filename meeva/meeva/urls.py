
from django.urls import path, include
from django.contrib import admin
urlpatterns = [
    path('', include('pages.urls')),  # Include URLs from the pages app
    path('meevaadmin/', include('admin.urls')),  # Custom admin panel
]
