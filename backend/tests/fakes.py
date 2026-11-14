from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from planner.domain.entities import LatLng, RouteOption, WeatherSample

WeatherFn = Callable[[LatLng, datetime], WeatherSample]


def straight_route(route_id: str, lat: float, miles: float = 100.0, hours: float = 2.0) -> RouteOption:
    return RouteOption(route_id, (LatLng(lat, 0), LatLng(lat, 1)), (0, miles), (0, hours), miles, hours)


class FakeRouting:
    def __init__(self, routes: Sequence[RouteOption]):
        self.routes = list(routes)
        self.calls: list[tuple] = []

    def get_routes(self, origin, destination, max_routes=3, max_weight_lb=None):
        self.calls.append((origin, destination, max_routes, max_weight_lb))
        return self.routes[:max_routes]


class FakeWeather:
    def __init__(self, fn: WeatherFn):
        self.fn = fn
        self.requested: list[tuple[LatLng, datetime]] = []

    def get_samples(self, points):
        self.requested.extend(points)
        return [self.fn(p, t) for p, t in points]

    def get_hourly_grid(self, points, start, hours=48):
        return [[self.fn(p, start + timedelta(hours=h)) for h in range(hours + 1)] for p in points]


class FakeGeocoder:
    def __init__(self, results: list[tuple[str, LatLng]]):
        self.results = results
        self.queries: list[str] = []

    def search(self, query: str, limit: int = 5):
        self.queries.append(query)
        return self.results[:limit]
