from rest_framework import serializers
from apartments.models import Apartment

class ApartmentSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedRelatedField(
        view_name='apartment-detail',
        lookup_field='pk',
        read_only=True
    )

    class Meta:
        model = Apartment
        fields = ['id', 'name', 'type', 'description', 'photo', 'video', 'url_obj']
        read_only_fields = ['id', 'name', 'type', 'description', 'photo', 'video']

