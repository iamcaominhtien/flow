from fslib import *
import sys
H = int(sys.argv[1]) if len(sys.argv) > 1 else 2100
b = Board('Sequence_Rules', 'Rules', 1280, H, hdr=False)
css = '''<style>.rc{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:20px 22px;display:flex;flex-direction:column;gap:12px;box-sizing:border-box}.rc h2{font-size:16px;font-weight:800}.rc li{font-size:13px;line-height:20px;color:#334155;margin-bottom:6px}.rc ul{padding-left:18px;margin:0}.mono{font-family:'JetBrains Mono',monospace;font-size:12px}.tbl{display:grid;gap:8px 12px;font-size:13px;line-height:20px;color:#334155;align-items:center}</style>'''
def line(kind, role='next', w=64):
    col, dash, sw = MSG[role]
    d = f' stroke-dasharray="{dash}"' if dash else ''
    head = {'sync': f'<path d="M{w-10} 6 L{w} 10 L{w-10} 14Z" fill="{col}" stroke="none"/>', 'open': f'<path d="M{w-9} 5 L{w-1} 10 L{w-9} 15" fill="none"/>'}
    h = head['sync'] if kind == 'sync' else head['open']
    ln = f'<path d="M2 10 H{w-8 if kind=="sync" else w-1}"{d}/>'
    if kind == 'lost': ln = f'<path d="M2 10 H{w-6}"/><circle cx="{w-5}" cy="10" r="4" fill="{col}" stroke="none"/>'; h = ''
    if kind == 'self': ln = f'<path d="M4 4 H40 V16 H9" fill="none"/>'; h = f'<path d="M12 12 L5 16 L12 20Z" fill="{col}" stroke="none" transform="translate(0 -2)"/>'
    return f'<svg width="{w}" height="20" viewBox="0 0 {w} 20" style="fill:none;stroke:{col};stroke-width:{sw};stroke-linecap:round">{ln}{h}</svg>'
kinds = [(line('sync'), 'Call', 'sync. Caller waits.'), (line('open', 'ret'), 'Return', 'dashed. Only when the value matters.'),
         (line('open'), 'Async', 'solid, open head. Caller carries on.'), (line('self'), 'Self call', 'loop on one lifeline.'),
         (line('lost'), 'Lost / found', 'filled dot: no receiver or no sender.'),
         (f'<svg width="64" height="20" viewBox="0 0 64 20" style="fill:none;stroke:{INK};stroke-width:2;stroke-dasharray:6 5"><path d="M2 10H44"/><path d="M36 5L44 10L36 15" stroke-dasharray="none"/><rect x="45" y="3" width="17" height="14" rx="3" style="stroke-dasharray:none;fill:#D3F3EF"/></svg>', 'Create', 'dashed into a box that appears lower.'),
         (f'<svg width="64" height="20" viewBox="0 0 64 20" style="fill:none;stroke:#B42318;stroke-width:3;stroke-linecap:round"><path d="M26 4L38 16M38 4L26 16"/></svg>', 'Destroy', 'rose cross ends the lifeline.')]
krow = ''.join(f'{a}<b>{n}</b><span>{t}</span>' for a, n, t in kinds)
roles = [('next', 'Next: ink, thin. Ordinary message.'), ('main', 'Main path: blue, thick, animated fast. One route per diagram.'), ('fail', 'Failure: rose, label in rose.'), ('event', 'Event stream: violet, thin, animated slowly.')]
rrow = ''
for r, t in roles:
    col, dash, sw = MSG[r]
    anim = {'main': 'stroke-dasharray:8 5', 'event': 'stroke-dasharray:6 6'}.get(r, '')
    rrow += f'<svg width="40" height="10" viewBox="0 0 40 10" style="fill:none;stroke:{col};stroke-width:{sw};{anim}"><path d="M0 5H40"/></svg><span>{t}</span>'
frag = [('alt', 'one branch of several, dashed divider, last is [else]'), ('opt', 'one branch that may be skipped'), ('loop', 'repeat while a guard holds'), ('par', 'branches at the same time'),
        ('break', 'leave the flow when the guard holds'), ('critical', 'an uninterrupted unit'), ('ref', 'another sequence diagram, by name')]
def tag(k):
    tint, bd, tg = FRAG[k]
    return f'<span style="display:inline-block;background:{tg};border:1.5px solid {bd};border-radius:6px 0 10px 0;font:700 11.5px/19px Inter,sans-serif;color:{bd};padding:0 10px">{k}</span>'
frow = ''.join(f'{tag(k)}<span>{t}</span>' for k, t in frag)
def card(t, inner): return f'<div class="rc"><h2>{t}</h2>{inner}</div>'
def ul(*it): return '<ul>' + ''.join(f'<li>{i}</li>' for i in it) + '</ul>'
cards = [
 card('Participants', ul('One lifeline per actor, system or object: <i>Customer</i>, <i>Order API</i>. Noun, singular, three words at most.', 'Left to right in order of first appearance. The one who starts is on the far left, databases and external services on the right.', 'Seven participants fit a page. Beyond that, move a part into a ref frame.', 'Header: <span class="mono">136 × 44</span> plain, <span class="mono">172 × 116</span> illustrated. A participant that is created later gets its header lower, on the create arrow.', 'Same icon and tone as the same actor in a flowchart lane.')),
 card('Message kinds', f'<div class="tbl" style="grid-template-columns:70px 100px 1fr">{krow}</div>' + ul('Line style says how the call behaves. The kind is stored, not the picture: a plugin draws it.')),
 card('Labels', ul('One short phrase above the line, centred. A call is written like code (<span class="mono">POST /orders</span>) or a verb phrase (<i>Charge card</i>). A return is the value: <i>Token</i>, <i>402</i>.', 'About 24 characters at most. Never wrap, never put a label across a header.', '<b>Numbers</b> are optional. Use them when other text refers to a step. A branch adds a letter: 6a, 6b.', 'An optional 14 px icon sits left of the text, from the flat set, for the payload (card, doc, pin).')),
 card('Line roles and animation', f'<div style="display:grid;grid-template-columns:auto 1fr;gap:12px 14px;align-items:center;font-size:13px;color:#334155">{rrow}</div>' + ul('Two animated tiers only. A second main path cancels the effect.', 'A return on the main path keeps its open head and takes the main colour.', 'Animation is off when the viewer prefers reduced motion. In draw.io each line has its own flow animation (flowAnimation=1) and its own duration: main route 500, event stream 1500. Checked in the draw.io viewer; SVG export not yet tested.')),
 card('Frames', f'<div class="tbl" style="grid-template-columns:90px 1fr">{frow}</div>' + ul('The tag names the kind, the guard is mono, in brackets, lower case. Dividers are dashed and carry the next guard.', 'A frame is inset 10 px inside its parent and spans only the participants it touches. Two levels at most.')),
 card('Activation bars', ul('A bar on a lifeline shows the time a participant is busy: from a call to its matching return.', 'Width 12 px, tint of the participant, 1.5 px ink border. A nested call shifts the bar 6 px to the right.', 'Messages start and end on the bar edge, not on the lifeline.', 'A plugin derives the bars from call and return pairs. Draw them only when waiting matters; a diagram of events needs none.')),
 card('Layout and spacing', ul('Time runs down. Messages never go up.', 'Participants 230 px apart (plain or illustrated). Rows 52 px apart, 70 px before a new phase, 14 px between a frame edge and its first message.', 'The first message is at least 58 px under the header.', 'A message never crosses a header. It may cross lifelines, which stay behind it.', 'About 40 rows per diagram. Longer: cut with a ref frame.')),
 card('Notes', ul('Amber, folded corner, one or two short sentences.', 'Beside a lifeline, never across a message. Use a note for a reason (<i>Passwords are compared as hashes</i>), not to repeat the label.', 'A note is not a participant. It has a position and a text only.')),
 card('Create and destroy', ul('A create arrow ends on the left edge of the new header. The lifeline starts under the header.', 'A rose cross ends a lifeline. Nothing is drawn under it, and the participant takes no later messages.', 'Use them when the object really lives and dies in the diagram: a session, a job, a courier on one order. Otherwise every lifeline runs to the bottom.')),
 card('Two styles', ul('<b>Plain:</b> a header box with a small icon. Default; for drafts and technical documents.', '<b>Illustrated:</b> a tinted card with a 64 px icon from the detailed set and a name pill. For readers outside the team.', 'Messages, frames, bars and notes are identical in both. Only the headers differ, and every y position shifts by the header height.', 'The same participant list works for both. A style is chosen per diagram.')),
 card('Reading it with other diagrams', ul('A participant can be an actor from a flowchart lane. Keep the name and the icon the same.', 'A <b>ref</b> frame can point to a flowchart or a screen flow by name. The plugin keeps the link.', 'Not decided yet: a screen thumbnail on a message, for example the screen where the tap happens.')),
 card('What a plugin can rely on', ul('A participant is: id, label, icon, tone, optional born-at row.', 'A message is: from, to, kind (sync, return, async, self, lost, found, create), role (next, main, fail, event), label, optional number and icon.', 'A frame is: kind, guard, optional dividers with guards, and the first and last row it covers. A note is: row, side, text.', 'Rows, not coordinates. The plugin spaces rows and places x from the participant order, bars from call and return pairs.', 'Anything not covered is left to the diagram author.')),
]
grid = f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px">{"".join(cards)}</div>'
b.raw(css + f'<div style="position:absolute;left:0;top:0;width:1280px;box-sizing:border-box;padding:64px;display:flex;flex-direction:column;gap:28px"><div style="display:flex;flex-direction:column;gap:8px"><div style="font-size:24px;font-weight:600">Sequence · Rules</div><div style="font-size:13px;line-height:20px;color:#475569;max-width:900px">The conventions every sequence diagram follows, and that a plugin can rely on. Message kinds and Fragments show them one by one, the examples show them together.</div></div>{grid}</div>')
print(save(b))
