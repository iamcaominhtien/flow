import html
from fclib import *
from fslib import TONES
from umllib import uline, umark
TONES['rose'] = ('#FDE4E4', '#F9C2C0')
ENV = '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 7l9 7 9-7"/>'
def svgi(b, x, y, d, inner, col='#0F172A', fill='none', sw=2):
    b.raw(f'<svg width="{d}" height="{d}" viewBox="0 0 24 24" style="position:absolute;left:{x:g}px;top:{y:g}px;fill:{fill};stroke:{col};stroke-width:{sw};stroke-linecap:round;stroke-linejoin:round" aria-hidden="true">{inner}</svg>')
def event(b, cx, cy, kind='start', marker=None, label=None, r=20, catch=True, lpos='below'):
    fill = {'start': '#DCF5E1', 'intermediate': '#FFF1DD', 'end': '#FDE4E4'}[kind]
    stroke = {'start': '#15803D', 'intermediate': '#B45309', 'end': '#B42318'}[kind]
    sw = 4 if kind == 'end' else 2
    inner = f'<circle cx="{r+2}" cy="{r+2}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if kind == 'intermediate': inner += f'<circle cx="{r+2}" cy="{r+2}" r="{r-5}" fill="none" stroke="{stroke}" stroke-width="2"/>'
    b.raw(f'<svg width="{2*r+4}" height="{2*r+4}" style="position:absolute;left:{cx-r-2:g}px;top:{cy-r-2:g}px;overflow:visible">{inner}</svg>')
    if marker == 'message':
        svgi(b, cx - 11, cy - 11, 22, ENV, stroke, '#0F172A' if not catch else 'none')
        if not catch: b.raw(f'<svg width="22" height="22" viewBox="0 0 24 24" style="position:absolute;left:{cx-11}px;top:{cy-11}px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M3 7l9 7 9-7"/></svg>')
    elif marker == 'timer': svgi(b, cx - 11, cy - 11, 22, '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', stroke)
    elif marker == 'error': svgi(b, cx - 11, cy - 11, 22, '<path d="M13 3L6 13h5l-2 8 8-11h-5z"/>', stroke, stroke if kind == 'end' else 'none', 1.8)
    elif marker == 'signal': svgi(b, cx - 11, cy - 11, 22, '<path d="M12 4L21 19H3z"/>', stroke)
    if label:
        if lpos == 'below': b.text(cx - 60, cy + r + 6, label, size=11.5, color='#334155', w=120, center=True, weight=600, lh=15)
        else: b.text(cx - 60, cy - r - 24, label, size=11.5, color='#334155', w=120, center=True, weight=600, lh=15)
    return Node(cx, cy, 2 * r, 2 * r)
def task(b, cx, cy, text, kind='task', w=130, h=64, tone='blue', sub=False):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:12px;background:{bg};display:flex;align-items:center;justify-content:center;text-align:center;font-size:12.5px;font-weight:700;line-height:15px;padding:0 10px 0 {26 if kind != "task" else 10}px">{html.escape(text)}</div>')
    ix, iy = cx - w / 2 + 7, cy - h / 2 + 6
    if kind == 'user': svgi(b, ix, iy, 18, '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>')
    elif kind == 'service': svgi(b, ix, iy, 18, '<circle cx="12" cy="12" r="3.2"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>')
    elif kind == 'send': svgi(b, ix, iy, 18, ENV, '#fff', '#0F172A')
    elif kind == 'receive': svgi(b, ix, iy, 18, ENV)
    elif kind == 'manual': svgi(b, ix, iy, 18, '<path d="M7 13V6a1.5 1.5 0 0 1 3 0v5M10 11V4.5a1.5 1.5 0 0 1 3 0V11M13 11V5.5a1.5 1.5 0 0 1 3 0V13l2-2a1.6 1.6 0 0 1 2.4 2L16 19a5 5 0 0 1-4 2h-1a5 5 0 0 1-4-2z"/>')
    if sub:
        b.raw(f'<div style="position:absolute;left:{cx-8}px;top:{cy+h/2-17}px;width:16px;height:16px;box-sizing:border-box;border:1.5px solid #0F172A;background:#fff;border-radius:3px;font:800 13px/12px Inter,sans-serif;text-align:center">+</div>')
    return Node(cx, cy, w, h)
def gateway(b, cx, cy, kind='x', label=None, d=26, lpos='above'):
    b.raw(f'<svg width="{2*d+4}" height="{2*d+4}" style="position:absolute;left:{cx-d-2:g}px;top:{cy-d-2:g}px;overflow:visible"><path d="M{d+2} 2L{2*d+2} {d+2}L{d+2} {2*d+2}L2 {d+2}Z" fill="#FFF1DD" stroke="#B45309" stroke-width="2" stroke-linejoin="round"/></svg>')
    m = {'x': '<path d="M8 8l8 8M16 8l-8 8"/>', 'plus': '<path d="M12 6v12M6 12h12"/>', 'o': '<circle cx="12" cy="12" r="6"/>', 'event': '<circle cx="12" cy="12" r="7"/><path d="M12 7.5l3.8 2.8-1.5 4.5H9.7l-1.5-4.5z"/>'}[kind]
    svgi(b, cx - 14, cy - 14, 28, m, '#B45309', 'none', 2.6)
    if label: b.text(cx - 60, (cy - d - 24) if lpos == 'above' else (cy + d + 4), label, size=11.5, color='#334155', w=120, center=True, weight=700, lh=15)
    return Node(cx, cy, 2 * d, 2 * d)
def pool(b, x, y, w, h, name, tone='gray', lanes=None):
    bg, pill = TONES[tone]
    b.raw(f'<div data-lint="box" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div>')
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:40px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px 0 0 6px;background:{pill};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:13px;font-weight:800;white-space:nowrap">{html.escape(name)}</div></div>')
def msgflow(b, pts, label=None, lpos=None):
    uline(b, pts, dashed=True, col='#334155', sw=1.8)
    x, y = pts[0]
    b.raw(f'<div style="position:absolute;left:{x-5:g}px;top:{y-5:g}px;width:10px;height:10px;box-sizing:border-box;border:1.8px solid #334155;border-radius:999px;background:#fff"></div>')
    import math
    p, q = pts[-1], pts[-2]
    L = math.hypot(p[0] - q[0], p[1] - q[1]) or 1
    umark(b, p[0], p[1], ((q[0] - p[0]) / L, (q[1] - p[1]) / L), 'tri', '#334155')
    if label: b.label(lpos[0], lpos[1], label, 'plain')
def save7(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>BPMN: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r

def boundary(b, cx, cy, marker='timer', interrupting=True, r=15):
    stroke = '#B45309'
    dash = '' if interrupting else ' stroke-dasharray="4 3"'
    b.raw(f'<svg width="{2*r+4}" height="{2*r+4}" style="position:absolute;left:{cx-r-2:g}px;top:{cy-r-2:g}px;overflow:visible"><circle cx="{r+2}" cy="{r+2}" r="{r}" fill="#FFF1DD" stroke="{stroke}" stroke-width="2"{dash}/><circle cx="{r+2}" cy="{r+2}" r="{r-4}" fill="none" stroke="{stroke}" stroke-width="1.6"{dash}/></svg>')
    svgi(b, cx - 8, cy - 8, 16, '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', stroke, 'none', 2.4)
    return Node(cx, cy, 2 * r, 2 * r)
def multi(b, cx, cy_bottom):
    for i in (-5, 0, 5): b.raw(f'<div style="position:absolute;left:{cx+i-1}px;top:{cy_bottom-14}px;width:2.5px;height:11px;background:#0F172A"></div>')
def datastore(b, cx, cy, label, w=54, h=46):
    b.raw(f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;overflow:visible"><path d="M2 8Q2 2 {w/2} 2Q{w-2} 2 {w-2} 8V{h-8}Q{w-2} {h-2} {w/2} {h-2}Q2 {h-2} 2 {h-8}Z" fill="#fff" stroke="#334155" stroke-width="2"/><path d="M2 8Q2 14 {w/2} 14Q{w-2} 14 {w-2} 8M2 16Q2 22 {w/2} 22Q{w-2} 22 {w-2} 16" fill="none" stroke="#334155" stroke-width="1.6"/></svg>')
    b.text(cx - 60, cy + h / 2 + 4, label, size=11.5, color='#334155', w=120, center=True, weight=600, lh=15)
    return Node(cx, cy, w, h)
def assoc(b, pts, arrow=True):
    uline(b, pts, dashed=False, col='#64748B', sw=1.6)
    # dotted look
    if arrow:
        import math
        p, q = pts[-1], pts[-2]; L = math.hypot(p[0]-q[0], p[1]-q[1]) or 1
        umark(b, p[0], p[1], ((q[0]-p[0])/L, (q[1]-p[1])/L), 'open', '#64748B')
def blackbox(b, x, y, w, h, name, tone='blue'):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:{pill};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800">{html.escape(name)}</div>')

def loopmark(b, cx, cy_bottom):
    svgi(b, cx - 8, cy_bottom - 20, 16, '<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>', '#0F172A', 'none', 2.4)
