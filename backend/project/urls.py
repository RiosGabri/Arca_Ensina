from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    InvitationCheckView,
    LogoutView,
    RegisterView,
    UserMeView,
)


def em_breve(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Arca Ensina - Em Breve</title>
        <style>
            body {
                background-color: #000;
                color: #fff;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            h1 {
                font-size: 3rem;
                letter-spacing: 5px;
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            p {
                font-size: 1.2rem;
                color: #888;
            }
            .logo-arca {
                color: #007bff;
            }
        </style>
    </head>
    <body>
        <h1>ARCA <span class="logo-arca">ENSINA</span></h1>
        <p>EM BREVE</p>
    </body>
    </html>
    """
    return HttpResponse(html_content)


V = "api/<str:version>"

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
    path(
        f"{V}/auth/invite/<str:token>/",
        InvitationCheckView.as_view(),
        name="invite_check",
    ),
    path(f"{V}/auth/user/", UserMeView.as_view(), name="user_me"),
    path(f"{V}/auth/logout/", LogoutView.as_view(), name="logout"),
    path(f"{V}/", include("apps.audit.urls")),
    path(f"{V}/calculator/", include("apps.calculator.urls")),
    path(f"{V}/", include("apps.pacientes.urls")),
    path(f"{V}/", include("apps.protocols.urls")),
    path(f"{V}/medications/", include("apps.medications.urls")),
]
