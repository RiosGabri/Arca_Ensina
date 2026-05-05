from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import LogoutView, RegisterView, UserMeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/<str:version>/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/<str:version>/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/<str:version>/auth/register/', RegisterView.as_view(), name='register'),
    path('api/<str:version>/auth/user/', UserMeView.as_view(), name='user_me'),
    path('api/<str:version>/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/<str:version>/', include('audit.urls')),
]
