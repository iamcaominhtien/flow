"""Draw the body of an L4 screen: its name, then a screenshot of the running app.

The screenshot is fitted to the width of the body and cut at its bottom, so an L4 screen has the
same frame, width and centre line as the other levels and raising a screen to L4 moves no
arrow. A red dot marks each hotspot, scaled from the screenshot's pixels. A capture that cannot
be read is drawn as a hatched block that says why; the check reports it as an error.
"""

from .captures import CaptureProblem, PngImage, read_png
from .model import Hotspot, Tone
from .screen_body import BodyFrame, hotspot_parts, title_parts
from .screen_part import Bounds, Part, PartKind

PROBLEM_WORDS = {
    CaptureProblem.MISSING: "capture missing",
    CaptureProblem.NOT_PNG: "capture is not a PNG",
}


def capture_parts(frame: BodyFrame) -> list[Part]:
    """Return the parts of the body of an L4 screen, back to front.

    Args:
        frame: The screen being drawn; its view has ``fidelity`` L4.

    Returns:
        The name, then the screenshot and the red dots of its hotspots, or a hatched block
        when the screenshot cannot be read.
    """
    parts, top = title_parts(frame, frame.origin[1])
    area = (frame.left, top, frame.span, frame.bottom - top)
    capture = frame.view.capture
    image = read_png(capture.image) if capture else CaptureProblem.MISSING
    if isinstance(image, CaptureProblem):
        return [*parts, *_problem_parts(frame, area, image)]
    scale = frame.span / image.width
    shown = (frame.left, top, frame.span, min(image.height * scale, area[3]))
    parts.append(_image_part(frame, shown, image))
    hotspots = capture.hotspots if capture else ()
    for hotspot in hotspots:
        box = _scaled(hotspot, shown, scale)
        if box is not None:
            parts.extend(hotspot_parts(frame, box))
    return parts


def _image_part(frame: BodyFrame, bounds: Bounds, image: PngImage) -> Part:
    """Make the screenshot part, with a thin border so a white page keeps its edge."""
    return Part(
        PartKind.IMAGE,
        bounds,
        stroke=frame.theme.tones[Tone.GRAY].stroke,
        stroke_width=1,
        image=image.base64_text,
    )


def _scaled(hotspot: Hotspot, shown: Bounds, scale: float) -> Bounds | None:
    """Return a hotspot's box on the screen, or None when it is below the part that is shown."""
    left, top, width, height = hotspot.box
    box = (shown[0] + left * scale, shown[1] + top * scale, width * scale, height * scale)
    if box[1] + box[3] > shown[1] + shown[3]:
        return None
    return box


def _problem_parts(frame: BodyFrame, area: Bounds, problem: CaptureProblem) -> list[Part]:
    """Draw a hatched block that names what is wrong with the capture."""
    hatch = Part(
        PartKind.HATCH,
        area,
        fill=frame.theme.row_rule,
        stroke=frame.theme.tones[Tone.GRAY].stroke,
        radius=frame.rules.element_radius - 1,
        is_dashed=True,
    )
    words = Part(
        PartKind.TEXT,
        area,
        text=PROBLEM_WORDS[problem],
        font_size=frame.rules.text_size,
        color=frame.theme.slate,
    )
    return [hatch, words]
