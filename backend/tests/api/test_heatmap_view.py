from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from planner import wiring
from planner.domain.entities import WeatherSample
from tests.fakes import FakeWeather


@pytest.fixture(autouse=True)
def fake_weather(monkeypatch):
    monkeypatch.setattr(wiring, "weather", lambda: FakeWeather(lambda p, t: WeatherSample(30, 0, 0)))


def payload(**overrides) -> dict:
    data = {
        "corridor": [{"lat": 41.0, "lng": -88.0}, {"lat": 41.0, "lng": -87.5}],
        "start": (timezone.now() + timedelta(hours=1)).isoformat(),
        "hours": 48,
        "weight_lb": 20_000,
    }
    data.update(overrides)
    return data


def test_heatmap_returns_compact_frames():
    response = APIClient().post("/api/heatmap/", payload(), format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["hours"] == 48
    assert len(body["frames"]) == 49
    assert len(body["frames"][0]) == len(body["points"])
    assert set(body["frames"][0]) == {1}  # 30 mph -> MODERATE


def test_too_many_hours_rejected():
    response = APIClient().post("/api/heatmap/", payload(hours=72), format="json")
    assert response.status_code == 400
    assert "hours" in response.json()


def test_empty_corridor_rejected():
    response = APIClient().post("/api/heatmap/", payload(corridor=[]), format="json")
    assert response.status_code == 400