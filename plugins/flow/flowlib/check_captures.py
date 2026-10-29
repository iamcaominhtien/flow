"""Checks of the screenshots of L4 screens: that they exist, fit their device and are current.

An L4 screen shows a screenshot of the running app (``docs/plugin/l4-as-built.md``). A missing
or broken file is an error, since the screen cannot be drawn. A screenshot of the wrong width,
one older than the code that draws the screen, a hotspot outside the picture and a diagram that
carries too many bytes of pictures are warnings.
"""

from .captures import CaptureProblem, PngImage, is_newer, read_png
from .check import Code, Finding, Severity
from .model import Capture, Device, Fidelity, Node, Orientation, Scene

WIDTH_TOLERANCE = 1.6  # a screenshot may be this much wider or narrower than its device's viewport
VIEWPORT_WIDTHS: dict[tuple[Device, Orientation], int] = {
    (Device.PHONE, Orientation.PORTRAIT): 390,
    (Device.PHONE, Orientation.LANDSCAPE): 844,
    (Device.TABLET, Orientation.PORTRAIT): 820,
    (Device.TABLET, Orientation.LANDSCAPE): 1180,
    (Device.DESKTOP, Orientation.PORTRAIT): 1280,
    (Device.DESKTOP, Orientation.LANDSCAPE): 1280,
    (Device.WATCH, Orientation.PORTRAIT): 200,
    (Device.WATCH, Orientation.LANDSCAPE): 200,
}  # the width of a typical viewport, at a scale factor of 1
CAPTURE_BUDGET_BYTES = 8 * 1024 * 1024  # the screenshots of one diagram, before base64
PROBLEM_CODES = {
    CaptureProblem.MISSING: Code.CAPTURE_MISSING,
    CaptureProblem.NOT_PNG: Code.CAPTURE_NOT_PNG,
}


def check_captures(scene: Scene) -> list[Finding]:
    """Check every L4 screen of a scene.

    Args:
        scene: The scene to check.

    Returns:
        The findings; empty when no screen is at L4.
    """
    findings: list[Finding] = []
    total = 0
    for node in scene.nodes:
        if node.screen is None or node.screen.fidelity is not Fidelity.L4:
            continue
        capture = node.screen.capture
        image = read_png(capture.image) if capture else CaptureProblem.MISSING
        if isinstance(image, CaptureProblem):
            findings.append(_problem(node, image))
            continue
        assert capture is not None
        total += image.byte_count
        findings.extend(_image_findings(node, capture, image))
    if total > CAPTURE_BUDGET_BYTES:
        findings.append(_heavy(total))
    return findings


def _problem(node: Node, problem: CaptureProblem) -> Finding:
    """Report a screenshot that cannot be drawn."""
    capture = node.screen.capture if node.screen else None
    where = f" ({capture.image})" if capture else ""
    words = "is missing" if problem is CaptureProblem.MISSING else "is not a PNG file"
    return Finding(
        Severity.ERROR,
        PROBLEM_CODES[problem],
        f"the screenshot of '{node.id}'{where} {words}",
        (node.id,),
    )


def _image_findings(node: Node, capture: Capture, image: PngImage) -> list[Finding]:
    """Report a screenshot of the wrong width, an old one, and hotspots outside it."""
    findings = []
    expected = _viewport_width(node)
    if not expected / WIDTH_TOLERANCE <= image.width <= expected * WIDTH_TOLERANCE:
        findings.append(
            _warn(
                Code.CAPTURE_WIDTH,
                f"the screenshot of '{node.id}' is {image.width} px wide; the viewport of its "
                f"device is about {expected} px. Capture it at that width, scale factor 1",
                node,
            )
        )
    if capture.source and is_newer(capture.source, capture.image):
        findings.append(
            _warn(
                Code.CAPTURE_STALE,
                f"'{capture.source}' changed after the screenshot of '{node.id}' was taken; "
                "capture it again",
                node,
            )
        )
    findings.extend(
        _warn(
            Code.HOTSPOT_OUTSIDE,
            f"the hotspot '{hotspot.text}' of '{node.id}' lies outside its screenshot",
            node,
        )
        for hotspot in capture.hotspots
        if hotspot.box[0] + hotspot.box[2] > image.width
        or hotspot.box[1] + hotspot.box[3] > image.height
    )
    return findings


def _viewport_width(node: Node) -> int:
    """Return the width of a typical viewport of the node's device, in pixels.

    The width, not the shape, is checked: a page taken whole (``full_page``) is taller than the
    device, but a phone screenshot in a desktop frame is far too narrow.
    """
    assert node.screen is not None
    return VIEWPORT_WIDTHS[(node.screen.device, node.screen.orientation)]


def _heavy(total: int) -> Finding:
    """Report a diagram whose screenshots add up to more than the budget."""
    megabytes = total / (1024 * 1024)
    return Finding(
        Severity.WARNING,
        Code.CAPTURE_HEAVY,
        f"the screenshots add up to {megabytes:.1f} MB; the HTML and draw.io files carry them "
        "all. Capture at the device's viewport with a scale factor of 1",
        (),
    )


def _warn(code: Code, message: str, node: Node) -> Finding:
    """Build a warning about one screen."""
    return Finding(Severity.WARNING, code, message, (node.id,))
