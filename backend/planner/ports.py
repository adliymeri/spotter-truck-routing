from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from planner.domain.entities import LatLng, RouteOption, WeatherSample


class ProviderError(Exception):
    """An external service failed or could not answer the request."""


class RoutingProvider(Protocol):
    def get_routes(
        self,
        origin: LatLng,
        destination: LatLng,
        max_routes: int = 3,
        max_weight_lb: float | None = None,
    ) -> list[RouteOption]: ...


class WeatherProvider(Protocol):
    def get_samples(self, points: Sequence[tuple[LatLng, datetime]]) -> list[WeatherSample]: ...

    def get_hourly_grid(
        self, points: Sequence[LatLng], start: datetime, hours: int = 48
    ) -> list[list[WeatherSample]]: ...


class Geocoder(Protocol):
    def search(self, query: str, limit: int = 5) -> list[tuple[str, LatLng]]: ...