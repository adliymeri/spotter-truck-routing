from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from planner.domain.entities import LatLng, WeatherSample
from planner.ports import ProviderError

HOURLY_VARS = "wind_speed_10m,rain,showers,snowfall"
MAX_FORECAST_DAYS = 16
CM_PER_INCH = 2.54

Key = tuple[float, float]


def _key(p: LatLng) -> Key:
    return (round(p.lat, 2), round(p.lng, 2))


def _nearest_hour(dt: datetime) -> int:
    return int((dt.timestamp() + 1800) // 3600 * 3600)


@dataclass(frozen=True)
class _HourlySeries:
    start: int
    wind: list[float]
    rain: list[float]
    snow: list[float]

    def at(self, ts: int) -> WeatherSample:
        i = (ts - self.start) // 3600
        if not 0 <= i < len(self.wind):
            raise ProviderError("Forecast not available for the requested time")
        return WeatherSample(wind_mph=self.wind[i], rain_in_per_hr=self.rain[i], snow_in_per_hr=self.snow[i])


def _parse(item: dict) -> _HourlySeries:
    hourly = item["hourly"]
    snow_factor = 1 / CM_PER_INCH if item.get("hourly_units", {}).get("snowfall") == "cm" else 1.0
    return _HourlySeries(
        start=hourly["time"][0],
        wind=[w or 0.0 for w in hourly["wind_speed_10m"]],
        rain=[(r or 0.0) + (s or 0.0) for r, s in zip(hourly["rain"], hourly["showers"])],
        snow=[(s or 0.0) * snow_factor for s in hourly["snowfall"]],
    )


class OpenMeteoWeather:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        batch_size: int,
        client: httpx.Client | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._now = now
        self._base_url = base_url
        self._batch_size = batch_size

    def get_samples(self, points: Sequence[tuple[LatLng, datetime]]) -> list[WeatherSample]:
        if not points:
            return []
        last_eta = max(eta for _, eta in points)
        series = self._fetch([p for p, _ in points], self._days_until(last_eta))
        return [series[_key(p)].at(_nearest_hour(eta)) for p, eta in points]

    def get_hourly_grid(
        self, points: Sequence[LatLng], start: datetime, hours: int = 48
    ) -> list[list[WeatherSample]]:
        if not points:
            return []
        t0 = _nearest_hour(start)
        series = self._fetch(points, self._days_until(datetime.fromtimestamp(t0 + hours * 3600, UTC)))
        return [[series[_key(p)].at(t0 + h * 3600) for h in range(hours + 1)] for p in points]

    def _days_until(self, last: datetime) -> int:
        days = (last.astimezone(UTC).date() - self._now().date()).days + 1
        if days > MAX_FORECAST_DAYS:
            raise ProviderError(f"Forecast only available {MAX_FORECAST_DAYS} days ahead")
        return max(days, 1)

    def _fetch(self, points: Sequence[LatLng], days: int) -> dict[Key, _HourlySeries]:
        locations = list(dict.fromkeys(_key(p) for p in points))
        result: dict[Key, _HourlySeries] = {}

        for i in range(0, len(locations), self._batch_size):
            chunk = locations[i : i + self._batch_size]
            params = {
                "latitude": ",".join(str(lat) for lat, _ in chunk),
                "longitude": ",".join(str(lng) for _, lng in chunk),
                "hourly": HOURLY_VARS,
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "GMT",
                "timeformat": "unixtime",
                "forecast_days": days,
            }
            try:
                response = self._client.get(self._base_url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError(f"Open-Meteo request failed: {exc}") from exc

            data = response.json()
            items = data if isinstance(data, list) else [data]
            for loc, item in zip(chunk, items):
                result[loc] = _parse(item)

        return result