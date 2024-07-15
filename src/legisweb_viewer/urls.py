from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from legisweb_viewer import views

router = DefaultRouter()
router.register(r"person", views.PersonViewSet, basename="person")
router.register(r"inquiry", views.InquiryViewSet, basename="inquiry")
router.register(r"hansard", views.HansardViewSet, basename="hansard")

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns = format_suffix_patterns([path("search", views.search)]) + urlpatterns