from datetime import UTC, datetime, timedelta

import pytest

from planner.application.plan_trip import TripRequest, plan_trip
from planner.domain.entities import LatLng, RiskLevel, WeatherSample
from tests.fakes import FakeRouting, FakeWeather, straight_route

DEPARTURE = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)


def request(weight_lb: float = 20_000, interval: int = 25) -> TripRequest:
    return TripRequest(LatLng(0, 0), LatLng(0, 1), DEPARTURE, weight_lb, interval)


def windy_south(p: LatLng, t: datetime) -> WeatherSample:
    return WeatherSample(40 if p.lat < 0.5 else 5, 0, 0)


def test_safer_route_recommended_even_if_slower():
    routing = FakeRouting(
        [straight_route("fast", lat=0.0, hours=2), straight_route("safe", lat=1.0, hours=3)]
    )
    plan = plan_trip(request(), routing, FakeWeather(windy_south))

    assert plan.recommended_route_id == "safe"
    assert plan.ranking == ("safe", "fast")
    fast = next(p for p in plan.routes if p.route.id == "fast")
    assert all(c.risk.level == RiskLevel.HIGH for c in fast.checkpoints)
    assert fast.summary.miles_by_level[RiskLevel.HIGH] == pytest.approx(100)


def test_weather_requested_at_checkpoint_etas():
    weather = FakeWeather(windy_south)
    plan_trip(request(interval=50), FakeRouting([straight_route("r", lat=1.0, hours=2)]), weather)
    assert [t for _, t in weather.requested] == [
        DEPARTURE,
        DEPARTURE + timedelta(hours=1),
        DEPARTURE + timedelta(hours=2),
    ]


def test_weight_passed_to_routing():
    routing = FakeRouting([straight_route("r", lat=1.0)])
    plan_trip(request(weight_lb=35_000), routing, FakeWeather(windy_south))
    assert routing.calls[0][3] == 35_000
