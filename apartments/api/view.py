from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from apartments.api.serializers import ApartmentSerializer, ScheduleSerializer
from apartments.models import Apartment, Schedule


class ApartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Эндпоинт: /api/apartments/search/?start_date=2026-01-01&end_date=2026-01-20
        """
        pass


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Календарь для конкретной квартиры
        /api/schedules/?apartment_id=1
        """
        queryset = super().get_queryset()
        apartment_id = self.request.query_params.get('apartment_id')
        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)
        return queryset