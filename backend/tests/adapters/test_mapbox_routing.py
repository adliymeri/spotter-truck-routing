import httpx
import pytest

from planner.adapters.mapbox_routing import MapboxRouting
from planner.domain.entities import LatLng
from planner.ports import ProviderError

TOKEN = "pk.test-secret"
ORIGIN = LatLng(41.88, -87.63)
DESTINATION = LatLng(39.10, -84.51)


def fake_route(distance_m: float, duration_s: float) -> dict:
    return {
        "distance": distance_m,
        "duration": duration_s,
        "geometry": {"coordinates": [[-87.63, 41.88], [-86.0, 40.5], [-84.51, 39.10]]},
        "legs": [{"annotation": {"distance": [distance_m / 2] * 2, "duration": [duration_s / 2] * 2}}],
    }


def make_routing(direct_routes: list[dict], calls: list[httpx.Request] | None = None) -> MapboxRouting:
    calls = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        waypoints = request.url.path.rsplit("/", 1)[-1].split(";")
        if len(waypoints) == 2:
            return httpx.Response(200, json={"code": "Ok", "routes": direct_routes})
        detour = fake_route(300_000 + 30_000 * len(calls), 12_000 + 600 * len(calls))
        return httpx.Response(200, json={"code": "Ok", "routes": [detour]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return MapboxRouting(token=TOKEN, base_url="https://test.local/directions", timeout_seconds=1, client=client)


def test_three_routes_converted_and_sorted_by_duration():
    routing = make_routing([
        fake_route(160_934.4, 7200),
        fake_route(170_000, 5400),
        fake_route(180_000, 9000),
    ])
    routes = routing.get_routes(ORIGIN, DESTINATION)

    assert [r.id for r in routes] == ["route-1", "route-2", "route-3"]
    assert [r.duration_hours for r in routes] == [1.5, 2.0, 2.5]

    fastest_100mi = routes[1]
    assert fastest_100mi.distance_miles == pytest.approx(100)
    assert fastest_100mi.cumulative_miles == pytest.approx((0, 50, 100))
    assert fastest_100mi.cumulative_hours == pytest.approx((0, 1, 2))
    assert fastest_100mi.geometry[0] == LatLng(41.88, -87.63)


def test_detours_fill_up_to_three_routes():
    calls: list[httpx.Request] = []
    routes = make_routing([fake_route(200_000, 9000)], calls).get_routes(ORIGIN, DESTINATION)
    assert len(routes) == 3
    assert len(calls) == 3


def test_weight_is_sent_in_tonnes():
    calls: list[httpx.Request] = []
    make_routing([fake_route(1, 1)] * 3, calls).get_routes(ORIGIN, DESTINATION, max_weight_lb=80_000)
    assert calls[0].url.params["max_weight"] == "36.3"


def test_http_error_does_not_leak_token():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    routing = MapboxRouting(token=TOKEN, base_url="https://test.local/directions", timeout_seconds=1, client=client)
    with pytest.raises(ProviderError) as exc:
        routing.get_routes(ORIGIN, DESTINATION)
    assert TOKEN not in str(exc.value)
    assert "401" in str(exc.value)


def test_missing_token_is_rejected():
    with pytest.raises(ValueError):
        MapboxRouting(token="", base_url="https://x", timeout_seconds=1)