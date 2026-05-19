from rest_framework.routers import DefaultRouter

from .views import ProtocolExecutionViewSet, ProtocolVersionViewSet, ProtocolViewSet

router = DefaultRouter()
router.register(r"protocols", ProtocolViewSet, basename="protocol")
router.register(
    r"protocol-versions", ProtocolVersionViewSet, basename="protocol-version"
)
router.register(
    r"protocol-executions",
    ProtocolExecutionViewSet,
    basename="protocol-execution",
)


urlpatterns = router.urls
