from rest_framework import viewsets

from apartments.api.serializers import ApartmentSerializer
from apartments.models import Apartment


class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer