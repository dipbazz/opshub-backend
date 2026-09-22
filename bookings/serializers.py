from rest_framework import serializers

from bookings.models import Booking, Resource


class ResourceSerializer(serializers.ModelSerializer[Resource]):
    capacity = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = Resource
        fields = ["id", "tenant", "name", "description", "capacity"]
        read_only_fields = ["tenant"]


class BookingSerializer(serializers.ModelSerializer[Booking]):
    class Meta:
        model = Booking
        fields = [
            "id",
            "tenant",
            "resource",
            "created_by",
            "start_time",
            "end_time",
            "status",
            "get_status_display",
        ]
        read_only_fields = ["tenant", "created_by", "status"]
