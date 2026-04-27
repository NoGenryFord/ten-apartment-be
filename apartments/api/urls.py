from django.urls import path, include
from rest_framework import routers

from rest_framework_simplejwt.views import (
TokenObtainPairView,
TokenRefreshView,
)

from .view import APIRootView
from .views import ApartmentViewSet, ScheduleViewSet, BookingViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r'apartments', ApartmentViewSet, basename='apartments')
router.register(r'schedules', ScheduleViewSet, basename='schedules')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]