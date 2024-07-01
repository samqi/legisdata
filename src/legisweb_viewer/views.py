from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from legisweb_viewer.models import Hansard, Inquiry, Person
from legisweb_viewer.serializers import (
    HansardSerializer,
    InquirySerializer,
    PersonSerializer,
)


class PersonViewSet(ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class InquiryViewSet(ReadOnlyModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer


class HansardViewSet(ReadOnlyModelViewSet):
    queryset = Hansard.objects.all()
    serializer_class = HansardSerializer