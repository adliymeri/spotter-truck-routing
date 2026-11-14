from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


class RiskLevel(IntEnum):
    """Ordered so max() returns the worst level."""
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


@dataclass(frozen=True, slots=True)
class LatLng:
    lat: float
    lng: float


@dataclass(frozen=True, slots=True)
class WeatherSample:
    wind_mph: float
    rain_in_per_hr: float
    snow_in_per_hr: float


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    level: RiskLevel
    drivers: tuple[str, ...]  # which rules produced the level, e.g. ("wind", "load")


@dataclass(frozen=True, slots=True)
class RouteOption:
    """A route from the routing provider, ready for checkpoint sampling."""
    id: str
    geometry: tuple[LatLng, ...]          # the route line, as ordered points
    cumulative_miles: tuple[float, ...]   # miles from start at each geometry point
    cumulative_hours: tuple[float, ...]   # driving hours from start at each geometry point
    distance_miles: float
    duration_hours: float


@dataclass(frozen=True, slots=True)
class Checkpoint:
    route_id: str
    index: int
    location: LatLng
    mile_marker: float      # miles from the start
    segment_miles: float    # how many route miles this checkpoint represents
    eta: datetime


@dataclass(frozen=True, slots=True)
class AssessedCheckpoint:
    checkpoint: Checkpoint
    weather: WeatherSample
    risk: RiskAssessment

@dataclass(frozen=True, slots=True)
class RouteSummary:
    route_id: str
    distance_miles: float
    duration_hours: float
    miles_by_level: dict[RiskLevel, float]
    avg_risk: float
    worst_level: RiskLevel