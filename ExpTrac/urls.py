from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

# ============================
# MAIN URL CONFIGURATION
# ============================

urlpatterns = [
    path('admin/', admin.site.urls),

    # GLOBAL ROUTES
    path('', include('Base.routes')),

    # APP ROUTES

    path('main/', include('main.routes')),
    path('accounts/', include('accounts.routes')),
]

# ============================
# SERVE MEDIA & STATIC IN DEVELOPMENT
# ============================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
