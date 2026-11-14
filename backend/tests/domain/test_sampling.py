from datetime import UTC, datetime, timedelta

import pytest

from planner.domain.entities import LatLng, RouteOption
from planner.domain.sampling import checkpoint_miles, sample_checkpoints

DEPARTURE = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)

ROUTE = RouteOption(
    id="r1",
    geometry=(LatLng(0, 0), LatLng(0, 1), LatLng(0, 2)),
    cumulative_miles=(0, 60, 120),
    cumulative_hours=(0, 1, 3),
    distance_miles=120,
    duration_hours=3,
)


@pytest.mark.parametrize(
    "total,interval,expected",
    [
        (120, 50, [0, 50, 100, 120]),
        (100, 50, [0, 50, 100]),
        (30, 50, [0, 30]),
        (0, 10, [0.0]),
    ],
)
def test_checkpoint_miles(total, interval, expected):
    assert checkpoint_miles(total, interval) == expected


def test_checkpoints_cover_the_whole_route():
    cps = sample_checkpoints(ROUTE, 25, DEPARTURE)
    assert [c.mile_marker for c in cps] == [0, 25, 50, 75, 100, 120]
    assert sum(c.segment_miles for c in cps) == pytest.approx(120)
    assert cps[0].segment_miles == pytest.approx(12.5)
    assert cps[-1].segment_miles == pytest.approx(10)


def test_eta_uses_route_timing():
    cps = {c.mile_marker: c for c in sample_checkpoints(ROUTE, 25, DEPARTURE)}
    assert cps[0].eta == DEPARTURE
    assert cps[25].eta == DEPARTURE + timedelta(hours=25 / 60)
    assert cps[75].eta == DEPARTURE + timedelta(hours=1.5)
    assert cps[120].eta == DEPARTURE + timedelta(hours=3)


def test_checkpoint_location_is_interpolated():
    at_75 = next(c for c in sample_checkpoints(ROUTE, 25, DEPARTURE) if c.mile_marker == 75)
    assert at_75.location.lat == pytest.approx(0)
    assert at_75.location.lng == pytest.approx(1.25)


def test_naive_departure_is_rejected():
    with pytest.raises(ValueError):
        sample_checkpoints(ROUTE, 25, datetime(2026, 11, 20, 8, 0))
