"""Swap the two axes of a layout, so that a top-to-bottom layout can serve a left-to-right one.

A flow that runs left to right is laid out as if it ran top to bottom, with every size and
position mirrored about the diagonal, and then mirrored back. The same trick serves the
routing, because a route is only geometry.
"""

from dataclasses import replace

from .model import Edge, EdgeLabel, Frame, Node, Point


def point(value: Point) -> Point:
    """Swap the x and y of a point."""
    return value[1], value[0]


def node(value: Node) -> Node:
    """Swap the axes of a node: its position and its size."""
    return replace(value, x=value.y, y=value.x, width=value.height, height=value.width)


def frame(value: Frame) -> Frame:
    """Swap the axes of a frame: its position and its size."""
    return replace(value, x=value.y, y=value.x, width=value.height, height=value.width)


def edge(value: Edge) -> Edge:
    """Swap the axes of an edge: its points and the position of its label."""
    label = value.label
    if label is not None:
        label = EdgeLabel(text=label.text, at=point(label.at), kind=label.kind)
    return replace(value, points=tuple(point(each) for each in value.points), label=label)
