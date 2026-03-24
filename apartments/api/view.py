from rest_framework import viewsets

from apartments.api.serializers import ApartmentSerializer, ScheduleSerializer
from apartments.models import Apartment, Schedule


class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer