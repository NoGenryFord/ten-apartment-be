from rest_framework import viewsets, permissions

from apartments.models import Schedule
from apartments.api.serializers import ScheduleSerializer

import logging

logger = logging.getLogger("apartments")


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Календарь для конкретной квартиры
        /api/schedules/?apartments_id=1
        """
        queryset = super().get_queryset()
        apartment_id = self.request.query_params.get('apartment_id')
        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)
        return queryset