from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from planner import wiring
from planner.api.presenters import present_heatmap, present_trip_plan
from planner.api.serializers import GeocodeQuerySerializer, HeatmapRequestSerializer, PlanRequestSerializer
from planner.application.build_heatmap import build_heatmap
from planner.application.plan_trip import plan_trip
from planner.ports import ProviderError


def _provider_error(exc: ProviderError) -> Response:
    return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
def plan(request):
    serializer = PlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = plan_trip(serializer.to_trip_request(), routing=wiring.routing(), weather=wiring.weather())
    except ProviderError as exc:
        return _provider_error(exc)
    return Response(present_trip_plan(result))


@api_view(["POST"])
def heatmap(request):
    serializer = HeatmapRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = build_heatmap(serializer.to_heatmap_request(), weather=wiring.weather())
    except ProviderError as exc:
        return _provider_error(exc)
    return Response(present_heatmap(result))


@api_view(["GET"])
def geocode(request):
    serializer = GeocodeQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    try:
        results = wiring.geocoder().search(serializer.validated_data["q"])
    except ProviderError as exc:
        return _provider_error(exc)
    return Response({"results": [{"label": label, "lat": p.lat, "lng": p.lng} for label, p in results]})
