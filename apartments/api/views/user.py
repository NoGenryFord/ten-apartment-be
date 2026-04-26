from rest_framework import viewsets, permissions


class UserRegistrationView(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    pass


class UserProfileView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pass


class ChangePasswordView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pass


class UserBookingHistoryView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pass
