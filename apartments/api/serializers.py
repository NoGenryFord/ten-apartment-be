from rest_framework import serializers
from apartments.models import Apartment, Schedule, ApartmentPhoto, ApartmentVideo, ApartmentType

class ApartmentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentPhoto
        fields = ['id', 'photo', 'updated_at']


class ApartmentVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentVideo
        fields = ['id', 'video', 'updated_at']

class ApartmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentType
        fields = ['id', 'name']

class ApartmentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Квартира. Включает в себя связанные фото, видео и тип квартиры.\n
    Атрибуты:
    url_obj - для получения URL объекта, для удобства навигации в API. Например: /api/apartments/n/ \n
    photos - используются только в detail просмотре объекта
    videos - используются только в detail просмотре объекта
    types - тип апартаментов, ссылка на модель типов апартаментов
    total_price - Не обязательное поле, заполняется только в случае поиска по датам

    """
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='apartments-detail',
        lookup_field='pk'
    )

    photos = ApartmentPhotoSerializer(many=True, read_only=True)
    videos = ApartmentVideoSerializer(many=True, read_only=True)
    type = ApartmentTypeSerializer(read_only=True)


    # Не обязательное поле, заполняется только в случае поиска по датам
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, required=False)

    class Meta:
        model = Apartment
        fields = ['id', 'name', 'type', 'description', 'photos', 'videos', 'total_price', 'url_obj']


class ScheduleSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name='schedules-detail',
        lookup_field='pk'
    )

    price_value = serializers.DecimalField(source='price.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'date', 'apartment', 'price_value', 'status', 'url_obj']


