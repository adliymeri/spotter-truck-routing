from collections.abc import Sequence

from planner.domain.entities import AssessedCheckpoint, RiskLevel, RouteOption, RouteSummary


def summarize_route(route: RouteOption, checkpoints: Sequence[AssessedCheckpoint]) -> RouteSummary:
    if not checkpoints:
        raise ValueError("route has no checkpoints")

    miles = {level: 0.0 for level in RiskLevel}
    for cp in checkpoints:
        miles[cp.risk.level] += cp.checkpoint.segment_miles

    total = sum(miles.values())
    avg = sum(level * m for level, m in miles.items()) / total if total else 0.0

    return RouteSummary(
        route_id=route.id,
        distance_miles=route.distance_miles,
        duration_hours=route.duration_hours,
        miles_by_level=miles,
        avg_risk=avg,
        worst_level=max(cp.risk.level for cp in checkpoints),
    )


def ranking_key(s: RouteSummary) -> tuple[float, ...]:
    """No Travel miles first (stricter than the spec), then: Severe, High, avg risk, duration."""
    m = s.miles_by_level
    return (
        round(m[RiskLevel.NO_TRAVEL], 1),
        round(m[RiskLevel.SEVERE], 1),
        round(m[RiskLevel.HIGH], 1),
        round(s.avg_risk, 3),
        s.duration_hours,
    )


def rank_routes(summaries: Sequence[RouteSummary]) -> list[RouteSummary]:
    return sorted(summaries, key=ranking_key)