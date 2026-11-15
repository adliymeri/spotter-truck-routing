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


def _perpendicular_distance(p: LatLng, a: LatLng, b: LatLng) -> float:
    dx, dy = b.lng - a.lng, b.lat - a.lat
    if dx == 0 and dy == 0:
        return math.hypot(p.lng - a.lng, p.lat - a.lat)
    return abs(dy * p.lng - dx * p.lat + b.lng * a.lat - b.lat * a.lng) / math.hypot(dx, dy)


def simplify(points: Sequence[LatLng], tolerance_deg: float) -> list[LatLng]:
    """Douglas–Peucker: drop points that lie within tolerance of the simplified line."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        max_dist, index = 0.0, -1
        for i in range(start + 1, end):
            d = _perpendicular_distance(points[i], points[start], points[end])
            if d > max_dist:
                max_dist, index = d, i
        if max_dist > tolerance_deg:
            keep[index] = True
            stack.extend([(start, index), (index, end)])
    return [p for p, k in zip(points, keep, strict=True) if k]
