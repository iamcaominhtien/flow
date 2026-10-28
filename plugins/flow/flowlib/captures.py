"""Read the screenshots of L4 screens: PNG files, checked and turned into base64 text.

An L4 screen shows a real screenshot of the running app (``docs/plugin/l4-as-built.md``). The
screenshot is taken outside the plugin; here it is only read. The standard library reads the
size of a PNG from its header and encodes the file, so no image library is needed; it cannot
resize one, so the capture is made at the size it is drawn at.
"""

import base64
import struct
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HEADER_CHUNK = b"IHDR"
HEADER_END = 24  # the signature, the chunk length and type, then the width and the height
SIZE_START = 16


class CaptureProblem(StrEnum):
    """Why a screenshot cannot be drawn."""

    MISSING = "missing"
    NOT_PNG = "not-png"


@dataclass(frozen=True)
class PngImage:
    """A screenshot read from its file: its size in pixels and its bytes as base64 text."""

    width: int
    height: int
    base64_text: str
    byte_count: int


def read_png(path: str) -> PngImage | CaptureProblem:
    """Read a PNG file for drawing.

    Args:
        path: The file.

    Returns:
        The image, or the reason it cannot be read: the file is missing or is not a PNG.
    """
    file = Path(path)
    if not file.is_file():
        return CaptureProblem.MISSING
    return _read_png_file(str(file.resolve()), file.stat().st_mtime_ns)


def is_newer(source: str, image: str) -> bool:
    """Tell whether a source file was changed after a screenshot was taken.

    Args:
        source: The file that draws the screen.
        image: The screenshot.

    Returns:
        True when both files exist and the source is the newer one.
    """
    source_file, image_file = Path(source), Path(image)
    if not (source_file.is_file() and image_file.is_file()):
        return False
    return source_file.stat().st_mtime > image_file.stat().st_mtime


@cache
def _read_png_file(path: str, _changed_ns: int) -> PngImage | CaptureProblem:
    """Read a PNG once per version of the file; the change time is part of the cache key."""
    data = Path(path).read_bytes()
    is_png = data.startswith(PNG_SIGNATURE) and data[12:16] == HEADER_CHUNK
    if not is_png or len(data) < HEADER_END:
        return CaptureProblem.NOT_PNG
    width, height = struct.unpack(">II", data[SIZE_START:HEADER_END])
    return PngImage(width, height, base64.b64encode(data).decode("ascii"), len(data))
