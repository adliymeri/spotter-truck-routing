import pytest

from planner.domain.entities import RiskLevel as R
from planner.domain.entities import WeatherSample
from planner.domain.risk import assess, rain_level, snow_level, wind_level


@pytest.mark.parametrize("mph,expected", [
    (24.9, R.LOW), (25, R.MODERATE), (34.9, R.MODERATE), (35, R.HIGH),
    (44.9, R.HIGH), (45, R.SEVERE), (54.9, R.SEVERE), (55, R.NO_TRAVEL),
])
def test_wind(mph, expected):
    assert wind_level(mph) == expected


@pytest.mark.parametrize("rate,expected", [
    (0.09, R.LOW), (0.10, R.MODERATE), (0.25, R.HIGH), (0.50, R.SEVERE),
    (1.00, R.SEVERE), (1.01, R.NO_TRAVEL),
])
def test_rain(rate, expected):
    assert rain_level(rate) == expected


@pytest.mark.parametrize("rate,expected", [
    (0.4, R.LOW), (0.5, R.MODERATE), (1.0, R.HIGH), (2.0, R.SEVERE),
    (3.0, R.SEVERE), (3.1, R.NO_TRAVEL),
])
def test_snow(rate, expected):
    assert snow_level(rate) == expected


@pytest.mark.parametrize("wind,weight,expected", [
    (50, 30_000, R.SEVERE),      # at the limit, not over -> plain wind risk
    (50, 30_001, R.NO_TRAVEL),   # 45–54 mph + >30k lb
    (40, 40_000, R.HIGH),
    (40, 40_001, R.SEVERE),      # 35–44 mph + >40k lb
    (60, 5_000, R.NO_TRAVEL),    # >=55 mph, any load
])
def test_load_rules(wind, weight, expected):
    assert assess(WeatherSample(wind, 0, 0), weight).level == expected


def test_calm_weather_is_low_with_no_drivers():
    result = assess(WeatherSample(5, 0, 0), 80_000)
    assert result.level == R.LOW
    assert result.drivers == ()


def test_worst_condition_wins_and_drivers_reported():
    result = assess(WeatherSample(wind_mph=40, rain_in_per_hr=0.6, snow_in_per_hr=0), 45_000)
    assert result.level == R.SEVERE
    assert set(result.drivers) == {"rain", "load"}