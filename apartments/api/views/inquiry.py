import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apartments.api.serializers import InquirySerializer
from apartments.tasks import send_inquiry_notification_task

logger = logging.getLogger("apartments")


class InquiryCreateView(APIView):
    """
    POST /api/v1/inquiries/
    Public endpoint — saves inquiry and dispatches a notification email via Celery.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = InquirySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        inquiry = serializer.save()
        send_inquiry_notification_task.delay(inquiry.id)
        logger.info("Inquiry id=%s created from contact=%s", inquiry.id, inquiry.contact)

        return Response({"id": inquiry.id}, status=status.HTTP_201_CREATED)
