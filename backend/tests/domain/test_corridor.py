import pytest

from planner.domain.corridor import corridor_grid
from planner.domain.entities import LatLng
from planner.domain.geo import haversine_miles

CORRIDOR = [LatLng(41.0, -88.0 + i * 0.25) for i in range(13)]  # ~160 mi east-west line


def test_all_grid_points_are_within_radius():
    grid = corridor_grid(CORRIDOR, radius_miles=25, max_points=500)
    assert grid.points
    for cell in grid.points:
        assert min(haversine_miles(cell, p) for p in CORRIDOR) <= 25


def test_grid_respects_max_points_by_widening_spacing():
    dense = corridor_grid(CORRIDOR, radius_miles=25, max_points=500)
    sparse = corridor_grid(CORRIDOR, radius_miles=25, max_points=40)
    assert len(sparse.points) <= 40
    assert sparse.spacing_miles > dense.spacing_miles


def test_grid_covers_both_ends_of_the_corridor():
    grid = corridor_grid(CORRIDOR, radius_miles=25, max_points=500)
    for end in (CORRIDOR[0], CORRIDOR[-1]):
        assert min(haversine_miles(end, cell) for cell in grid.points) <= grid.spacing_miles


def test_empty_corridor_rejected():
    with pytest.raises(ValueError):
        corridor_grid([], radius_miles=25, max_points=100)