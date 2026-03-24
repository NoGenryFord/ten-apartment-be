from django.urls import path, include
from rest_framework import routers

from rest_framework_simplejwt.views import (
TokenObtainPairView,
TokenRefreshView,
)

from .view import ApartmentViewSet, ScheduleViewSet

router = routers.DefaultRouter()
router.register(r'apartments', ApartmentViewSet, basename='apartments')
router.register(r'schedules', ScheduleViewSet, basename='schedules')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]