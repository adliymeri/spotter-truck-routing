from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

from planner.domain.entities import LatLng, WeatherSample
from planner.ports import ProviderError

HOURLY_VARS = "wind_speed_10m,rain,showers,snowfall"
FORECAST_DAYS = 10
CM_PER_INCH = 2.54

Key = tuple[float, float]


class CacheBackend(Protocol):
    def get_many(self, keys: Iterable[str]) -> dict[str, Any]: ...

    def set_many(self, data: dict[str, Any], timeout: int | None = ...) -> Any: ...


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
        rain=[(r or 0.0) + (s or 0.0) for r, s in zip(hourly["rain"], hourly["showers"], strict=True)],
        snow=[(s or 0.0) * snow_factor for s in hourly["snowfall"]],
    )


class OpenMeteoWeather:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        batch_size: int,
        cache: CacheBackend | None = None,
        cache_seconds: int = 0,
        client: httpx.Client | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._now = now
        self._base_url = base_url
        self._batch_size = batch_size
        self._cache = cache
        self._cache_seconds = cache_seconds

    def get_samples(self, points: Sequence[tuple[LatLng, datetime]]) -> list[WeatherSample]:
        if not points:
            return []
        self._check_horizon(max(eta for _, eta in points))
        series = self._fetch([p for p, _ in points])
        return [series[_key(p)].at(_nearest_hour(eta)) for p, eta in points]

    def get_hourly_grid(
        self, points: Sequence[LatLng], start: datetime, hours: int = 48
    ) -> list[list[WeatherSample]]:
        if not points:
            return []
        t0 = _nearest_hour(start)
        self._check_horizon(datetime.fromtimestamp(t0 + hours * 3600, UTC))
        series = self._fetch(points)
        return [[series[_key(p)].at(t0 + h * 3600) for h in range(hours + 1)] for p in points]

    def _check_horizon(self, last: datetime) -> None:
        days = (last.astimezone(UTC).date() - self._now().date()).days + 1
        if days > FORECAST_DAYS:
            raise ProviderError(f"Forecast only available {FORECAST_DAYS} days ahead")

    def _fetch(self, points: Sequence[LatLng]) -> dict[Key, _HourlySeries]:
        locations = list(dict.fromkeys(_key(p) for p in points))
        day = self._now().date().isoformat()
        cache_keys = {loc: f"open-meteo:{day}:{loc[0]}:{loc[1]}" for loc in locations}

        result: dict[Key, _HourlySeries] = {}
        if self._cache:
            cached = self._cache.get_many(list(cache_keys.values()))
            result = {loc: cached[ck] for loc, ck in cache_keys.items() if ck in cached}

        missing = [loc for loc in locations if loc not in result]
        fresh: dict[Key, _HourlySeries] = {}

        for i in range(0, len(missing), self._batch_size):
            chunk = missing[i : i + self._batch_size]
            params = {
                "latitude": ",".join(str(lat) for lat, _ in chunk),
                "longitude": ",".join(str(lng) for _, lng in chunk),
                "hourly": HOURLY_VARS,
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "GMT",
                "timeformat": "unixtime",
                "forecast_days": FORECAST_DAYS,
            }
            try:
                response = self._client.get(self._base_url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError(f"Open-Meteo request failed: {exc}") from exc

            data = response.json()
            items = data if isinstance(data, list) else [data]
            if len(items) != len(chunk):
                raise ProviderError("Open-Meteo returned an unexpected number of locations")
            for loc, item in zip(chunk, items, strict=True):
                fresh[loc] = _parse(item)

        if self._cache and fresh:
            self._cache.set_many({cache_keys[loc]: s for loc, s in fresh.items()}, timeout=self._cache_seconds)

        result.update(fresh)
        return result