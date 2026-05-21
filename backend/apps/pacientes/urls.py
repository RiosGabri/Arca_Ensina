from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PacienteViewSet, SintomaViewSet

router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet, basename="paciente")
router.register(r"symptoms", SintomaViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
