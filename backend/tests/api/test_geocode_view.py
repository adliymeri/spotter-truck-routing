import pytest
from rest_framework.test import APIClient

from planner import wiring
from planner.domain.entities import LatLng
from tests.fakes import FakeGeocoder


@pytest.fixture(autouse=True)
def fake_geocoder(monkeypatch):
    geocoder = FakeGeocoder([("Chicago, Illinois, United States", LatLng(41.88, -87.63))])
    monkeypatch.setattr(wiring, "geocoder", lambda: geocoder)


def test_geocode_returns_results():
    response = APIClient().get("/api/geocode/", {"q": "chicago"})
    assert response.status_code == 200
    assert response.json() == {
        "results": [{"label": "Chicago, Illinois, United States", "lat": 41.88, "lng": -87.63}]
    }


def test_short_query_rejected():
    response = APIClient().get("/api/geocode/", {"q": "c"})
    assert response.status_code == 400