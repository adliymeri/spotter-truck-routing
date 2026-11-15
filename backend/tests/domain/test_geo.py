import pytest

from planner.domain.entities import LatLng
from planner.domain.geo import cumulative_miles, haversine_miles, lerp_point, locate, simplify


def test_one_degree_of_latitude_is_about_69_miles():
    assert haversine_miles(LatLng(0, 0), LatLng(1, 0)) == pytest.approx(69.09, abs=0.05)


def test_cumulative_miles_starts_at_zero_and_grows():
    totals = cumulative_miles([LatLng(0, 0), LatLng(1, 0), LatLng(2, 0)])
    assert totals[0] == 0
    assert totals[2] == pytest.approx(2 * totals[1])


def test_lerp_point_midpoint():
    assert lerp_point(LatLng(0, 0), LatLng(2, 4), 0.5) == LatLng(1, 2)


@pytest.mark.parametrize(
    "x,expected",
    [
        (-5, (0, 0.0)),
        (0, (0, 0.0)),
        (30, (0, 0.5)),
        (60, (1, 0.0)),
        (90, (1, 0.5)),
        (200, (1, 1.0)),
    ],
)
def test_locate(x, expected):
    assert locate([0, 60, 120], x) == expected


def test_simplify_drops_points_on_a_straight_line():
    line = [LatLng(0, x / 10) for x in range(11)]
    assert simplify(line, 0.0005) == [LatLng(0, 0), LatLng(0, 1)]


def test_simplify_keeps_corners():
    corner = [LatLng(0, 0), LatLng(0, 0.5), LatLng(0, 1), LatLng(0.5, 1), LatLng(1, 1)]
    assert simplify(corner, 0.0005) == [LatLng(0, 0), LatLng(0, 1), LatLng(1, 1)]
