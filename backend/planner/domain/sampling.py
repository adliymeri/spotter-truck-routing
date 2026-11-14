from datetime import datetime, timedelta

from planner.domain.entities import Checkpoint, RouteOption
from planner.domain.geo import lerp_point, locate

ALLOWED_INTERVALS_MILES = (10, 25, 50)


def checkpoint_miles(total_miles: float, interval_miles: float) -> list[float]:
    if total_miles <= 0:
        return [0.0]
    marks = []
    k = 0
    while k * interval_miles < total_miles:
        marks.append(k * interval_miles)
        k += 1
    marks.append(total_miles)
    return marks


def sample_checkpoints(route: RouteOption, interval_miles: float, departure: datetime) -> list[Checkpoint]:
    """
    Each checkpoint covers the road halfway to its neighbours,
    so segment_miles sums to the route length.
    """
    if interval_miles <= 0:
        raise ValueError("interval_miles must be positive")
    if departure.tzinfo is None:
        raise ValueError("departure must be timezone-aware")
    if len(route.geometry) < 2:
        raise ValueError("route geometry needs at least two points")

    total = route.cumulative_miles[-1]
    marks = checkpoint_miles(total, interval_miles)
    checkpoints: list[Checkpoint] = []

    for idx, mile in enumerate(marks):
        lower = 0.0 if idx == 0 else (marks[idx - 1] + mile) / 2
        upper = total if idx == len(marks) - 1 else (mile + marks[idx + 1]) / 2

        i, t = locate(route.cumulative_miles, mile)
        location = lerp_point(route.geometry[i], route.geometry[i + 1], t)
        hours = route.cumulative_hours[i] + (route.cumulative_hours[i + 1] - route.cumulative_hours[i]) * t

        checkpoints.append(
            Checkpoint(
                route_id=route.id,
                index=idx,
                location=location,
                mile_marker=mile,
                segment_miles=upper - lower,
                eta=departure + timedelta(hours=hours),
            )
        )
    return checkpoints
