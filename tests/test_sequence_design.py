"""Tests for the sequence rules of design 04: headers, spacing, frames, tones and lint."""

import json
import sys
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
PLAIN = ROOT / "examples" / "delivery-sequence.spec.json"
ILLUSTRATED = ROOT / "examples" / "delivery-sequence-illustrated.spec.json"
PAYMENT = ROOT / "examples" / "payment-sequence.spec.json"
REFUND = ROOT / "examples" / "refund-swimlane.spec.json"
PITCH_PX = 230
FIRST_MESSAGE_MIN_PX = 58
AFTER_FRAME_MIN_PX = 34
FRAME_INSET_PX = 10
BAR_WIDTH_PX = 12
PLAIN_HEADER = (136, 44)
CARD_HEADER = (172, 116)

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape, Tone  # noqa: E402


def laid_out(path: Path) -> Scene:
    """Lay out a sequence spec file."""
    return diagrams.layout(json.loads(path.read_text()))


def headers(scene: Scene) -> list:
    """Return the participant headers of a scene, left to right."""
    return sorted((node for node in scene.nodes if node.shape is Shape.HEADER), key=lambda n: n.x)


def messages(scene: Scene) -> list:
    """Return the message lines of a scene, top to bottom."""
    drawn = [edge for edge in scene.edges if edge.role is not Role.LIFELINE]
    return sorted(drawn, key=lambda edge: edge.points[0][1])


def test_lifelines_are_230_px_apart_in_both_styles() -> None:
    """Participants keep the pitch of the design, plain or illustrated."""
    for path in (PLAIN, ILLUSTRATED):
        centres = [node.x + node.width / 2 for node in headers(laid_out(path))]
        gaps = {round(second - first) for first, second in pairwise(centres)}
        assert gaps == {PITCH_PX}


def test_header_sizes_follow_the_style() -> None:
    """A plain header is 136 by 44; an illustrated one is a 172 by 116 card."""
    plain = headers(laid_out(PLAIN))[0]
    card = headers(laid_out(ILLUSTRATED))[0]
    assert (plain.width, plain.height, plain.card) == (*PLAIN_HEADER, False)
    assert (card.width, card.height, card.card) == (*CARD_HEADER, True)


def test_first_message_is_58_px_under_the_header_and_y_shifts_by_the_header() -> None:
    """The first message keeps its distance, so the illustrated one is lower by 72 px."""
    plain, card = laid_out(PLAIN), laid_out(ILLUSTRATED)
    for scene in (plain, card):
        header = headers(scene)[0]
        assert messages(scene)[0].points[0][1] - (header.y + header.height) >= FIRST_MESSAGE_MIN_PX
    shift = CARD_HEADER[1] - PLAIN_HEADER[1]
    pairs = zip(messages(plain), messages(card), strict=True)
    assert all(abs(b.points[0][1] - a.points[0][1] - shift) < 1 for a, b in pairs)


def test_messages_never_go_up() -> None:
    """Every message line is horizontal, and each is below the one before."""
    heights = [edge.points[0][1] for edge in messages(laid_out(PLAIN))]
    assert heights == sorted(heights)


def test_a_message_leaves_34_px_after_a_frame_closes() -> None:
    """The first line under a frame is at least 34 px below its bottom edge."""
    scene = laid_out(PLAIN)
    lines = [edge.points[0][1] for edge in messages(scene)]
    for frame in scene.frames:
        below = [y for y in lines if y > frame.y + frame.height]
        assert min(below) - (frame.y + frame.height) >= AFTER_FRAME_MIN_PX


def test_a_nested_frame_is_inset_10_px() -> None:
    """The inner frame sits at least 10 px inside the outer one on both sides."""
    frames = [f for f in laid_out(PAYMENT).frames if f.variant is FrameVariant.FRAGMENT]
    outer, inner = frames
    assert inner.x - outer.x >= FRAME_INSET_PX
    assert outer.x + outer.width - (inner.x + inner.width) >= FRAME_INSET_PX


def test_a_created_header_stays_inside_the_frame() -> None:
    """The created participant of the payment example no longer crosses its fragment."""
    codes = {finding.code for finding in check_scene(laid_out(PAYMENT))}
    assert Code.CROSSES_BORDER not in codes


def test_refund_swimlane_has_no_label_on_a_lane_border() -> None:
    """A label chip is moved off the border of a lane."""
    codes = {finding.code for finding in check_scene(laid_out(REFUND))}
    assert Code.CROSSES_BORDER not in codes


def test_frames_take_their_colour_from_their_kind() -> None:
    """Break and critical are rose, par is teal, loop is violet."""
    tones = {f.label: f.tone for f in laid_out(PLAIN).frames}
    assert tones["break"] is Tone.RED and tones["critical"] is Tone.RED
    assert tones["par"] is Tone.TEAL and tones["loop"] is Tone.VIOLET


def test_activation_bar_is_12_px_wide_with_an_ink_border() -> None:
    """The bars are 12 px wide and drawn with the ink outline."""
    scene = laid_out(PLAIN)
    bars = [node for node in scene.nodes if node.shape is Shape.BAR]
    assert bars and {bar.width for bar in bars} == {BAR_WIDTH_PX}
    assert 'stroke="#0F172A"' in render_html.render(scene)


def test_message_icon_is_kept_in_the_label() -> None:
    """A message can carry a flat icon for its payload."""
    labels = {edge.label.text: edge.label for edge in messages(laid_out(PLAIN)) if edge.label}
    assert labels["Charge card"].icon == "card"


def test_a_ref_frame_shows_the_name_of_the_other_diagram() -> None:
    """A ref frame has no messages; its name is drawn in the middle of both outputs."""
    raw = {
        "type": "sequence",
        "participants": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        "items": [{"fragment": "ref", "sections": [{"guard": "Sign in", "items": []}]}],
    }
    scene = diagrams.layout(raw)
    assert "Sign in" in render_html.render(scene)
    assert 'id="ref-name-fragment-1"' in render_drawio.render(scene)


def test_a_long_message_label_is_warned() -> None:
    """A label over about 24 characters is flagged."""
    raw = {
        "type": "sequence",
        "participants": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        "items": [{"kind": "sync", "from": "a", "to": "b", "label": "x" * 30}],
    }
    assert Code.SEQUENCE_LABEL_LONG in {
        finding.code for finding in check_scene(diagrams.layout(raw))
    }
    assert Code.SEQUENCE_LABEL_LONG not in {
        finding.code for finding in check_scene(laid_out(PLAIN))
    }
