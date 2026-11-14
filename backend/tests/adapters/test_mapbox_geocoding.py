import httpx
import pytest

from planner.adapters.mapbox_geocoding import MapboxGeocoder
from planner.domain.entities import LatLng
from planner.ports import ProviderError

TOKEN = "pk.test-secret"


def make_geocoder(handler) -> MapboxGeocoder:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return MapboxGeocoder(
        token=TOKEN, base_url="https://test.local/geocode", timeout_seconds=1, countries="us", client=client
    )


def test_results_are_parsed():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "chicago"
        assert request.url.params["country"] == "us"
        return httpx.Response(200, json={"features": [
            {"properties": {"full_address": "Chicago, Illinois, United States"},
             "geometry": {"coordinates": [-87.63, 41.88]}},
            {"properties": {"name": "Chicago Heights"}, "geometry": {"coordinates": [-87.64, 41.5]}},
            {"properties": {}, "geometry": {"coordinates": [0, 0]}},
        ]})

    results = make_geocoder(handler).search("chicago")
    assert results == [
        ("Chicago, Illinois, United States", LatLng(41.88, -87.63)),
        ("Chicago Heights", LatLng(41.5, -87.64)),
    ]


def test_error_does_not_leak_token():
    with pytest.raises(ProviderError) as exc:
        make_geocoder(lambda r: httpx.Response(401)).search("chicago")
    assert TOKEN not in str(exc.value)