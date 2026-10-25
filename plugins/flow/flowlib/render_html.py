"""Render a scene as one self-contained HTML file: boxes, inline SVG and CSS animation."""

import html
import math

from .theme import icons, theme

FONTS_LINK = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)


def _esc(text):
    return html.escape(str(text))


def _shape_svg(shape, w, h, fill, stroke):
    """The outline of one flowchart shape, drawn to fill a w x h box."""
    common = f'fill="{fill}" stroke="{stroke}" stroke-width="2"'
    if shape in ("terminator", "fail"):
        body = (
            f'<rect x="1" y="1" width="{w - 2:g}" height="{h - 2:g}" '
            f'rx="{(h - 2) / 2:g}" {common}/>'
        )
    elif shape in ("process", "subprocess"):
        body = f'<rect x="1" y="1" width="{w - 2:g}" height="{h - 2:g}" rx="10" {common}/>'
        if shape == "subprocess":
            body += (
                f'<path d="M14 1V{h - 1:g}M{w - 14:g} 1V{h - 1:g}" stroke="{stroke}" '
                'stroke-width="2" fill="none"/>'
            )
    elif shape == "decision":
        body = (
            f'<path d="M{w / 2:g} 1L{w - 1:g} {h / 2:g}L{w / 2:g} {h - 1:g}L1 {h / 2:g}Z" '
            f'{common} stroke-linejoin="round"/>'
        )
    elif shape == "io":
        s = min(18, w / 6)
        body = (
            f'<path d="M{s:g} 1H{w - 1:g}L{w - s:g} {h - 1:g}H1Z" {common} '
            'stroke-linejoin="round"/>'
        )
    elif shape == "document":
        r = h * 0.2
        body = (
            f'<path d="M1 1H{w - 1:g}V{h - r:.1f}Q{w * 0.75:.1f} {h - r * 2.2:.1f} {w / 2:.1f} '
            f'{h - r:.1f}T1 {h - r:.1f}Z" {common} stroke-linejoin="round"/>'
        )
    elif shape == "preparation":
        s = min(20, w / 5)
        body = (
            f'<path d="M{s:g} 1H{w - s:g}L{w - 1:g} {h / 2:g}L{w - s:g} {h - 1:g}H{s:g}'
            f'L1 {h / 2:g}Z" {common} stroke-linejoin="round"/>'
        )
    else:  # connector
        body = f'<circle cx="{w / 2:g}" cy="{h / 2:g}" r="{min(w, h) / 2 - 1:g}" {common}/>'
    return (
        f'<svg width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" preserveAspectRatio="none" '
        f'style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">{body}</svg>'
    )


def _icon_svg(name, x, y, size, color):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'style="position:absolute;left:{x:g}px;top:{y:g}px" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{icons()[name]}</svg>"
    )


def _node(node, t):
    shape, w, h = node["shape"], node["w"], node["h"]
    colors = dict(t["shapes"][shape])
    if "tone" in node:
        colors["fill"] = t["tones"][node["tone"]]["box"]
    parts = [_shape_svg(shape, w, h, colors["fill"], colors["stroke"])]

    inner = (
        w * 0.64
        if shape == "decision"
        else w - (36 if shape in ("io", "preparation", "subprocess") else 20)
    )
    shift = 0
    if "icon" in node:
        left = {"subprocess": 22, "io": 26, "preparation": 24}.get(shape, 14)
        top = (h - 18) / 2 - (3 if shape == "document" else 0)
        parts.append(_icon_svg(node["icon"], left, top, 18, colors["stroke"]))
        inner -= 24
        shift = 12

    text = node.get("text", "")
    lines = [text] if isinstance(text, str) else text
    if lines:
        fs = node.get("font_size", 13)
        box_h = h - (6 if shape == "document" else 0)
        label = "<br>".join(_esc(line) for line in lines)
        parts.append(
            f'<div style="position:absolute;left:{(w - inner) / 2 + shift:g}px;top:0;'
            f"width:{inner:g}px;height:{box_h:g}px;display:flex;align-items:center;"
            f"justify-content:center;text-align:center;font-size:{fs}px;"
            f'line-height:{int(fs * 1.25)}px;font-weight:600;color:{t["ink"]}">{label}</div>'
        )
    out = (
        f'<div data-id="{_esc(node["id"])}" style="position:absolute;left:{node["x"]:g}px;'
        f'top:{node["y"]:g}px;width:{w:g}px;height:{h:g}px">{"".join(parts)}</div>'
    )
    if "number" in node:
        out += (
            f'<div style="position:absolute;left:{node["x"] - 6:g}px;top:{node["y"] - 10:g}px;'
            "min-width:22px;height:20px;padding:0 6px;box-sizing:border-box;border-radius:999px;"
            f"background:{t['ink']};color:#7DD3CB;font:700 11px/20px 'JetBrains Mono',"
            f'monospace;text-align:center">{_esc(node["number"])}</div>'
        )
    return out


def _frame(frame, t):
    tone = t["tones"][frame.get("tone", "gray")]
    out = (
        f'<div data-id="{_esc(frame["id"])}" style="position:absolute;left:{frame["x"]:g}px;'
        f"top:{frame['y']:g}px;width:{frame['w']:g}px;height:{frame['h']:g}px;box-sizing:border-box;"
        f'background:{tone["box"]};border:1.5px dashed {tone["pill"]};border-radius:16px"></div>'
    )
    if frame.get("label"):
        out += (
            f'<div style="position:absolute;left:{frame["x"] + 16:g}px;top:{frame["y"] + 12:g}px;'
            f"height:22px;padding:0 12px;box-sizing:border-box;border-radius:999px;"
            f"background:{tone['pill']};color:{t['ink']};font-size:12px;font-weight:700;"
            f'line-height:22px;white-space:nowrap">{_esc(frame["label"])}</div>'
        )
    return out


def _shorten(points, gap):
    """Pull the last point back along the last segment so the arrowhead tip touches the box."""
    (x0, y0), (x1, y1) = points[-2], points[-1]
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= gap or length == 0:
        return points
    k = (length - gap) / length
    return [*points[:-1], [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k]]


def _edge(edge, t):
    role = t["roles"][edge.get("role", "next")]
    points = [list(p) for p in edge["points"]]
    arrow = edge.get("arrow", "end") == "end"
    if arrow:
        points = _shorten(points, role["gap"])
    d = "M " + " L ".join(f"{x:g} {y:g}" for x, y in points)
    attrs = [
        f'd="{d}"',
        f'stroke="{role["color"]}"',
        f'stroke-width="{role["width"]}"',
        'fill="none"',
        'stroke-linejoin="round"',
    ]
    if role.get("dash"):
        attrs.append(f'stroke-dasharray="{role["dash"]}"')
    if role.get("animation"):
        attrs.append(f'class="{role["animation"]}"')
    if arrow:
        attrs.append(f'marker-end="url(#head-{edge.get("role", "next")})"')
    return f'<path data-id="{_esc(edge["id"])}" {" ".join(attrs)}/>'


def _markers(t):
    out = []
    for name, role in t["roles"].items():
        n = role["head"]
        out.append(
            f'<marker id="head-{name}" orient="auto" markerWidth="{n}" markerHeight="{n}" '
            f'refX="{n / 2:g}" refY="{n / 2:g}" overflow="visible">'
            f'<path d="M0 0 L{n} {n / 2:g} L0 {n} Z" fill="{role["color"]}" '
            'stroke="none"/></marker>'
        )
    return "<defs>" + "".join(out) + "</defs>"


def _label(edge, t):
    label = edge["label"]
    chip = t["chips"][label.get("kind", "plain")]
    x, y = label["at"]
    return (
        f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;transform:translate(-50%,-50%);'
        f"padding:2px 8px;border-radius:999px;background:{chip['bg']};color:{chip['fg']};"
        f'font-size:11px;font-weight:700;line-height:16px;white-space:nowrap">{_esc(label["text"])}</div>'
    )


def _css(t):
    sans, mono = t["fonts"]["sans"], t["fonts"]["mono"]
    rules = [
        f"body{{margin:0;background:{t['canvas']};font-family:'{sans}',system-ui,sans-serif;"
        f"color:{t['ink']}}}",
        f".mono{{font-family:'{mono}',monospace}}",
    ]
    for name, a in t["animations"].items():
        rules.append(f"@keyframes {name}{{to{{stroke-dashoffset:{a['offset']}}}}}")
        rules.append(f".{name}{{animation:{name} {a['seconds']}s linear infinite}}")
    rules.append("@media (prefers-reduced-motion: reduce){.flow,.flow2{animation:none}}")
    return "\n".join(rules)


def render(scene):
    """Return the HTML text for a validated scene."""
    t = theme()
    w, h = scene["size"]
    body = [_frame(f, t) for f in scene.get("frames", [])]
    body += [_node(n, t) for n in scene.get("nodes", [])]
    edges = scene.get("edges", [])
    body.append(
        f'<svg width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" '
        'style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">'
        + _markers(t)
        + "".join(_edge(e, t) for e in edges)
        + "</svg>"
    )
    body += [_label(e, t) for e in edges if e.get("label")]
    if scene.get("title"):
        desc = scene.get("desc")
        body.append(
            '<div style="position:absolute;left:64px;top:48px;display:flex;flex-direction:column;'
            f'gap:8px"><div style="font-size:24px;font-weight:600">{_esc(scene["title"])}</div>'
            + (
                f'<div style="font-size:13px;line-height:20px;color:{t["slate"]};'
                f'max-width:{min(w - 128, 900):g}px">{_esc(desc)}</div>'
                if desc
                else ""
            )
            + "</div>"
        )
    title = _esc(scene.get("title") or "Diagram")
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        f'<link href="{FONTS_LINK}" rel="stylesheet">\n'
        f"<style>\n{_css(t)}\n</style>\n</head>\n<body>\n"
        f'<div style="position:relative;width:{w:g}px;height:{h:g}px;background:{t["canvas"]};'
        f'overflow:hidden">\n' + "\n".join(body) + "\n</div>\n</body>\n</html>\n"
    )
