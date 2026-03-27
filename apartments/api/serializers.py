from rest_framework import serializers
from apartments.models import Apartment, Schedule

class ApartmentSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='apartments-detail',
        lookup_field='pk'
    )

    class Meta:
        model = Apartment
        fields = ['id', 'name', 'type', 'description', 'url_obj']
        read_only_fields = ['id', 'name', 'type', 'description']


class ScheduleSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='schedules-detail',
        lookup_field='pk'
    )

    class Meta:
        model = Schedule
        fields = ['id', 'date', 'apartment', 'price', 'status', 'url_obj']
        read_only_fields = ['id', 'date', 'apartment', 'price', 'status']


