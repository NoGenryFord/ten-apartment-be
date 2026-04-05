from django.urls import path, include


urlpatterns = [
    # 1.0 api version
    path('api/v1/', include('apartments.api.urls')),
]
