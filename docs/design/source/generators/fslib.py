# Sequence-diagram builder on top of fclib.Board. Layers: frames, lifelines, activations, messages, notes.
import html
from fclib import *

SEQ_CSS = ''  # sequence uses the same keyframes as fclib.save()
TONES = {
 'blue': ('#DCEEFB', '#BFDBFE'), 'violet': ('#E6E3FB', '#CFC8F7'), 'amber': ('#FFF1DD', '#FFD9A3'),
 'green': ('#DCF5E1', '#B5EBC1'), 'teal': ('#D3F3EF', '#A8E6DE'), 'gray': ('#F1F5F9', '#E2E8F0'),
}
FRAG = {  # frame tint, border, tag fill
 'alt': ('rgba(245,158,58,0.07)', '#D97706', '#FFE2B0'), 'opt': ('rgba(29,78,216,0.05)', '#1D4ED8', '#DCEEFB'),
 'loop': ('rgba(91,75,214,0.06)', '#5B4BD6', '#E6E3FB'), 'par': ('rgba(15,118,110,0.06)', '#0F766E', '#D3F3EF'),
 'break': ('rgba(217,45,32,0.06)', '#B42318', '#FDE4E4'), 'critical': ('rgba(217,45,32,0.06)', '#B42318', '#FDE4E4'),
 'ref': ('rgba(71,85,105,0.05)', '#475569', '#E2E8F0'),
}
MSG = {  # colour, dash, stroke width
 'next': (INK, None, 2), 'main': ('#1D4ED8', None, 4), 'fail': ('#B42318', None, 2),
 'ret': (SLATE, '6 5', 2), 'event': ('#7C3AED', None, 2),
}
_mid = [0]

class Seq:
    def __init__(s, b, parts, top, bottom, style='plain', gap_label=18):
        """parts: list of dict(key,label,x,icon,tone,born=None). top: header top y. bottom: lifeline end y."""
        s.b, s.style, s.top, s.bottom = b, style, top, bottom
        s.P = {p['key']: p for p in parts}
        s.hw, s.hh = (136, 44) if style == 'plain' else (172, 116)
        for p in parts:
            p['head_y'] = p.get('born') if p.get('born') else top
        s.acts, s.frames, s.msgs, s.notes, s.ends = [], [], [], [], []
        s.mids = 0

    # ---- registration -----
    def act(s, key, y0, y1, lvl=0): s.acts.append((key, y0, y1, lvl))
    def frame(s, kind, x0, x1, y0, y1, guard='', div=(), name=None): s.frames.append((kind, x0, x1, y0, y1, guard, div, name))
    def note(s, x, y, w, text, h=None): s.notes.append((x, y, w, text, h))
    def destroy(s, key, y): s.ends.append((key, y))
    def edge(s, key, y, side):
        p = s.P[key]; x = p['x']
        cov = [a for a in s.acts if a[0] == key and a[1] <= y <= a[2]]
        if not cov: return x
        if side > 0: return x + 6 + 6 * max(a[3] for a in cov)
        return x - 6

    def msg(s, a, b, y, label='', kind='sync', role='next', num=None, ic=None, lx=None, to_x=None, from_x=None, ret=False, dy=0):
        s.msgs.append(dict(a=a, b=b, y=y, label=label, kind=kind, role=role, num=num, ic=ic, to_x=to_x, from_x=from_x))
    def selfcall(s, key, y, label, h=30, role='next', num=None, w=44):
        s.msgs.append(dict(a=key, b=key, y=y, label=label, kind='self', role=role, num=num, h=h, w=w, ic=None))

    # ---- drawing -----
    def draw(s):
        b = s.b
        # frames
        for kind, x0, x1, y0, y1, guard, div, name in s.frames:
            tint, bd, tag = FRAG[kind]
            b.raw(f'<div data-lint="box" style="position:absolute;left:{x0}px;top:{y0}px;width:{x1-x0}px;height:{y1-y0}px;box-sizing:border-box;background:{tint};border:1.5px solid {bd};border-radius:6px"></div>')
            tw = 14 + 8 * len(name or kind)
            b.raw(f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{tw}px;height:22px;box-sizing:border-box;background:{tag};border:1.5px solid {bd};border-radius:6px 0 10px 0;font:700 11.5px/19px Inter,sans-serif;color:{bd};padding-left:8px;white-space:nowrap">{name or kind}</div>')
            if guard:
                b.raw(f'<div style="position:absolute;left:{x0+tw+8}px;top:{y0+3}px;font:500 11.5px/16px \'JetBrains Mono\',monospace;color:#334155;white-space:nowrap">{html.escape(guard)}</div>')
            for dy, dg in div:
                b.raw(f'<div data-lint="edge" style="position:absolute;left:{x0}px;top:{dy}px;width:{x1-x0}px;border-top:1.5px dashed {bd}"></div>')
                if dg:
                    b.raw(f'<div style="position:absolute;left:{x0+10}px;top:{dy+3}px;font:500 11.5px/16px \'JetBrains Mono\',monospace;color:#334155;white-space:nowrap">{html.escape(dg)}</div>')
        # lifelines
        for k, p in s.P.items():
            y0 = p['head_y'] + s.hh
            y1 = s.bottom
            for e in s.ends:
                if e[0] == k: y1 = e[1]
            b.raw(f'<div style="position:absolute;left:{p["x"]-0.75:g}px;top:{y0}px;height:{y1-y0}px;border-left:1.5px dashed #94A3B8"></div>')
        for k, y in s.ends:
            x = s.P[k]['x']
            b.raw(f'<svg width="22" height="22" viewBox="0 0 22 22" style="position:absolute;left:{x-11}px;top:{y-11}px;stroke:#B42318;stroke-width:3;stroke-linecap:round" aria-hidden="true"><path d="M3 3L19 19M19 3L3 19"/></svg>')
        # activations
        for key, y0, y1, lvl in s.acts:
            p = s.P[key]; bg = TONES[p['tone']][1]
            b.raw(f'<div style="position:absolute;left:{p["x"]-6+6*lvl}px;top:{y0}px;width:12px;height:{y1-y0}px;box-sizing:border-box;background:{bg};border:1.5px solid #0F172A;border-radius:2px"></div>')
        # headers
        for k, p in s.P.items():
            s.head(p)
        # messages
        for m in s.msgs:
            s.draw_msg(m)
        for x, y, w, text, h in s.notes:
            h = h or 26 + 17 * (1 + text.count('<br>'))
            b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#FFF1DD;border:1.5px solid #E0A458;border-radius:4px;clip-path:polygon(0 0,calc(100% - 14px) 0,100% 14px,100% 100%,0 100%);padding:7px 20px 7px 10px;font-size:11.5px;line-height:16px;color:#334155">{text}</div>')
            b.raw(f'<svg width="14" height="14" viewBox="0 0 14 14" style="position:absolute;left:{x+w-14}px;top:{y}px" aria-hidden="true"><path d="M0.75 0.75V13.25H13.25Z" fill="#FFE2B0" stroke="#E0A458" stroke-width="1.5" stroke-linejoin="round"/></svg>')

    def head(s, p):
        b = s.b
        bg, pill = TONES[p['tone']]
        x, y = p['x'] - s.hw / 2, p['head_y']
        if s.style == 'plain':
            ic = ''
            if p.get('icon'):
                ic = icon_svg(p['icon'], 12, (s.hh - 18) / 2, 18, '#334155')
            b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y}px;width:{s.hw}px;height:{s.hh}px;box-sizing:border-box;background:{bg};border:2px solid #0F172A;border-radius:10px">{ic}'
                  f'<div style="position:absolute;left:{34 if ic else 0}px;right:0;top:0;bottom:0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;padding:0 6px;text-align:center;line-height:15px">{html.escape(p["label"])}</div></div>')
        else:
            di = p.get('dicon') or p.get('icon'); ic = detailicon(di, 64, (s.hw - 64) / 2, 8) if di in DETAIL else ''
            b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y}px;width:{s.hw}px;height:{s.hh}px;box-sizing:border-box;background:{bg};border:2px solid #0F172A;border-radius:12px">{ic}'
                  f'<div style="position:absolute;left:0;right:0;top:78px;display:flex;justify-content:center"><div style="padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:12.5px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(p["label"])}</div></div></div>')

    def label(s, x, y, text, ic=None, num=None, color='#0F172A', bold=False):
        b = s.b
        inner = ''
        if num is not None:
            inner += f'<span style="flex:none;min-width:18px;height:18px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:700 10.5px/18px \'JetBrains Mono\',monospace;text-align:center;padding:0 3px;box-sizing:border-box">{num}</span>'
        if ic:
            inner += icon_svg(ic, 0, 0, 14, '#334155').replace('position:absolute;left:0px;top:0px', 'flex:none')
        inner += f'<span>{text}</span>'
        b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;transform:translate(-50%,-100%);display:flex;align-items:center;gap:5px;font-size:12px;line-height:16px;font-weight:{700 if bold else 500};color:{color};white-space:nowrap;padding:0 4px;background:rgba(248,250,252,0.85);border-radius:4px">{inner}</div>')

    def draw_msg(s, m):
        b = s.b
        col, dash, sw = MSG[m['role']]
        y = m['y']
        if m['kind'] == 'self':
            x0 = s.edge(m['a'], y, 1); w, h = m['w'], m['h']
            _mid[0] += 1
            mid = f'dc-arrow-head-filled-{9000+_mid[0]}'
            b.raw(f'<svg width="{w+16}" height="{h+12}" viewBox="0 0 {w+16} {h+12}" style="position:absolute;left:{x0:g}px;top:{y-6}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round">'
                  f'<defs><marker id="{mid}" orient="auto" markerWidth="5" markerHeight="5" refX="2.5" refY="2.5" overflow="visible"><path d="M0 0 L5 2.5 L0 5 Z" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/></marker></defs>'
                  f'<path d="M0 6 H{w} V{h+6} H5" marker-end="url(#{mid})"/></svg>')
            b.raw(f'<div style="position:absolute;left:{x0+w+8:g}px;top:{y+h/2-4:g}px;transform:translateY(-50%);display:flex;align-items:center;gap:5px;font-size:12px;line-height:16px;font-weight:500;white-space:nowrap">'
                  + (f'<span style="flex:none;min-width:18px;height:18px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:700 10.5px/18px \'JetBrains Mono\',monospace;text-align:center;padding:0 3px;box-sizing:border-box">{m["num"]}</span>' if m['num'] is not None else '')
                  + f'{m["label"]}</div>')
            return
        a, bb = m['a'], m['b']
        ax, bx = s.P[a]['x'], s.P[bb]['x']
        d = 1 if bx > ax else -1
        xa = m['from_x'] if m['from_x'] is not None else s.edge(a, y, d)
        if m['kind'] == 'create':
            xb = bx - d * s.hw / 2
        elif m['to_x'] is not None:
            xb = m['to_x']
        else:
            xb = s.edge(bb, y, -d)
        kind = m['kind']
        flow = m['role'] == 'main'
        head = {'sync': 'filled', 'async': 'open', 'ret': 'open', 'create': 'open', 'lost': 'dot', 'found': 'open'}.get(kind, 'filled')
        if kind == 'ret' or kind == 'create': dash = '6 5'
        if kind == 'lost': head = 'dot'
        gap = (8 if sw == 4 else 5) if head == 'filled' else 0
        x_end = xb - d * gap
        L = abs(x_end - xa)
        left = min(xa, x_end) if head != 'open' else min(xa, xb) - 2
        pad = 8
        W = abs(xb - xa) + 12
        cls = ' class="flow"' if flow else (' class="flow2"' if m['role'] == 'event' else '')
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        if m['role'] == 'event': dd = ''
        # draw in absolute-ish svg: local origin at min(xa,xb)-6
        ox = min(xa, xb) - 6
        lxa, lxb, lxe = xa - ox, xb - ox, x_end - ox
        extra, mk, mattr = '', '', ''
        if head == 'filled':
            _mid[0] += 1
            mid = f'dc-arrow-head-filled-{9000+_mid[0]}'
            hu = 4 if sw == 4 else 5
            mk = f'<defs><marker id="{mid}" orient="auto" markerWidth="{hu}" markerHeight="{hu}" refX="{hu/2}" refY="{hu/2}" overflow="visible"><path d="M0 0 L{hu} {hu/2} L0 {hu} Z" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/></marker></defs>'
            mattr = f' marker-end="url(#{mid})"'
            path = f'M {lxa:g} {pad} L {lxe:g} {pad}'
        elif head == 'open':
            path = f'M {lxa:g} {pad} L {lxb:g} {pad}'
            extra = f'<path d="M {lxb - d*10:g} {pad-5} L {lxb:g} {pad} L {lxb - d*10:g} {pad+5}" stroke-dasharray="none" style="stroke-dasharray:none"/>'
        else:  # dot
            path = f'M {lxa:g} {pad} L {lxb:g} {pad}'
            extra = f'<circle cx="{lxb:g}" cy="{pad}" r="5" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/>'
        if kind == 'found':
            extra += f'<circle cx="{lxa:g}" cy="{pad}" r="5" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/>'
        b.raw(f'<svg{cls} width="{W:g}" height="{2*pad}" viewBox="0 0 {W:g} {2*pad}" style="position:absolute;left:{ox:g}px;top:{y-pad}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round;stroke-linecap:round"{dd}>{mk}<path d="{path}"{mattr}></path></svg>'
              if not extra else
              f'<svg width="{W:g}" height="{2*pad}" viewBox="0 0 {W:g} {2*pad}" style="position:absolute;left:{ox:g}px;top:{y-pad}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round;stroke-linecap:round">'
              f'<path{cls} d="{path}"{dd}></path>{extra}</svg>')
        if m['label'] or m['num'] is not None:
            cx = (xa + xb) / 2
            s.label(cx, y - 5, m['label'], m.get('ic'), m['num'], color=('#B42318' if m['role'] == 'fail' else '#0F172A'), bold=(m['role'] == 'main'))


def save(b, hh=None):
    r = b.save(hh)
    path = ROOT + b.name + '.dc.html'
    h = open(path, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Sequence: ')
    open(path, 'w', encoding='utf-8').write(h)
    return r
