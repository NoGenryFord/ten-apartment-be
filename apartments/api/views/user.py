from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apartments.models import Booking, User
from apartments.api.serializers import UserSerializer, BookingHistorySerializer


class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my_bookings")
    def my_bookings(self, request):
        queryset = Booking.objects.filter(user=request.user).order_by("-created_at")
        serializer = BookingHistorySerializer(queryset, many=True)
        return Response(serializer.data)
