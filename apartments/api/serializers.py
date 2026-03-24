from rest_framework import serializers
from apartments.models import Apartment, Schedule

class ApartmentSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='apartments-detail',
        lookup_field='pk'
    )

    class Meta:
        model = Apartment
        fields = ['id', 'name', 'type', 'description', 'photo', 'video', 'url_obj']
        read_only_fields = ['id', 'name', 'type', 'description', 'photo', 'video']


