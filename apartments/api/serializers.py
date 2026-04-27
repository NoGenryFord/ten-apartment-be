from rest_framework import serializers
from apartments.models import (
    Apartment,
    Schedule,
    ApartmentPhoto,
    ApartmentVideo,
    ApartmentType,
    Tag,
    Booking,
    User,
)


class ApartmentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentPhoto
        fields = ["id", "photo", "updated_at"]


class ApartmentVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentVideo
        fields = ["id", "video", "updated_at"]


class ApartmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentType
        fields = ["id", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


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
        view_name="apartments-detail", lookup_field="pk"
    )

    photos = ApartmentPhotoSerializer(many=True, read_only=True)
    videos = ApartmentVideoSerializer(many=True, read_only=True)
    type = ApartmentTypeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Не обязательное поле, заполняется только в случае поиска по датам
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, required=False
    )

    today_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Apartment
        fields = [
            "id",
            "name",
            "type",
            "description",
            "photos",
            "videos",
            "tags",
            "total_price",
            "today_price",
            "max_guests",
            "address",
            "latitude",
            "longitude",
            "url_obj",
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name="schedules-detail", lookup_field="pk"
    )

    price_value = serializers.DecimalField(
        source="price.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Schedule
        fields = ["id", "date", "apartment", "price_value", "status", "url_obj"]


class BookingSerializer(serializers.ModelSerializer):
    url_obj = serializers.HyperlinkedIdentityField(
        view_name="bookings-detail", lookup_field="pk"
    )

    class Meta:
        model = Booking
        fields = [
            "user",
            "email",
            "total_price",
            "status",
            "reserved_until",
            "created_at",
            "paid",
            "url_obj",
        ]


class CreateBookingSerializer(serializers.Serializer):
    apartment_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data["start_date"] >= data["end_date"]:
            raise serializers.ValidationError(
                {"dates": "Check in date must be before end date"}
            )
        return data


class StartPaymentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)


class PaymentResultSerializer(serializers.ModelSerializer):
    result = serializers.ChoiceField(choices=["success", "failed"])

    class Meta:
        model = Booking
        fields = ["result"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone"]
        read_only_fields = ["id", "username", "email"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(
        write_only=True, required=True, min_length=8
    )

    def validate_email(self, value):
        pass


class ChangePasswordViewSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)

    def validate_new_password_confirm(self, value):
        if value != self.initial_data.get("new_password"):
            raise serializers.ValidationError(
                "New password and confirmation do not match."
            )
        return value

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                "New password and confirmation do not match."
            )
        return data
