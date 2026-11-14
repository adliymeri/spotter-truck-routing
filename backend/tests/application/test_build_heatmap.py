from datetime import UTC, datetime

from planner.application.build_heatmap import HeatmapRequest, build_heatmap
from planner.domain.entities import LatLng, RiskLevel, WeatherSample
from tests.fakes import FakeWeather

START = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)
CORRIDOR = tuple(LatLng(41.0, -88.0 + i * 0.25) for i in range(5))


def storm_after_hour_10(p: LatLng, t: datetime) -> WeatherSample:
    hours = (t - START).total_seconds() / 3600
    return WeatherSample(50 if hours >= 10 else 5, 0, 0)


def test_frames_cover_every_hour_and_every_point():
    heatmap = build_heatmap(HeatmapRequest(CORRIDOR, START, 48, 20_000), FakeWeather(storm_after_hour_10))
    assert len(heatmap.frames) == 49
    assert all(len(frame) == len(heatmap.points) for frame in heatmap.frames)


def test_risk_changes_over_time_and_respects_load():
    light = build_heatmap(HeatmapRequest(CORRIDOR, START, 48, 20_000), FakeWeather(storm_after_hour_10))
    heavy = build_heatmap(HeatmapRequest(CORRIDOR, START, 48, 35_000), FakeWeather(storm_after_hour_10))
    assert set(light.frames[0]) == {RiskLevel.LOW}
    assert set(light.frames[10]) == {RiskLevel.SEVERE}
    assert set(heavy.frames[10]) == {RiskLevel.NO_TRAVEL}
