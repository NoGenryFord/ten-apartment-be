from rest_framework import serializers
from apartments.models import Apartments, Schedule

class ApartmentSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='apartment-detail',
        lookup_field='pk'
    )

    class Meta:
        model = Apartments
        fields = ['id', 'name', 'type', 'description', 'photo', 'video', 'url_obj']
        read_only_fields = ['id', 'name', 'type', 'description', 'photo', 'video']


