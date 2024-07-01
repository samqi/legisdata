from django.urls import include, path
from rest_framework.routers import DefaultRouter

from legisweb_viewer import views

router = DefaultRouter()
router.register(r"person", views.PersonViewSet, basename="person")
router.register(r"inquiry", views.InquiryViewSet, basename="inquiry")
router.register(r"hansard", views.HansardViewSet, basename="hansard")

urlpatterns = [
    path("", include(router.urls)),
]