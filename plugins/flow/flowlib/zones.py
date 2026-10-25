"""Frames around groups of nodes: zones such as a region, a subnet or a system boundary."""

from dataclasses import dataclass

from .model import Frame, Node
from .spec import Spec, SpecZone
from .theme import LayoutRules


@dataclass(frozen=True)
class _Box:
    """A rectangle given by its edges."""

    left: float
    top: float
    right: float
    bottom: float

    def union(self, other: "_Box") -> "_Box":
        """Return the smallest rectangle that holds both."""
        return _Box(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )


def depth_of(zone: SpecZone, zones: dict[str, SpecZone]) -> int:
    """Return how many zones enclose a zone: 0 for an outermost one."""
    depth = 0
    while zone.parent is not None:
        zone = zones[zone.parent]
        depth += 1
    return depth


def _own_box(zone: SpecZone, spec: Spec, nodes: dict[str, Node]) -> _Box | None:
    """Return the box that holds the nodes placed directly in a zone, or None if it has none."""
    boxes = [
        _Box(node.x, node.y, node.x + node.width, node.y + node.height)
        for node in (nodes[each.id] for each in spec.nodes if each.zone == zone.id)
    ]
    if not boxes:
        return None
    box = boxes[0]
    for other in boxes[1:]:
        box = box.union(other)
    return box


def zone_frames(spec: Spec, nodes: dict[str, Node], rules: LayoutRules) -> tuple[Frame, ...]:
    """Build one frame per zone, wide enough for its nodes and the zones inside it.

    Args:
        spec: The description, with its zones.
        nodes: The placed nodes.
        rules: The layout rules, which hold the padding and the room for the label.

    Returns:
        The frames, outermost first, so that an inner zone is drawn on top of its parent.
    """
    zones = {zone.id: zone for zone in spec.zones}
    boxes: dict[str, _Box] = {}
    ordered = sorted(spec.zones, key=lambda zone: -depth_of(zone, zones))
    for zone in ordered:
        box = _own_box(zone, spec, nodes)
        for child in (each for each in spec.zones if each.parent == zone.id):
            inner = boxes.get(child.id)
            if inner is not None:
                box = inner if box is None else box.union(inner)
        if box is None:
            continue
        pad = rules.zone_padding
        boxes[zone.id] = _Box(
            box.left - pad, box.top - pad - rules.zone_label_room, box.right + pad, box.bottom + pad
        )
    frames = [
        Frame(
            id=f"zone-{zone.id}",
            x=boxes[zone.id].left,
            y=boxes[zone.id].top,
            width=boxes[zone.id].right - boxes[zone.id].left,
            height=boxes[zone.id].bottom - boxes[zone.id].top,
            label=zone.label,
            tone=zone.tone,
        )
        for zone in spec.zones
        if zone.id in boxes
    ]
    return tuple(sorted(frames, key=lambda frame: depth_of(zones[frame.id[5:]], zones)))
