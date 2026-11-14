import math
from bisect import bisect_right
from collections.abc import Sequence
from itertools import pairwise

from planner.domain.entities import LatLng

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(a: LatLng, b: LatLng) -> float:
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlng = math.radians(b.lng - a.lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(h))


def cumulative_miles(points: Sequence[LatLng]) -> list[float]:
    totals = [0.0]
    for prev, cur in pairwise(points):
        totals.append(totals[-1] + haversine_miles(prev, cur))
    return totals


def lerp_point(a: LatLng, b: LatLng, t: float) -> LatLng:
    return LatLng(a.lat + (b.lat - a.lat) * t, a.lng + (b.lng - a.lng) * t)


def locate(xs: Sequence[float], x: float) -> tuple[int, float]:
    """Return (i, t): x lies between xs[i] and xs[i+1] at fraction t. Clamped to range."""
    if x <= xs[0]:
        return 0, 0.0
    if x >= xs[-1]:
        return len(xs) - 2, 1.0
    i = bisect_right(xs, x) - 1
    span = xs[i + 1] - xs[i]
    t = 0.0 if span == 0 else (x - xs[i]) / span
    return i, t
