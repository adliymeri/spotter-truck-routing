import httpx
import pytest

from planner.adapters.mapbox_routing import MapboxRouting
from planner.domain.entities import LatLng
from planner.ports import ProviderError

TOKEN = "pk.test-secret"
ORIGIN = LatLng(41.88, -87.63)
DESTINATION = LatLng(39.10, -84.51)
MAIN_COORDS = [[-87.63, 41.88], [-86.0, 40.5], [-84.51, 39.10]]


def fake_route(coords: list[list[float]], distance_m: float, duration_s: float) -> dict:
    segments = len(coords) - 1
    return {
        "distance": distance_m,
        "duration": duration_s,
        "geometry": {"coordinates": coords},
        "legs": [
            {
                "annotation": {
                    "distance": [distance_m / segments] * segments,
                    "duration": [duration_s / segments] * segments,
                }
            }
        ],
    }


def shifted(shift: float) -> list[list[float]]:
    return [MAIN_COORDS[0], [-86.0 + shift, 40.5 + shift], MAIN_COORDS[2]]


def make_routing(direct_routes, detour_route=None, calls=None) -> MapboxRouting:
    calls = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        waypoints = request.url.path.rsplit("/", 1)[-1].split(";")
        if len(waypoints) == 2:
            return httpx.Response(200, json={"code": "Ok", "routes": direct_routes})
        detour = detour_route(len(calls)) if detour_route else fake_route(shifted(len(calls)), 300_000, 12_000)
        return httpx.Response(200, json={"code": "Ok", "routes": [detour]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return MapboxRouting(
        token=TOKEN, base_url="https://test.local/directions", timeout_seconds=1, client=client
    )


def test_three_routes_converted_and_sorted_by_duration():
    routing = make_routing([
        fake_route(shifted(0), 160_934.4, 7200),
        fake_route(shifted(1), 170_000, 5400),
        fake_route(shifted(2), 180_000, 9000),
    ])
    routes = routing.get_routes(ORIGIN, DESTINATION)

    assert [r.id for r in routes] == ["route-1", "route-2", "route-3"]
    assert [r.duration_hours for r in routes] == [1.5, 2.0, 2.5]

    hundred_miles = routes[1]
    assert hundred_miles.distance_miles == pytest.approx(100)
    assert hundred_miles.cumulative_miles == pytest.approx((0, 50, 100))
    assert hundred_miles.cumulative_hours == pytest.approx((0, 1, 2))
    assert hundred_miles.geometry[0] == LatLng(41.88, -87.63)


def test_detours_fill_up_to_three_routes():
    calls: list[httpx.Request] = []
    routes = make_routing([fake_route(MAIN_COORDS, 200_000, 9000)], calls=calls).get_routes(ORIGIN, DESTINATION)
    assert len(routes) == 3
    assert len(calls) == 3


def test_out_and_back_detour_is_rejected():
    spur = [MAIN_COORDS[0], [-86.0, 40.5], [-85.99, 40.51], [-86.0, 40.5], MAIN_COORDS[2]]
    calls: list[httpx.Request] = []
    routing = make_routing(
        [fake_route(MAIN_COORDS, 200_000, 9000)],
        detour_route=lambda _: fake_route(spur, 202_000, 9100),
        calls=calls,
    )
    routes = routing.get_routes(ORIGIN, DESTINATION)
    assert len(routes) == 1
    assert len(calls) == 5  # 1 direct + 4 detour attempts, all rejected


def test_weight_is_sent_in_tonnes():
    calls: list[httpx.Request] = []
    routing = make_routing([fake_route(shifted(i), 1000 + i, 100) for i in range(3)], calls=calls)
    routing.get_routes(ORIGIN, DESTINATION, max_weight_lb=80_000)
    assert calls[0].url.params["max_weight"] == "36.3"


def test_http_error_does_not_leak_token():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    routing = MapboxRouting(
        token=TOKEN, base_url="https://test.local/directions", timeout_seconds=1, client=client
    )
    with pytest.raises(ProviderError) as exc:
        routing.get_routes(ORIGIN, DESTINATION)
    assert TOKEN not in str(exc.value)
    assert "401" in str(exc.value)


def test_missing_token_is_rejected():
    with pytest.raises(ValueError):
        MapboxRouting(token="", base_url="https://x", timeout_seconds=1)