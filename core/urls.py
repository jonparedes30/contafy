from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
try:
    from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )
except Exception:
    # fallback dummy views if simplejwt is not installed (development envs)
    TokenObtainPairView = None
    TokenRefreshView = None
from django.conf import settings
from django.conf.urls.static import static
from empresa.views.health import health_check

urlpatterns = [
    path('', lambda request: redirect('empresa:home')),
    path('admin/', admin.site.urls),
    # Incluir con namespace para permitir reverses como 'empresa:home' y 'empresa:dashboard_manufactura'
    path('app-beta-2024/', include(('empresa.urls', 'empresa'), namespace='empresa')),  # URL secreta
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('health/', health_check, name='health_check'),
    # JWT token endpoints (only if simplejwt is available)
    *( [
        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ] if TokenObtainPairView and TokenRefreshView else [
        # Provide simple 501 placeholders so imports succeed in dev without JWT package
        path('api/token/', lambda request: (_ for _ in ()).throw(Exception('JWT not installed')), name='token_obtain_pair'),
        path('api/token/refresh/', lambda request: (_ for _ in ()).throw(Exception('JWT not installed')), name='token_refresh'),
    ] ),
    path('api/academia/', include('empresa.api.urls')),
]
