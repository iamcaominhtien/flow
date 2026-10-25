# Tiny helper to emit absolutely positioned flowchart artboards (.dc.html)
import html
from fcicons import icon as bigicon
from fcdetail import D as DETAIL, detail as detailicon
import fcdetail_a, fcdetail_b, fcdetail_c, fcdetail_d, fcdetail_e, fcdetail_f, fcdetail_g
ROOT = '/path/to/flowdesign/project/'
INK, SLATE = '#0F172A', '#475569'
COL = {
 'terminator': ('#DCF5E1', '#1E7A3C'), 'fail': ('#FDE4E4', '#B42318'),
 'process': ('#DCEEFB', '#1E5AA8'), 'decision': ('#FFF1DD', '#B45309'),
 'io': ('#E6E3FB', '#4F46A5'), 'document': ('#FFFFFF', '#334155'),
 'subprocess': ('#DCEEFB', '#1E5AA8'), 'preparation': ('#D3F3EF', '#0F766E'),
 'connector': ('#FDE4E4', '#B42318'),
}
ROLE = {  # color, dash, stroke width
 'next': (INK, None, 2), 'yes': ('#15803D', None, 2), 'no': ('#B42318', None, 2),
 'back': (SLATE, '6 5', 2), 'main': ('#1D4ED8', None, 4), 'data': ('#7C3AED', '6 5', 2),
}
CHIP = {'yes': ('#DCF5E1', '#15803D'), 'no': ('#FDE4E4', '#B42318'), 'back': ('#E2E8F0', '#334155'), 'plain': ('#F1F5F9', '#334155')}

def shape_svg(kind, w, h):
    fill, stroke = COL[kind]
    i = 1
    if kind in ('terminator', 'fail'):
        d = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{(h-2)/2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    elif kind == 'process':
        d = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    elif kind == 'subprocess':
        d = (f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
             f'<path d="M14 1V{h-1}M{w-14} 1V{h-1}" stroke="{stroke}" stroke-width="2" fill="none"/>')
    elif kind == 'decision':
        d = f'<path d="M{w/2} 1L{w-1} {h/2}L{w/2} {h-1}L1 {h/2}Z" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>'
    elif kind == 'io':
        s = min(18, w / 6)
        d = f'<path d="M{s} 1H{w-1}L{w-s} {h-1}H1Z" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>'
    elif kind == 'document':
        r = h * 0.2
        d = (f'<path d="M1 1H{w-1}V{h-r:.1f}Q{w*0.75:.1f} {h-r*2.2:.1f} {w/2:.1f} {h-r:.1f}T1 {h-r:.1f}Z" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>')
    elif kind == 'preparation':
        s = min(20, w / 5)
        d = f'<path d="M{s} 1H{w-s}L{w-1} {h/2}L{w-s} {h-1}H{s}L1 {h/2}Z" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>'
    elif kind == 'connector':
        d = f'<circle cx="{w/2}" cy="{h/2}" r="{min(w,h)/2-1}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">{d}</svg>'


ICONS = {
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
 'phone': '<rect x="7" y="2" width="10" height="20" rx="2.5"/><path d="M11 18h2"/>',
 'cart': '<path d="M3 4h3l2.5 11h10L21 7H7"/><circle cx="10" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/>',
 'card': '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20M6 15h4"/>',
 'bell': '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>',
 'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'pin': '<path d="M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 'pot': '<path d="M4 11h16v3a6 6 0 0 1-6 6h-4a6 6 0 0 1-6-6z"/><path d="M8 7c0-2 2-2 2-4M14 7c0-2 2-2 2-4"/>',
 'check': '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
 'box': '<path d="M3 8l9-5 9 5v9l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v9"/>',
 'bike': '<circle cx="6" cy="17" r="3.5"/><circle cx="18" cy="17" r="3.5"/><path d="M6 17l4-8h5l3 8M10 9L8.5 6H6"/>',
 'refund': '<path d="M4 12a8 8 0 1 1 2.5 5.8"/><path d="M4 5v7h7"/>',
 'warn': '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
 'star': '<path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1L3.2 9.4l6.1-.8z"/>',
 'doc': '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 12h7M9 16h7"/>',
 'store': '<path d="M3 9l1.5-5h15L21 9"/><path d="M4 9v11h16V9M9 20v-6h6v6"/>',
}
def icon_svg(name, x, y, size=18, color='#0F172A'):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" style="position:absolute;left:{x}px;top:{y}px" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'

class Node:
    def __init__(s, cx, cy, w, h): s.cx, s.cy, s.w, s.h = cx, cy, w, h
    def t(s, dx=0): return (s.cx + dx, s.cy - s.h / 2)
    def b(s, dx=0): return (s.cx + dx, s.cy + s.h / 2)
    def l(s, dy=0): return (s.cx - s.w / 2, s.cy + dy)
    def r(s, dy=0): return (s.cx + s.w / 2, s.cy + dy)

class Board:
    def __init__(s, name, title, w, h, desc=None, hdr=True):
        s.name, s.title, s.w, s.h, s.parts, s.mid = name, title, w, h, [], 0
        if hdr:
            s.parts.append(f'<div style="position:absolute;left:64px;top:48px;display:flex;flex-direction:column;gap:8px"><div style="font-size:24px;font-weight:600">{html.escape(title)}</div>'
                           + (f'<div style="font-size:13px;line-height:20px;color:#475569;max-width:{min(w-128,900)}px">{desc}</div>' if desc else '') + '</div>')
    def raw(s, h): s.parts.append(h)
    def rect(s, x, y, w, h, bg, border, radius=16, dashed=True, extra=''):
        s.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:{bg};border:1.5px {"dashed" if dashed else "solid"} {border};border-radius:{radius}px;{extra}"></div>')
    def pill(s, x, y, text, bg, fg='#FFFFFF', w=None):
        s.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;{"width:%dpx;" % w if w else ""}height:22px;padding:0 12px;box-sizing:border-box;border-radius:999px;background:{bg};color:{fg};font-size:12px;font-weight:700;line-height:22px;text-align:center;white-space:nowrap">{html.escape(text)}</div>')
    def text(s, x, y, t, size=12, color='#475569', weight=400, w=None, mono=False, center=False, lh=None):
        lh = lh or int(size * 1.55)
        st = f'position:absolute;left:{x}px;top:{y}px;font-size:{size}px;line-height:{lh}px;color:{color};font-weight:{weight};' + (f'width:{w}px;' if w else 'white-space:nowrap;') + ("font-family:'JetBrains Mono',monospace;" if mono else '') + ('text-align:center;' if center else '')
        s.raw(f'<div style="{st}">{t}</div>')
    def node(s, kind, cx, cy, w, h, text='', fs=13, chip=None, bold=True, tone=None, icon=None):
        n = Node(cx, cy, w, h)
        k = kind
        inner = w * 0.64 if kind == 'decision' else w - (36 if kind in ('io', 'preparation', 'subprocess') else 20)
        shift = 0
        ic = ''
        if icon:
            il = {'subprocess': 22, 'io': 26, 'preparation': 24}.get(kind, 14)
            ic = icon_svg(icon, il, (h - 18) / 2 - (3 if kind == 'document' else 0), 18, COL[k][1])
            inner -= 24; shift = 12
        lab = f'<div style="position:absolute;left:{(w-inner)/2 + shift}px;top:0;width:{inner}px;height:{h - (6 if kind == "document" else 0)}px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:{fs}px;line-height:{int(fs*1.25)}px;font-weight:{600 if bold else 500};color:#0F172A">{html.escape(text)}</div>' if text else ''
        s.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px">{shape_svg(k, w, h)}{ic}{lab}</div>')
        if chip:
            s.raw(f'<div style="position:absolute;left:{cx-w/2-6:g}px;top:{cy-h/2-10:g}px;min-width:22px;height:20px;padding:0 6px;box-sizing:border-box;border-radius:999px;background:#0F172A;color:#7DD3CB;font:700 11px/20px \'JetBrains Mono\',monospace;text-align:center">{chip}</div>')
        return n
    def label(s, x, y, text, kind='plain', mono=False):
        bg, fg = CHIP[kind]
        s.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;transform:translate(-50%,-50%);padding:2px 8px;border-radius:999px;background:{bg};color:{fg};font-size:11px;font-weight:700;line-height:16px;white-space:nowrap;{"font-family:JetBrains Mono,monospace;" if mono else ""}">{html.escape(text)}</div>')
    def arrow(s, pts, role='next', label=None, lpos=None, lkind=None):
        col, dash, sw = ROLE[role]
        flow = role == 'main'; flow2 = role == 'data'
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            last = i == len(pts) - 2
            s.mid += 1
            pad = 6
            gap = (8 if sw == 4 else 5) if last else 0
            L = abs(x1 - x0) + abs(y1 - y0)
            if abs(y1 - y0) < 0.01:  # horizontal
                left, top, W, H = min(x0, x1), y0 - pad, L, 2 * pad
                dirn = 1 if x1 > x0 else -1
                a, b = (0, L - gap) if dirn > 0 else (L, gap)
                path = f'M {a:g} {pad} L {b:g} {pad}'
            else:
                left, top, W, H = x0 - pad, min(y0, y1), 2 * pad, L
                dirn = 1 if y1 > y0 else -1
                a, b = (0, L - gap) if dirn > 0 else (L, gap)
                path = f'M {pad} {a:g} L {pad} {b:g}'
            mk, mattr = '', ''
            if last:
                mid = f'dc-arrow-head-filled-{s.mid}'
                hu = 4 if sw == 4 else 5
                mk = f'<defs><marker id="{mid}" orient="auto" markerWidth="{hu}" markerHeight="{hu}" refX="{hu/2}" refY="{hu/2}" overflow="visible"><path d="M0 0 L{hu} {hu/2} L0 {hu} Z" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/></marker></defs>'
                mattr = f' marker-end="url(#{mid})"'
            cls = ' class="flow"' if flow else (' class="flow2"' if flow2 else '')
            da = f' stroke-dasharray="{dash}"' if (dash and not flow2) else ''
            s.raw(f'<svg{cls} width="{W:g}" height="{H:g}" viewBox="0 0 {W:g} {H:g}" preserveAspectRatio="none" style="position:absolute;left:{left:g}px;top:{top:g}px;width:{W:g}px;height:{H:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round"{da}>{mk}<path d="{path}"{mattr}></path></svg>')
        if label:
            lx, ly = lpos
            s.label(lx, ly, label, lkind or ({'yes': 'yes', 'no': 'no', 'back': 'back'}.get(role, 'plain')))
    def card(s, cx, cy, title, desc, ic, tone, w=232, h=96, bars=False, style='flat'):
        bg, pb = tone
        px = 24 if bars else 14
        sh = ''.join(f'<div style="position:absolute;top:2px;bottom:2px;width:2px;background:#0F172A;left:{x}px"></div>' for x in ((10, w - 14) if bars else ()))
        s.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:12px;background:{bg}">{sh}'
              f'<div style="position:absolute;left:{px}px;top:14px;padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{pb};box-shadow:0 3px 0 #0F172A;font-size:12.5px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(title)}</div>'
              f'<div style="position:absolute;left:{px}px;top:52px;width:{w-px-86}px;font-size:11.5px;line-height:15px;color:#334155">{html.escape(desc)}</div>'
              + (detailicon(ic, 64, w - 78, (h - 64) / 2 - 2) if style == 'detail' and ic in DETAIL else bigicon(ic, 56, w - 74, (h - 56) / 2 - 2)) + '</div>')
        return Node(cx, cy, w, h)
    def screen_card(s, cx, cy, sid, name, w=150, h=92, style='flat'):
        s.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:#fff;padding:10px 12px;display:flex;flex-direction:column;justify-content:space-between"><span style="background:#0F172A;color:#7DD3CB;font-size:11px;font-weight:700;border-radius:999px;padding:1px 8px;align-self:flex-start">{sid}</span><span style="font-size:14px;font-weight:800">{html.escape(name)}</span>'
              + (detailicon('Mobile', 62, w - 70, (h - 62) / 2) if style == 'detail' else bigicon('Mobile', 46, w - 62, (h - 46) / 2)) + '</div>')
        return Node(cx, cy, w, h)
    def screen(s, cx, cy, sid, name, w=128, h=72):
        s.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:#fff;padding:9px 11px;display:flex;flex-direction:column;justify-content:space-between"><span style="display:flex;align-items:center;justify-content:space-between"><span style="background:#0F172A;color:#7DD3CB;font-size:11px;font-weight:700;border-radius:999px;padding:1px 8px">{sid}</span><svg width="12" height="16" viewBox="0 0 14 18" fill="none" stroke="#475569" stroke-width="1.6" stroke-linecap="round"><rect x="2" y="1" width="10" height="16" rx="2.5"/><path d="M6 14h2"/></svg></span><span style="font-size:13px;font-weight:800">{html.escape(name)}</span></div>')
        return Node(cx, cy, w, h)
    def chip(s, cx, cy, text, dark=True, icon=None):
        bg, fg = ('#0F172A', '#FFFFFF') if dark else ('#E2E8F0', '#334155')
        ic = icon_svg(icon, 0, 0, 12, fg).replace('position:absolute;left:0px;top:0px', 'flex:none') if icon else ''
        s.raw(f'<div style="position:absolute;left:{cx:g}px;top:{cy:g}px;transform:translate(-50%,-50%);height:20px;padding:0 9px;box-sizing:border-box;border-radius:999px;background:{bg};color:{fg};font-size:11px;font-weight:700;line-height:20px;white-space:nowrap;display:flex;align-items:center;gap:5px">{ic}{html.escape(text)}</div>')
    def bar(s, x, y0, y1):
        s.raw(f'<div style="position:absolute;left:{x-4}px;top:{y0}px;width:8px;height:{y1-y0}px;border-radius:4px;background:#0F172A"></div>')
    def save(s, hh=None):
        H = hh or s.h
        body = '\n'.join(s.parts)
        out = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Flowchart: {html.escape(s.title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#F8FAFC;font-family:'Inter',system-ui,sans-serif;color:#0F172A}}
h2,p,ul{{margin:0}}
@keyframes dc-flow{{to{{stroke-dashoffset:-18}}}}
.flow{{stroke-dasharray:10 8;animation:dc-flow 0.7s linear infinite}}
@keyframes dc-flow2{{to{{stroke-dashoffset:-12}}}}
.flow2{{stroke-dasharray:6 6;animation:dc-flow2 1.8s linear infinite}}
@media (prefers-reduced-motion: reduce){{.flow,.flow2{{animation:none}}}}
</style>
</helmet>
<div style="position: relative; width: {s.w}px; height: {H}px; background: #F8FAFC; overflow: hidden">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{s.w},"height":{H}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''
        open(ROOT + s.name + '.dc.html', 'w', encoding='utf-8').write(out)
        return (s.name + '.dc.html', s.w, H, s.title)
