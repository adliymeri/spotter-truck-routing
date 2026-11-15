from planner.application.build_heatmap import Heatmap
from planner.application.plan_trip import RoutePlan, TripPlan
from planner.domain.entities import AssessedCheckpoint
from planner.domain.geo import simplify

DISPLAY_TOLERANCE_DEG = 0.0005


def present_trip_plan(plan: TripPlan) -> dict:
    return {
        "recommended_route_id": plan.recommended_route_id,
        "ranking": list(plan.ranking),
        "routes": [_present_route(p) for p in plan.routes],
    }


def _present_route(p: RoutePlan) -> dict:
    s = p.summary
    return {
        "id": p.route.id,
        "distance_miles": round(p.route.distance_miles, 1),
        "duration_hours": round(p.route.duration_hours, 2),
        "arrival": p.checkpoints[-1].checkpoint.eta.isoformat(),
        "geometry": [
            [round(pt.lng, 5), round(pt.lat, 5)] for pt in simplify(p.route.geometry, DISPLAY_TOLERANCE_DEG)
        ],
        "summary": {
            "miles_by_level": {level.name: round(m, 1) for level, m in s.miles_by_level.items()},
            "avg_risk": round(s.avg_risk, 3),
            "worst_level": s.worst_level.name,
        },
        "checkpoints": [_present_checkpoint(c) for c in p.checkpoints],
    }


def _present_checkpoint(a: AssessedCheckpoint) -> dict:
    cp = a.checkpoint
    return {
        "index": cp.index,
        "lat": round(cp.location.lat, 5),
        "lng": round(cp.location.lng, 5),
        "mile_marker": round(cp.mile_marker, 1),
        "segment_miles": round(cp.segment_miles, 1),
        "eta": cp.eta.isoformat(),
        "wind_mph": round(a.weather.wind_mph, 1),
        "rain_in_per_hr": round(a.weather.rain_in_per_hr, 2),
        "snow_in_per_hr": round(a.weather.snow_in_per_hr, 2),
        "risk_level": a.risk.level.name,
        "risk_drivers": list(a.risk.drivers),
    }


def present_heatmap(heatmap: Heatmap) -> dict:
    return {
        "start": heatmap.start.isoformat(),
        "hours": len(heatmap.frames) - 1,
        "spacing_miles": round(heatmap.spacing_miles, 1),
        "points": [[round(p.lng, 4), round(p.lat, 4)] for p in heatmap.points],
        "frames": [[int(level) for level in frame] for frame in heatmap.frames],
    }
