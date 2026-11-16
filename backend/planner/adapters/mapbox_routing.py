import logging
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
DETOUR_FACTORS = (0.15, -0.15, 0.3, -0.3)
OVERLAP_CELL_DEGREES = 0.01
MAX_SHARED_FRACTION = 0.8
MAX_BACKTRACK_FRACTION = 0.05
BACKTRACK_MIN_GAP_MILES = 5.0

logger = logging.getLogger(__name__)


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
            except ProviderError as exc:
                logger.info("Detour attempt %.2f failed: %s", factor, exc)
                continue
            routes.extend(c for c in candidates if not _backtracks(c) and _is_distinct(c, routes))
        selected = sorted(routes[:max_routes], key=lambda r: r.duration_hours)
        return [replace(r, id=f"route-{i + 1}") for i, r in enumerate(selected)]

    def _request(
        self, points: Sequence[LatLng], alternatives: bool, max_weight_lb: float | None
    ) -> list[RouteOption]:
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


Cell = tuple[int, int]


def _cell(p: LatLng) -> Cell:
    return (round(p.lat / OVERLAP_CELL_DEGREES), round(p.lng / OVERLAP_CELL_DEGREES))


def _cells(route: RouteOption) -> set[Cell]:
    return {_cell(p) for p in route.geometry}


def _shared_fraction(candidate: RouteOption, other_cells: set[Cell]) -> float:
    """Share of the candidate's miles that run along roads in other_cells."""
    total = candidate.cumulative_miles[-1]
    if total <= 0:
        return 1.0
    shared = 0.0
    for i in range(len(candidate.geometry) - 1):
        ci, cj = _cell(candidate.geometry[i])
        near = any((ci + di, cj + dj) in other_cells for di in (-1, 0, 1) for dj in (-1, 0, 1))
        if near:
            shared += candidate.cumulative_miles[i + 1] - candidate.cumulative_miles[i]
    return shared / total


def _is_distinct(candidate: RouteOption, existing: Sequence[RouteOption]) -> bool:
    return all(_shared_fraction(candidate, _cells(r)) <= MAX_SHARED_FRACTION for r in existing)


def _backtracks(route: RouteOption) -> bool:
    """True if the route drives back over road it already used, e.g. an out-and-back spur."""
    first_seen: dict[Cell, float] = {}
    backtracked = 0.0
    for i, point in enumerate(route.geometry):
        mile = route.cumulative_miles[i]
        seen = first_seen.setdefault(_cell(point), mile)
        if i and mile - seen > BACKTRACK_MIN_GAP_MILES:
            backtracked += mile - route.cumulative_miles[i - 1]
    return backtracked > MAX_BACKTRACK_FRACTION * route.distance_miles
