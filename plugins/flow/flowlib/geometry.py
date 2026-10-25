"""Small geometry helpers shared by the parts that draw lines between boxes."""

from .model import Node, Point


def center_of(node: Node) -> Point:
    """Return the centre of a node.

    Args:
        node: The node.

    Returns:
        The centre point.
    """
    return (node.x + node.width / 2, node.y + node.height / 2)


def border_point(node: Node, toward: Point) -> Point:
    """Return where a line from the centre of a node toward a point leaves its box.

    Args:
        node: The node the line starts in.
        toward: The point the line aims at.

    Returns:
        The point on the border of the node's rectangle; its centre when ``toward`` is the centre.
    """
    center_x, center_y = center_of(node)
    delta_x, delta_y = toward[0] - center_x, toward[1] - center_y
    if delta_x == 0 and delta_y == 0:
        return (center_x, center_y)
    scale_x = (node.width / 2) / abs(delta_x) if delta_x else float("inf")
    scale_y = (node.height / 2) / abs(delta_y) if delta_y else float("inf")
    scale = min(scale_x, scale_y)
    return (center_x + delta_x * scale, center_y + delta_y * scale)
