from functools import lru_cache

from django.conf import settings
from django.core.cache import cache

from planner.adapters.mapbox_routing import MapboxRouting
from planner.adapters.open_meteo import OpenMeteoWeather
from planner.adapters.mapbox_geocoding import MapboxGeocoder


@lru_cache(maxsize=1)
def routing() -> MapboxRouting:
    return MapboxRouting(
        token=settings.MAPBOX_TOKEN,
        base_url=settings.MAPBOX_DIRECTIONS_URL,
        timeout_seconds=settings.MAPBOX_TIMEOUT_SECONDS,
    )


@lru_cache(maxsize=1)
def weather() -> OpenMeteoWeather:
    return OpenMeteoWeather(
        base_url=settings.OPEN_METEO_URL,
        timeout_seconds=settings.OPEN_METEO_TIMEOUT_SECONDS,
        batch_size=settings.OPEN_METEO_BATCH_SIZE,
        cache=cache,
        cache_seconds=settings.WEATHER_CACHE_SECONDS,
    )

@lru_cache(maxsize=1)
def geocoder() -> MapboxGeocoder:
    return MapboxGeocoder(
        token=settings.MAPBOX_TOKEN,
        base_url=settings.MAPBOX_GEOCODING_URL,
        timeout_seconds=settings.MAPBOX_TIMEOUT_SECONDS,
        countries=settings.MAPBOX_GEOCODING_COUNTRIES,
    )