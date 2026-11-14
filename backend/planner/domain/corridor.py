import math
from collections.abc import Sequence
from dataclasses import dataclass

from planner.domain.entities import LatLng
from planner.domain.geo import haversine_miles

MILES_PER_DEGREE_LAT = 69.0
INITIAL_SPACING_MILES = 10.0
SPACING_GROWTH = 1.25


@dataclass(frozen=True, slots=True)
class CorridorGrid:
    points: tuple[LatLng, ...]
    spacing_miles: float


def corridor_grid(corridor: Sequence[LatLng], radius_miles: float, max_points: int) -> CorridorGrid:
    """Regular grid of points within radius_miles of the corridor, widened until it fits max_points."""
    if not corridor:
        raise ValueError("corridor is empty")
    if max_points < 1:
        raise ValueError("max_points must be positive")

    ref_lat = sum(p.lat for p in corridor) / len(corridor)
    lng_scale = max(math.cos(math.radians(ref_lat)), 0.01)
    spacing = INITIAL_SPACING_MILES

    while True:
        cells = _cells_within(corridor, radius_miles, spacing, lng_scale)
        if len(cells) <= max_points:
            return CorridorGrid(tuple(sorted(cells, key=lambda p: (p.lat, p.lng))), spacing)
        spacing *= SPACING_GROWTH


def _cells_within(corridor: Sequence[LatLng], radius: float, spacing: float, lng_scale: float) -> set[LatLng]:
    dlat = spacing / MILES_PER_DEGREE_LAT
    dlng = dlat / lng_scale
    reach = math.ceil(radius / spacing)
    cells: set[LatLng] = set()

    for p in corridor:
        ci, cj = round(p.lat / dlat), round(p.lng / dlng)
        for i in range(ci - reach, ci + reach + 1):
            for j in range(cj - reach, cj + reach + 1):
                cell = LatLng(round(i * dlat, 4), round(j * dlng, 4))
                if haversine_miles(p, cell) <= radius:
                    cells.add(cell)
    return cells