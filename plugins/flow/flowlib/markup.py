"""Small helpers that keep the HTML and SVG builders readable."""

import html


def fmt(number: float) -> str:
    """Format a number without a trailing ``.0``."""
    return f"{number:g}"


def px(number: float) -> str:
    """Format a number as a CSS length in pixels."""
    return f"{number:g}px"


def esc(text: object) -> str:
    """Escape text for use in HTML content or in an attribute value."""
    return html.escape(str(text))


def css(properties: dict[str, str]) -> str:
    """Join CSS properties into the text of a ``style`` attribute.

    Args:
        properties: Property name to value, in the order they should be written.

    Returns:
        ``name:value`` pairs separated by semicolons.
    """
    return ";".join(f"{name}:{value}" for name, value in properties.items())


def tag(name: str, style: dict[str, str], content: str = "", **attributes: str) -> str:
    """Build an HTML element with an inline style.

    Args:
        name: The tag name, such as ``div``.
        style: CSS properties for the ``style`` attribute.
        content: Already-escaped inner markup.
        **attributes: Further attributes; values are escaped.

    Returns:
        The element as markup.
    """
    extra = "".join(f' {key.replace("_", "-")}="{esc(value)}"' for key, value in attributes.items())
    return f'<{name}{extra} style="{css(style)}">{content}</{name}>'
