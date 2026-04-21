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
        EN:
        Calendar for a specific apartment.
        Supports both query params for compatibility:
        - /api/schedules/?apartment_id=1
        - /api/schedules/?apartment=1 (legacy)

        RU:
        Календарь для конкретной квартиры.
        Поддерживаются оба query-параметра для совместимости:
        - /api/schedules/?apartment_id=1
        - /api/schedules/?apartment=1 (legacy)
        """
        queryset = super().get_queryset()
        apartment_id = self.request.query_params.get(
            "apartment_id"
        ) or self.request.query_params.get("apartment")
        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)
        return queryset
