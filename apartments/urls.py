from django.urls import path, include


urlpatterns = [
    path('api/', include('apartments.api.urls')),
]
