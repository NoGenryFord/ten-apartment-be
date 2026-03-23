from rest_framework import viewsets

from apartments.api.serializers import ApartmentSerializer
from apartments.models import Apartments


class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartments.objects.all()
    serializer_class = ApartmentSerializer