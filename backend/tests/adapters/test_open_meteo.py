from datetime import UTC, datetime, timedelta

import httpx
import pytest

from planner.adapters.open_meteo import OpenMeteoWeather
from planner.domain.entities import LatLng
from planner.ports import ProviderError

DAY = datetime(2026, 11, 20, tzinfo=UTC)
T0 = int(DAY.timestamp())
requests_made: list[httpx.Request] = []


def fake_api(request: httpx.Request) -> httpx.Response:
    requests_made.append(request)
    count = len(request.url.params["latitude"].split(","))
    item = {
        "hourly_units": {"snowfall": "cm"},
        "hourly": {
            "time": [T0 + h * 3600 for h in range(3)],
            "wind_speed_10m": [10, 40, None],
            "rain": [0.0, 0.2, 0.0],
            "showers": [0.0, 0.1, None],
            "snowfall": [0.0, 2.54, 0.0],
        },
    }
    return httpx.Response(200, json=[item] * count)


class DictCache:
    def __init__(self):
        self.data: dict = {}

    def get_many(self, keys):
        return {k: self.data[k] for k in keys if k in self.data}

    def set_many(self, data, timeout=None):
        self.data.update(data)


def make_weather(batch_size: int = 100, cache: DictCache | None = None) -> OpenMeteoWeather:
    client = httpx.Client(transport=httpx.MockTransport(fake_api))
    return OpenMeteoWeather(
        base_url="https://test.local/forecast",
        timeout_seconds=1,
        batch_size=batch_size,
        cache=cache,
        cache_seconds=60,
        client=client,
        now=lambda: DAY,
    )


@pytest.fixture
def weather():
    requests_made.clear()
    return make_weather()


def test_sample_uses_nearest_hour_and_converts_units(weather):
    [sample] = weather.get_samples([(LatLng(40.0, -100.0), DAY + timedelta(minutes=70))])
    assert sample.wind_mph == 40
    assert sample.rain_in_per_hr == pytest.approx(0.3)
    assert sample.snow_in_per_hr == pytest.approx(1.0)


def test_missing_values_become_zero(weather):
    [sample] = weather.get_samples([(LatLng(40.0, -100.0), DAY + timedelta(hours=2))])
    assert sample.wind_mph == 0
    assert sample.rain_in_per_hr == 0


def test_nearby_points_share_one_location(weather):
    weather.get_samples(
        [
            (LatLng(40.001, -100.001), DAY),
            (LatLng(40.002, -100.002), DAY),
        ]
    )
    assert requests_made[0].url.params["latitude"] == "40.0"


def test_time_outside_forecast_raises(weather):
    with pytest.raises(ProviderError):
        weather.get_samples([(LatLng(40.0, -100.0), DAY + timedelta(hours=10))])


def test_requests_are_batched():
    requests_made.clear()
    make_weather(batch_size=2).get_samples([(LatLng(40 + i, -100.0), DAY) for i in range(5)])
    assert len(requests_made) == 3


def test_cached_locations_are_not_requested_again():
    requests_made.clear()
    weather = make_weather(cache=DictCache())
    weather.get_samples([(LatLng(40.0, -100.0), DAY)])
    weather.get_samples([(LatLng(40.0, -100.0), DAY)])
    assert len(requests_made) == 1


def test_rate_limit_gives_friendly_message():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429)))
    weather = OpenMeteoWeather(
        base_url="https://test.local/forecast",
        timeout_seconds=1,
        batch_size=100,
        client=client,
        now=lambda: DAY,
    )
    with pytest.raises(ProviderError) as exc:
        weather.get_samples([(LatLng(40.0, -100.0), DAY)])
    assert "rate limit" in str(exc.value)
    assert "https://" not in str(exc.value)
