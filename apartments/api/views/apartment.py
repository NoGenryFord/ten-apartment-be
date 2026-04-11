from datetime import datetime, timedelta

from django.db.models import Count, Sum, Q

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apartments.models import Apartment, Schedule
from apartments.api.serializers import ApartmentSerializer

import logging

logger = logging.getLogger("apartments")

class ApartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def search(self, request, *args, **kwargs):
        """
        Эндпоинт: /api/apartments/search/?start_date=2026-01-01&end_date=2026-01-20
        """
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        logger.debug("Apartment search requested: start_date=%s end_date=%s", start_date, end_date)

        try:
            if not start_date:
                logger.warning("Validation error: start_date is missing")
                return Response({"error": "start_date are required."},
                                status=status.HTTP_400_BAD_REQUEST)
            if not end_date:
                logger.debug("end_date is missing, using start_date as end_date")
                end_date = start_date
            try:
                logger.debug("Start date is %s", start_date)
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                logger.debug("End date is %s", end_date)
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            except:
                logger.warning("Validation error: invalid date format start=%s end=%s", start_date, end_date)
                return Response({"error": "start_date and end_date are not valid. Use YYYY-MM-DD format"},
                                status=status.HTTP_400_BAD_REQUEST)

            if end_date == start_date:
                end_date += timedelta(days=1)
                logger.debug("end_date is the same as start_date, adjusted end_date to %s", end_date)

            night_needed = (end_date - start_date).days
            actual_end_date = end_date - timedelta(days=1)
            logger.debug("Actual end date is %s", actual_end_date)

            if night_needed < 0:
                logger.warning("Validation error: night_needed is negative")
                return Response({"error": "night_needed must be greater than 0"},
                                status=status.HTTP_400_BAD_REQUEST)


            """
            Поиск в БД по фильтру: Квартира должна иметь статус AVAILABLE на все ночи в запрошенном диапазоне дат.
            """
            available_apartments = Apartment.objects.filter(
                schedule__date__range=[start_date, actual_end_date],
                schedule__status=Schedule.Status.AVAILABLE
            ).annotate(
                available_nights=Count('schedule', filter=Q(
                    schedule__status=Schedule.Status.AVAILABLE,
                    schedule__date__range=[start_date, actual_end_date]
                )),
                total_price=Sum('schedule__price__price', filter=Q(
                    schedule__status=Schedule.Status.AVAILABLE,
                    schedule__date__range=[start_date, actual_end_date]
                ))
            ).filter(
                available_nights=night_needed
            )
            serializer = self.get_serializer(available_apartments, many=True)

            logger.info(f"Found {len(available_apartments)} available apartments for the given date range.")
            return Response(serializer.data)
        except Exception:
            logger.exception("Unexpected error in ApartmentViewSet.search")
            raise