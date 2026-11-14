from dataclasses import dataclass
from datetime import datetime

from planner.domain.corridor import corridor_grid
from planner.domain.entities import LatLng, RiskLevel
from planner.domain.risk import assess
from planner.ports import WeatherProvider

CORRIDOR_RADIUS_MILES = 25.0
MAX_HEATMAP_POINTS = 300


@dataclass(frozen=True, slots=True)
class HeatmapRequest:
    corridor: tuple[LatLng, ...]
    start: datetime
    hours: int
    weight_lb: float


@dataclass(frozen=True, slots=True)
class Heatmap:
    start: datetime
    spacing_miles: float
    points: tuple[LatLng, ...]
    frames: tuple[tuple[RiskLevel, ...], ...]


def build_heatmap(request: HeatmapRequest, weather: WeatherProvider) -> Heatmap:
    grid = corridor_grid(request.corridor, CORRIDOR_RADIUS_MILES, MAX_HEATMAP_POINTS)
    series = weather.get_hourly_grid(grid.points, request.start, request.hours)

    frames = tuple(
        tuple(assess(series[i][h], request.weight_lb).level for i in range(len(grid.points)))
        for h in range(request.hours + 1)
    )
    return Heatmap(request.start, grid.spacing_miles, grid.points, frames)
