# Data flow diagram builder (Gane-Sarson style) on top of archlib
import html
from archlib import *
def ext(b, cx, cy, eid, name, icon, tone, w=240, h=80):
    """External entity: square-cornered box, someone or something outside the system."""
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:3px;background:{bg}">'
          + bigicon(icon, 34, 14, (h - 34) / 2 - 2)
          + f'<div style="position:absolute;left:62px;right:8px;top:0;height:{h-4}px;display:flex;flex-direction:column;justify-content:center"><div style="font-size:11px;font-family:\'JetBrains Mono\',monospace;color:#475569">{eid}</div><div style="font-size:14px;font-weight:800;line-height:18px">{html.escape(name)}</div></div></div>')
    return Node(cx, cy, w, h)
def proc(b, cx, cy, pid, name, desc, tone='violet', w=260, h=124):
    """Process: rounded box with its number in a header strip."""
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg};overflow:hidden">'
          f'<div style="height:28px;border-bottom:2px solid #0F172A;background:{pill};padding:0 12px;font:700 12px/26px \'JetBrains Mono\',monospace">{pid}</div>'
          f'<div style="padding:8px 14px 0"><div style="font-size:14px;font-weight:800;line-height:18px;text-align:center">{html.escape(name)}</div><div style="font-size:11.5px;line-height:15px;color:#475569;text-align:center;margin-top:4px">{html.escape(desc)}</div></div></div>')
    return Node(cx, cy, w, h)
def store(b, cx, cy, sid, name, tone='amber', w=260, h=64, ghost=False):
    """Data store: open on the right. The id sits in the left cell. ghost = shown for reference, belongs to another level."""
    bg, pill = TONES[tone]
    st = 'dashed' if ghost else 'solid'
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px {st} #0F172A;border-right:none;background:{bg};display:flex;align-items:center">'
          f'<div style="width:52px;height:100%;border-right:2px {st} #0F172A;display:flex;align-items:center;justify-content:center;font:700 12px \'JetBrains Mono\',monospace;background:{pill}">{sid}</div>'
          f'<div style="padding:0 14px;font-size:14px;font-weight:800">{html.escape(name)}</div></div>')
    return Node(cx, cy, w, h)
def save10(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>DFD: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
# ---- illustrated variants: name pill + large detailed icon, same ids, lines and labels ----
def ext_d(b, cx, cy, eid, name, dicon, tone, w=280, h=120):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:3px;background:{bg}">'
          f'<div style="position:absolute;left:14px;top:16px;padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:13px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(name)}</div>'
          f'<div style="position:absolute;left:16px;top:62px;font:700 12px \'JetBrains Mono\',monospace;color:#475569">{eid}</div>'
          + detailicon(dicon, 76, w - 92, (h - 76) / 2 - 2) + '</div>')
    return Node(cx, cy, w, h)
def proc_d(b, cx, cy, pid, name, desc, dicon, tone='violet', w=300, h=170):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg};overflow:hidden">'
          f'<div style="height:28px;border-bottom:2px solid #0F172A;background:{pill};padding:0 12px;font:700 12px/26px \'JetBrains Mono\',monospace">{pid}</div>'
          f'<div style="position:absolute;left:14px;top:42px;padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:13px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(name)}</div>'
          f'<div style="position:absolute;left:14px;top:88px;width:{w-118}px;font-size:11.5px;line-height:15px;color:#334155">{html.escape(desc)}</div>'
          + detailicon(dicon, 80, w - 96, 60) + '</div>')
    return Node(cx, cy, w, h)
def store_d(b, cx, cy, sid, name, dicon, tone='amber', w=340, h=96, ghost=False):
    bg, pill = TONES[tone]
    st = 'dashed' if ghost else 'solid'
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px {st} #0F172A;border-right:none;background:{bg};display:flex;align-items:center">'
          f'<div style="width:52px;height:100%;border-right:2px {st} #0F172A;display:flex;align-items:center;justify-content:center;font:700 12px \'JetBrains Mono\',monospace;background:{pill}">{sid}</div>'
          f'<div style="padding:0 14px;font-size:14px;font-weight:800">{html.escape(name)}</div>'
          + detailicon(dicon, 64, w - 84, (h - 64) / 2 - 2) + '</div>')
    return Node(cx, cy, w, h)
