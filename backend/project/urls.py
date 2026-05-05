from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts.views import LogoutView, RegisterView, UserMeView

V = "api/<str:version>"


def em_breve(_request):
    html = (
        "<html><head><title>Arca Ensina</title></head>"
        "<body style='margin:0;background:#000;display:flex;"
        "flex-direction:column;justify-content:center;"
        "align-items:center;height:100vh;'>"
        "<div style='font-size:6rem;'>🏥</div>"
        "<h1 style='color:white;font-family:sans-serif;"
        "font-size:5rem;margin:0.5rem 0;'>Arca Ensina</h1>"
        "<p style='color:#aaa;font-family:sans-serif;font-size:2rem;"
        "margin:0;letter-spacing:2px;text-transform:uppercase;'>"
        "Em Breve</p></body></html>"
    )
    return HttpResponse(html, content_type="text/html")


urlpatterns = [
    path("", em_breve),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(f"{V}/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(f"{V}/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(f"{V}/auth/register/", RegisterView.as_view(), name="register"),
    path(f"{V}/auth/user/", UserMeView.as_view(), name="user_me"),
    path(f"{V}/auth/logout/", LogoutView.as_view(), name="logout"),
    path(f"{V}/", include("apps.audit.urls")),
]
