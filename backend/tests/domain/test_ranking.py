from datetime import UTC, datetime

import pytest

from planner.domain.entities import (
    AssessedCheckpoint,
    Checkpoint,
    LatLng,
    RiskAssessment,
    RouteOption,
    WeatherSample,
)
from planner.domain.entities import (
    RiskLevel as R,
)
from planner.domain.ranking import rank_routes, summarize_route

NOW = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)


def make_route(route_id: str, hours: float, miles: float = 100) -> RouteOption:
    return RouteOption(route_id, (LatLng(0, 0), LatLng(0, 1)), (0, miles), (0, hours), miles, hours)


def make_cp(level: R, miles: float) -> AssessedCheckpoint:
    return AssessedCheckpoint(
        checkpoint=Checkpoint("r", 0, LatLng(0, 0), 0, miles, NOW),
        weather=WeatherSample(0, 0, 0),
        risk=RiskAssessment(level, ()),
    )


def summary(route_id: str, hours: float, **miles_per_level: float):
    cps = [make_cp(R[name.upper()], m) for name, m in miles_per_level.items()]
    return summarize_route(make_route(route_id, hours), cps)


def test_summary_totals_and_weighted_average():
    s = summary("a", 2, low=50, high=50)
    assert s.miles_by_level[R.LOW] == 50
    assert s.miles_by_level[R.HIGH] == 50
    assert s.miles_by_level[R.SEVERE] == 0
    assert s.avg_risk == pytest.approx(1.0)
    assert s.worst_level == R.HIGH


def test_fewer_severe_miles_wins_even_if_slower():
    fast = summary("fast", 2, low=80, severe=20)
    slow = summary("slow", 3, low=90, severe=10)
    assert rank_routes([fast, slow])[0].route_id == "slow"


def test_severe_tie_then_fewer_high_miles_wins():
    a = summary("a", 2, low=60, severe=10, high=30)
    b = summary("b", 3, low=80, severe=10, high=10)
    assert rank_routes([a, b])[0].route_id == "b"


def test_severe_and_high_tie_then_lower_average_wins():
    a = summary("a", 2, low=40, moderate=60)
    b = summary("b", 3, low=80, moderate=20)
    assert rank_routes([a, b])[0].route_id == "b"


def test_full_risk_tie_then_shortest_time_wins():
    a = summary("a", 3, low=100)
    b = summary("b", 2, low=100)
    assert rank_routes([a, b])[0].route_id == "b"


def test_any_no_travel_miles_ranks_below_severe():
    blocked = summary("blocked", 2, low=90, no_travel=10)
    stormy = summary("stormy", 3, low=50, severe=50)
    assert rank_routes([blocked, stormy])[0].route_id == "stormy"
