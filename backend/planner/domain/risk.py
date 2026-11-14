"""
Risk classification per the assessment rules.

Boundary convention: a value equal to a range's lower bound belongs to that
range (e.g. wind 35.0 mph -> HIGH, rain 0.25 in/hr -> HIGH).
The spec's "No Travel" bounds are followed literally: wind >= 55 mph,
rain > 1.00 in/hr, snow > 3.0 in/hr.
"""

from planner.domain.entities import RiskAssessment, RiskLevel, WeatherSample


def wind_level(mph: float) -> RiskLevel:
    if mph >= 55:
        return RiskLevel.NO_TRAVEL
    if mph >= 45:
        return RiskLevel.SEVERE
    if mph >= 35:
        return RiskLevel.HIGH
    if mph >= 25:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def rain_level(in_per_hr: float) -> RiskLevel:
    if in_per_hr > 1.00:
        return RiskLevel.NO_TRAVEL
    if in_per_hr >= 0.50:
        return RiskLevel.SEVERE
    if in_per_hr >= 0.25:
        return RiskLevel.HIGH
    if in_per_hr >= 0.10:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def snow_level(in_per_hr: float) -> RiskLevel:
    if in_per_hr > 3.0:
        return RiskLevel.NO_TRAVEL
    if in_per_hr >= 2.0:
        return RiskLevel.SEVERE
    if in_per_hr >= 1.0:
        return RiskLevel.HIGH
    if in_per_hr >= 0.5:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def load_level(wind_mph: float, weight_lb: float) -> RiskLevel:
    """Heavy loads escalate wind risk. (>= 55 mph is already No Travel via wind_level.)"""
    if 45 <= wind_mph < 55 and weight_lb > 30_000:
        return RiskLevel.NO_TRAVEL
    if 35 <= wind_mph < 45 and weight_lb > 40_000:
        return RiskLevel.SEVERE
    return RiskLevel.LOW


def assess(sample: WeatherSample, weight_lb: float) -> RiskAssessment:
    """Checkpoint risk = the worst level produced by any rule."""
    levels = {
        "wind": wind_level(sample.wind_mph),
        "rain": rain_level(sample.rain_in_per_hr),
        "snow": snow_level(sample.snow_in_per_hr),
        "load": load_level(sample.wind_mph, weight_lb),
    }
    worst = max(levels.values())
    drivers = tuple(name for name, lvl in levels.items() if lvl == worst and lvl > RiskLevel.LOW)
    return RiskAssessment(level=worst, drivers=drivers)
