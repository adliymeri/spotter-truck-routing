from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from planner.application.build_heatmap import HeatmapRequest
from planner.application.plan_trip import TripRequest
from planner.domain.entities import LatLng
from planner.domain.sampling import ALLOWED_INTERVALS_MILES

MAX_DEPARTURE_DAYS_AHEAD = 7
DEPARTURE_PAST_TOLERANCE = timedelta(hours=1)
MAX_WEIGHT_LB = 200_000
MAX_HEATMAP_HOURS = 48
MAX_CORRIDOR_POINTS = 2000


def validate_start_time(value: datetime) -> datetime:
    now = timezone.now()
    if value < now - DEPARTURE_PAST_TOLERANCE:
        raise serializers.ValidationError("Time cannot be in the past.")
    if value > now + timedelta(days=MAX_DEPARTURE_DAYS_AHEAD):
        raise serializers.ValidationError(f"Time must be within {MAX_DEPARTURE_DAYS_AHEAD} days.")
    return value


class LatLngSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class PlanRequestSerializer(serializers.Serializer):
    origin = LatLngSerializer()
    destination = LatLngSerializer()
    departure = serializers.DateTimeField(validators=[validate_start_time])
    weight_lb = serializers.FloatField(min_value=1, max_value=MAX_WEIGHT_LB)
    interval_miles = serializers.ChoiceField(choices=ALLOWED_INTERVALS_MILES)

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


class HeatmapRequestSerializer(serializers.Serializer):
    corridor = LatLngSerializer(many=True, min_length=1, max_length=MAX_CORRIDOR_POINTS)
    start = serializers.DateTimeField(validators=[validate_start_time])
    hours = serializers.IntegerField(min_value=1, max_value=MAX_HEATMAP_HOURS, default=MAX_HEATMAP_HOURS)
    weight_lb = serializers.FloatField(min_value=1, max_value=MAX_WEIGHT_LB)

    def to_heatmap_request(self) -> HeatmapRequest:
        data = self.validated_data
        return HeatmapRequest(
            corridor=tuple(LatLng(**p) for p in data["corridor"]),
            start=data["start"],
            hours=data["hours"],
            weight_lb=data["weight_lb"],
        )

class GeocodeQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=200, trim_whitespace=True)