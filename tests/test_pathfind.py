"""Tests for the route search that goes around boxes and avoids other lines."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib.pathfind import (  # noqa: E402
    CROSSING_COST_PX,
    TRACK_GAP_PX,
    SearchSpace,
    find_route,
    path_cost,
)

BOX = (40.0, -30.0, 60.0, 30.0)


def test_a_free_path_is_a_straight_line() -> None:
    """With nothing in the way the route is one straight segment."""
    found = find_route(SearchSpace(()), (0, 0), (100, 0))
    assert found is not None
    assert found.points == [(0, 0), (100, 0)]


def test_a_box_in_the_way_is_gone_round_with_two_bends() -> None:
    """The route leaves the line, passes the box on one side and comes back."""
    found = find_route(SearchSpace((BOX,)), (0, 0), (100, 0))
    assert found is not None
    assert len(found.points) == 4
    assert max(abs(y) for _, y in found.points) >= 30


def test_a_start_inside_a_box_has_no_route() -> None:
    """A start or end that lies inside an obstacle gives None, not a bad route."""
    assert find_route(SearchSpace((BOX,)), (50, 0), (100, 0)) is None


def test_a_line_already_drawn_is_not_shared_when_there_is_room() -> None:
    """The route keeps off a drawn line that runs along the straight way."""
    drawn = (((0.0, 0.0), (100.0, 0.0)),)
    found = find_route(SearchSpace((), drawn), (0, 0), (100, 0))
    assert found is not None
    assert found.points != [(0, 0), (100, 0)]


def test_a_crossing_is_paid_once() -> None:
    """A route across a drawn line costs its length plus one crossing, not its length alone."""
    drawn = (((50.0, -20.0), (50.0, 20.0)),)
    found = find_route(SearchSpace((), drawn), (0, 0), (100, 0))
    assert found is not None
    assert found.cost == 100 + CROSSING_COST_PX


def test_running_close_beside_a_line_costs_more_than_running_clear_of_it() -> None:
    """A stretch a few pixels from a parallel line is charged; one a track away is not."""
    space = SearchSpace((), (((0.0, 0.0), (100.0, 0.0)),))
    assert path_cost(space, [(0, 4), (100, 4)]) > 100
    assert path_cost(space, [(0, TRACK_GAP_PX), (100, TRACK_GAP_PX)]) == 100
