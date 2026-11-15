from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from planner import wiring
from planner.domain.entities import WeatherSample
from planner.ports import ProviderError
from tests.fakes import FakeRouting, FakeWeather, straight_route


def payload(**overrides) -> dict:
    data = {
        "origin": {"lat": 41.88, "lng": -87.63},
        "destination": {"lat": 39.10, "lng": -84.51},
        "departure": (timezone.now() + timedelta(hours=1)).isoformat(),
        "weight_lb": 40_000,
        "interval_miles": 25,
    }
    data.update(overrides)
    return data


@pytest.fixture
def fakes(monkeypatch):
    routing = FakeRouting(
        [straight_route("route-1", lat=0.0, hours=2), straight_route("route-2", lat=1.0, hours=3)]
    )
    weather = FakeWeather(lambda p, t: WeatherSample(50 if p.lat < 0.5 else 5, 0, 0))
    monkeypatch.setattr(wiring, "routing", lambda: routing)
    monkeypatch.setattr(wiring, "weather", lambda: weather)


def post(data: dict):
    return APIClient().post("/api/plan/", data, format="json")


def test_plan_returns_routes_and_recommendation(fakes):
    response = post(payload())
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_route_id"] == "route-2"
    route_1 = next(r for r in body["routes"] if r["id"] == "route-1")
    assert route_1["checkpoints"][0]["risk_level"] == "NO_TRAVEL"
    assert "load" in route_1["checkpoints"][0]["risk_drivers"]
    assert route_1["summary"]["worst_level"] == "NO_TRAVEL"


def test_invalid_interval_rejected(fakes):
    response = post(payload(interval_miles=30))
    assert response.status_code == 400
    assert "interval_miles" in response.json()


def test_past_departure_rejected(fakes):
    response = post(payload(departure=(timezone.now() - timedelta(days=1)).isoformat()))
    assert response.status_code == 400
    assert "departure" in response.json()


def test_provider_failure_returns_502(monkeypatch):
    class BrokenRouting:
        def get_routes(self, *args, **kwargs):
            raise ProviderError("Mapbox unavailable")

    monkeypatch.setattr(wiring, "routing", lambda: BrokenRouting())
    monkeypatch.setattr(wiring, "weather", lambda: FakeWeather(lambda p, t: WeatherSample(0, 0, 0)))
    response = post(payload())
    assert response.status_code == 502
    assert response.json()["detail"] == "Mapbox unavailable"


def test_unexpected_error_returns_json_500(monkeypatch):
    class ExplodingRouting:
        def get_routes(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(wiring, "routing", lambda: ExplodingRouting())
    monkeypatch.setattr(wiring, "weather", lambda: FakeWeather(lambda p, t: WeatherSample(0, 0, 0)))
    response = post(payload())
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
