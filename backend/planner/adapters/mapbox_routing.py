import math
from collections.abc import Iterable, Sequence
from dataclasses import replace

import httpx

from planner.domain.entities import LatLng, RouteOption
from planner.domain.geo import cumulative_miles, haversine_miles, lerp_point, locate
from planner.ports import ProviderError

METERS_PER_MILE = 1609.344
LB_PER_TONNE = 2204.62
MAX_WEIGHT_TONNES = 100
MILES_PER_DEGREE_LAT = 69.0
DETOUR_FACTORS = (0.1, -0.1, 0.2, -0.2)
MIN_DISTANCE_DIFFERENCE = 0.02


class MapboxRouting:
    def __init__(self, token: str, base_url: str, timeout_seconds: float, client: httpx.Client | None = None):
        if not token:
            raise ValueError("Mapbox token is missing")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def get_routes(
        self,
        origin: LatLng,
        destination: LatLng,
        max_routes: int = 3,
        max_weight_lb: float | None = None,
    ) -> list[RouteOption]:
        routes = self._request([origin, destination], True, max_weight_lb)
        if not routes:
            raise ProviderError("No route found")

        for factor in DETOUR_FACTORS:
            if len(routes) >= max_routes:
                break
            via = _detour_point(routes[0], origin, destination, factor)
            try:
                candidates = self._request([origin, via, destination], False, max_weight_lb)
            except ProviderError:
                continue
            routes.extend(c for c in candidates if _is_distinct(c, routes))

        selected = sorted(routes[:max_routes], key=lambda r: r.duration_hours)
        return [replace(r, id=f"route-{i + 1}") for i, r in enumerate(selected)]

    def _request(self, points: Sequence[LatLng], alternatives: bool, max_weight_lb: float | None) -> list[RouteOption]:
        coords = ";".join(f"{p.lng},{p.lat}" for p in points)
        params: dict[str, str | float] = {
            "access_token": self._token,
            "alternatives": "true" if alternatives else "false",
            "geometries": "geojson",
            "overview": "full",
            "annotations": "distance,duration",
        }
        if max_weight_lb:
            params["max_weight"] = round(min(max_weight_lb / LB_PER_TONNE, MAX_WEIGHT_TONNES), 1)

        try:
            response = self._client.get(f"{self._base_url}/{coords}", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Mapbox request failed with status {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise ProviderError(f"Mapbox request failed: {type(exc).__name__}") from None

        data = response.json()
        if data.get("code") != "Ok":
            raise ProviderError(f"Mapbox: {data.get('message') or data.get('code')}")
        return [_parse_route(route) for route in data.get("routes", [])]


def _running_sum(values: Iterable[float]) -> list[float]:
    totals = [0.0]
    for v in values:
        totals.append(totals[-1] + v)
    return totals


def _parse_route(route: dict) -> RouteOption:
    geometry = tuple(LatLng(lat, lng) for lng, lat in route["geometry"]["coordinates"])
    seg_m = [d for leg in route["legs"] for d in leg["annotation"]["distance"]]
    seg_s = [d for leg in route["legs"] for d in leg["annotation"]["duration"]]
    duration_hours = route["duration"] / 3600

    if len(seg_m) == len(geometry) - 1:
        cum_miles = _running_sum(m / METERS_PER_MILE for m in seg_m)
        cum_hours = _running_sum(s / 3600 for s in seg_s)
    else:
        cum_miles = cumulative_miles(geometry)
        total = cum_miles[-1]
        cum_hours = [m / total * duration_hours if total else 0.0 for m in cum_miles]

    return RouteOption(
        id="",
        geometry=geometry,
        cumulative_miles=tuple(cum_miles),
        cumulative_hours=tuple(cum_hours),
        distance_miles=route["distance"] / METERS_PER_MILE,
        duration_hours=duration_hours,
    )


def _detour_point(route: RouteOption, origin: LatLng, destination: LatLng, factor: float) -> LatLng:
    """Point beside the route's midpoint, perpendicular to the origin→destination line."""
    i, t = locate(route.cumulative_miles, route.cumulative_miles[-1] / 2)
    mid = lerp_point(route.geometry[i], route.geometry[i + 1], t)

    lat_scale = math.cos(math.radians(mid.lat))
    dx = (destination.lng - origin.lng) * lat_scale
    dy = destination.lat - origin.lat
    length = math.hypot(dx, dy) or 1.0
    offset_deg = factor * haversine_miles(origin, destination) / MILES_PER_DEGREE_LAT

    return LatLng(
        mid.lat + (dx / length) * offset_deg,
        mid.lng + (-dy / length) * offset_deg / lat_scale,
    )


def _is_distinct(candidate: RouteOption, existing: Sequence[RouteOption]) -> bool:
    return all(
        abs(candidate.distance_miles - r.distance_miles) / (r.distance_miles or 1) > MIN_DISTANCE_DIFFERENCE
        for r in existing
    )