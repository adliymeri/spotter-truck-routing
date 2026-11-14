from dataclasses import dataclass
from datetime import datetime

from planner.domain.entities import AssessedCheckpoint, LatLng, RouteOption, RouteSummary
from planner.domain.ranking import rank_routes, summarize_route
from planner.domain.risk import assess
from planner.domain.sampling import sample_checkpoints
from planner.ports import RoutingProvider, WeatherProvider

MAX_ROUTES = 3


@dataclass(frozen=True, slots=True)
class TripRequest:
    origin: LatLng
    destination: LatLng
    departure: datetime
    weight_lb: float
    interval_miles: int


@dataclass(frozen=True, slots=True)
class RoutePlan:
    route: RouteOption
    checkpoints: tuple[AssessedCheckpoint, ...]
    summary: RouteSummary


@dataclass(frozen=True, slots=True)
class TripPlan:
    request: TripRequest
    routes: tuple[RoutePlan, ...]
    ranking: tuple[str, ...]

    @property
    def recommended_route_id(self) -> str:
        return self.ranking[0]


def plan_trip(request: TripRequest, routing: RoutingProvider, weather: WeatherProvider) -> TripPlan:
    routes = routing.get_routes(
        request.origin, request.destination, max_routes=MAX_ROUTES, max_weight_lb=request.weight_lb
    )
    checkpoints_per_route = [sample_checkpoints(r, request.interval_miles, request.departure) for r in routes]
    all_checkpoints = [cp for cps in checkpoints_per_route for cp in cps]
    samples = weather.get_samples([(cp.location, cp.eta) for cp in all_checkpoints])

    plans: list[RoutePlan] = []
    offset = 0
    for route, cps in zip(routes, checkpoints_per_route):
        route_samples = samples[offset : offset + len(cps)]
        offset += len(cps)
        assessed = tuple(
            AssessedCheckpoint(cp, sample, assess(sample, request.weight_lb))
            for cp, sample in zip(cps, route_samples)
        )
        plans.append(RoutePlan(route, assessed, summarize_route(route, assessed)))

    ranking = tuple(s.route_id for s in rank_routes([p.summary for p in plans]))
    return TripPlan(request, tuple(plans), ranking)