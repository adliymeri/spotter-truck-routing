from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from planner import wiring
from planner.api.presenters import present_trip_plan
from planner.api.serializers import PlanRequestSerializer
from planner.application.plan_trip import plan_trip
from planner.ports import ProviderError


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
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(present_trip_plan(result))