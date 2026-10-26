"""Tests for reading a .drawio file back into a scene."""

import base64
import json
import sys
import urllib.parse
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, import_drawio, render_drawio  # noqa: E402
from flowlib.model import Head, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

HAND_DRAWN = """<mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="pool" value="Team" style="swimlane;container=1" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="400" height="200" as="geometry"/></mxCell>
<mxCell id="a" value="Start&lt;br&gt;here" style="rounded=1;fillColor=#DCEEFB"
  vertex="1" parent="pool">
  <mxGeometry x="20" y="60" width="120" height="50" as="geometry"/></mxCell>
<mxCell id="b" value="Decide" style="rhombus" vertex="1" parent="pool">
  <mxGeometry x="220" y="40" width="100" height="90" as="geometry"/></mxCell>
<mxCell id="e" value="go" style="endArrow=none;dashed=1" edge="1" source="a" target="b" parent="1">
  <mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel>"""


def write_graph(tmp_path: Path, graph: str, compressed: bool) -> Path:
    """Write a graph model as a .drawio file, optionally compressed the way draw.io does.

    Args:
        tmp_path: The folder to write in.
        graph: The ``mxGraphModel`` XML.
        compressed: Whether to deflate and base64 the diagram text.

    Returns:
        The path of the file.
    """
    if compressed:
        raw = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        packed = raw.compress(urllib.parse.quote(graph).encode()) + raw.flush()
        body = base64.b64encode(packed).decode()
    else:
        body = graph
    path = tmp_path / "hand.drawio"
    path.write_text(f'<mxfile><diagram name="p">{body}</diagram></mxfile>')
    return path


def exported(example: str, tmp_path: Path) -> Path:
    """Lay out an example spec and write its draw.io file.

    Args:
        example: The example file name.
        tmp_path: The folder to write in.

    Returns:
        The path of the .drawio file.
    """
    scene = diagrams.layout(json.loads((ROOT / "examples" / example).read_text()))
    path = tmp_path / "out.drawio"
    path.write_text(render_drawio.render(scene))
    return path


@pytest.mark.parametrize(
    "example",
    ["order-flow.spec.json", "delivery-er.spec.json", "shop-architecture.spec.json"],
)
def test_own_file_round_trips_nodes_and_edges(example: str, tmp_path: Path) -> None:
    """Every box and every connected line of a Flow file comes back."""
    original = diagrams.layout(json.loads((ROOT / "examples" / example).read_text()))
    result = import_drawio.convert(exported(example, tmp_path))
    assert len(result.scene.nodes) == len(original.nodes)
    assert len(result.scene.edges) == len(original.edges)
    assert len(result.scene.frames) == len(original.frames)
    assert result.scene.title == original.title


def test_tables_keep_their_rows(tmp_path: Path) -> None:
    """A table comes back as a table node with its column rows."""
    result = import_drawio.convert(exported("delivery-er.spec.json", tmp_path))
    orders = next(node for node in result.scene.nodes if node.id == "node-orders")
    assert orders.shape is Shape.TABLE
    assert orders.sections[0][1].left == "customer_id"
    assert orders.sections[0][1].right == "bigint"
    assert orders.sections[0][1].flags == ("FK",)


@pytest.mark.parametrize("compressed", [False, True])
def test_hand_drawn_file_is_read(tmp_path: Path, *, compressed: bool) -> None:
    """A hand-drawn file, compressed or not, gives shapes, a container frame and a dashed line."""
    scene = import_drawio.convert(write_graph(tmp_path, HAND_DRAWN, compressed)).scene
    shapes = {node.id: node.shape for node in scene.nodes}
    assert shapes == {"a": Shape.PROCESS, "b": Shape.DECISION}
    assert [frame.label for frame in scene.frames] == ["Team"]
    assert scene.nodes[0].text == ("Start", "here")
    (edge,) = scene.edges
    assert edge.dashed
    assert edge.head is Head.NONE


def test_children_of_a_container_get_page_positions(tmp_path: Path) -> None:
    """A box inside a container is placed relative to the page, not to the container."""
    scene: Scene = import_drawio.convert(write_graph(tmp_path, HAND_DRAWN, False)).scene
    frame, node = scene.frames[0], scene.nodes[0]
    assert frame.x < node.x < frame.x + frame.width
    assert frame.y < node.y < frame.y + frame.height


def test_file_without_boxes_is_refused(tmp_path: Path) -> None:
    """A file with no drawable box fails with a message."""
    empty = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>'
    with pytest.raises(SpecError, match="no boxes"):
        import_drawio.convert(write_graph(tmp_path, empty, False))


def test_text_that_is_not_xml_is_refused(tmp_path: Path) -> None:
    """A file that is not XML fails with a message."""
    path = tmp_path / "bad.drawio"
    path.write_text("not xml")
    with pytest.raises(SpecError, match="not XML"):
        import_drawio.convert(path)
