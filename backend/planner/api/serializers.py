from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from planner.application.plan_trip import TripRequest
from planner.domain.entities import LatLng
from planner.domain.sampling import ALLOWED_INTERVALS_MILES

MAX_DEPARTURE_DAYS_AHEAD = 7
DEPARTURE_PAST_TOLERANCE = timedelta(hours=1)
MAX_WEIGHT_LB = 200_000


class LatLngSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class PlanRequestSerializer(serializers.Serializer):
    origin = LatLngSerializer()
    destination = LatLngSerializer()
    departure = serializers.DateTimeField()
    weight_lb = serializers.FloatField(min_value=1, max_value=MAX_WEIGHT_LB)
    interval_miles = serializers.ChoiceField(choices=ALLOWED_INTERVALS_MILES)

    def validate_departure(self, value):
        now = timezone.now()
        if value < now - DEPARTURE_PAST_TOLERANCE:
            raise serializers.ValidationError("Departure cannot be in the past.")
        if value > now + timedelta(days=MAX_DEPARTURE_DAYS_AHEAD):
            raise serializers.ValidationError(f"Departure must be within {MAX_DEPARTURE_DAYS_AHEAD} days.")
        return value

    def validate(self, attrs):
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError("Origin and destination must be different.")
        return attrs

    def to_trip_request(self) -> TripRequest:
        data = self.validated_data
        return TripRequest(
            origin=LatLng(**data["origin"]),
            destination=LatLng(**data["destination"]),
            departure=data["departure"],
            weight_lb=data["weight_lb"],
            interval_miles=data["interval_miles"],
        )