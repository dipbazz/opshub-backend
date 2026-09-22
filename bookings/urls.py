from rest_framework.routers import DefaultRouter

from bookings.views import ResourceViewSet

router = DefaultRouter()
router.register(r"resources", ResourceViewSet)

urlpatterns = router.urls
