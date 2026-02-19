from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('pages.urls')),  # Include URLs from the pages app
    path('meevaadmin/', include('admin.urls')),  # Custom admin panel
    path('vendor/', include('vendor.urls')),  # Vendor panel
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
