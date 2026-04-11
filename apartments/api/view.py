from rest_framework import views, permissions, status
from rest_framework.response import Response

# logger
import logging

logger = logging.getLogger("apartments")

class APIRootView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            'apartments': '/api/apartments/',
            'schedules': '/api/schedules/',
            'auth_token': '/api/token/',
        }, status = status.HTTP_200_OK)
