from pllib import *
import html as H_
TONES['rose'] = ('#FDE4E4', '#F9C2C0'); TONES['sky'] = ('#DDF1FB', '#B6DFF3')
def N(t, k=None, **f): return dict(t=t, k=k or [], **f)
RIGHT = [
 ('Product', 'Idea', '#1D4ED8', 'blue', [
   N('Customer app', [N('Browse menus', [N('Search'), N('Filters'), N('Photos')]), N('Checkout', [N('Cards', p=1), N('Wallets'), N('Promo codes')]), N('Tracking', [N('Live map', p=1, id='lm'), N('Arrival time')])]),
   N('Restaurant tools', [N('Menu editor', who='A'), N('Order screen', p=1)]),
   N('Courier app', [N('Job offers'), N('Navigation', id='nav', more=3)])]),
 ('Engineering', 'Server', '#5B4BD6', 'violet', [
   N('Platform', [N('Backend API', done=1), N('Event bus', [N('Order events', id='oe'), N('Courier events', id='ce')]), N('Data store', more=4)]),
   N('Quality', [N('Tests', [N('Unit'), N('End to end')]), N('Monitoring', [N('Alerts'), N('Dashboards')])]),
   N('Security', [N('Login', done=1), N('Data protection', p=2)])]),
 ('Operations', 'Courier', '#0F766E', 'teal', [
   N('Couriers', [N('Recruit', who='L'), N('Train'), N('Pay')]),
   N('Restaurants', [N('Sign up', who='M'), N('Onboard')]),
   N('Support', [N('Help desk'), N('Refunds', p=2)])])]
LEFT = [
 ('Marketing', 'Flag', '#D97706', 'amber', [
   N('Launch', [N('Opening offer', p=1), N('Press kit', done=1)]),
   N('Channels', [N('Social media', [N('Posts'), N('Ads')]), N('Email'), N('Referrals', p=2)])]),
 ('Money and law', 'Money', '#15803D', 'green', [
   N('Licences', [N('Business licence', done=1), N('Food safety', p=1)]),
   N('Finance', [N('Budget'), N('Pricing', [N('Delivery fee'), N('Commission')]), N('Payouts', id='po')]),
   N('Legal', [N('Terms'), N('Privacy'), N('Insurance')])]),
 ('People', 'Team', '#B42318', 'rose', [
   N('Hiring', [N('Engineers', who='S'), N('Support agents')]),
   N('Culture', [N('Rituals'), N('Handbook')])]),
 ('Partners', 'Cloud', '#0369A1', 'sky', [
   N('Payments', [N('Card provider', p=1, id='cp')]),
   N('Maps', [N('Routing'), N('Geocoding')]),
   N('Messaging', [N('SMS'), N('Push')])])]
W = 2840
cx = W // 2
SL4, SL3, GG, BG = 40, 44, 16, 60
def slots(n):
    if not n['k']: return SL3
    return sum(slots(c) for c in n['k'])
# layout per side
def layout(branches):
    y = 0
    for (name, ic, col, tone, groups) in branches:
        by0 = y
        for g in groups:
            g0 = y
            for leaf in g['k']:
                h = SL4 * max(1, len(leaf['k'])) if leaf['k'] else SL3
                leaf['y'] = y + h / 2
                for i, s in enumerate(leaf['k']): s['y'] = y + SL4 * i + SL4 / 2
                y += h
            g['y'] = (g['k'][0]['y'] + g['k'][-1]['y']) / 2
            y += GG
        y -= GG
        branches_y.append(0)
        y += BG
    return y - BG
def assign(branches):
    tot = layout_side(branches)
    return tot
def layout_side(branches):
    y = 0
    for br in branches:
        groups = br[4]
        for g in groups:
            for leaf in g['k']:
                h = SL4 * len(leaf['k']) if leaf['k'] else SL3
                leaf['y'] = y + h / 2
                for i, s in enumerate(leaf['k']): s['y'] = y + SL4 * i + SL4 / 2
                y += h
            g['y'] = (g['k'][0]['y'] + g['k'][-1]['y']) / 2
            y += GG
        y -= GG
        br_y = (groups[0]['y'] + groups[-1]['y']) / 2
        br_dict[br[0]] = br_y
        y += BG
    return y - BG
br_dict = {}
hr = layout_side(RIGHT); hl = layout_side(LEFT)
top = 330
Hh = top + max(hr, hl) + 140
CYY = top + max(hr, hl) / 2
oy = {1: CYY - hr / 2, -1: CYY - hl / 2}
b = Board('Planning_Mind_Large', 'Mind map: starting a food delivery company', W, int(Hh),
  'Four levels, seven branches. Colour follows the branch, P1 and P2 mark priority, a check means done, a circle is the owner, +N hides more ideas, dashed arcs link ideas on different branches.')
# legend
lx = 64; ly = 178
def lg_pill(x, t, bgc, fg): 
    b.raw(f'<div style="position:absolute;left:{x}px;top:{ly}px;height:22px;padding:0 9px;border-radius:999px;background:{bgc};color:{fg};font:800 11px/22px Inter,sans-serif">{t}</div>')
lg_pill(lx, 'P1', '#FDE4E4', '#B42318'); b.text(lx + 36, ly + 2, 'Do first', size=12, color='#334155')
lg_pill(lx + 130, 'P2', '#FFE2B0', '#92400E'); b.text(lx + 166, ly + 2, 'Do next', size=12, color='#334155')
b.raw(f'<svg width="22" height="22" viewBox="0 0 22 22" style="position:absolute;left:{lx+260}px;top:{ly}px"><circle cx="11" cy="11" r="10" fill="#15803D"/><path d="M6 11.5L9.5 15L16 7.5" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'); b.text(lx + 290, ly + 2, 'Done', size=12, color='#334155')
lg_pill(lx + 360, '+4', '#0F172A', '#fff'); b.text(lx + 398, ly + 2, 'More ideas hidden', size=12, color='#334155')
avatar(b, lx + 560, ly - 2, 'K', 'green', 26); b.text(lx + 594, ly + 2, 'Owner', size=12, color='#334155')
b.raw(f'<svg width="50" height="22" style="position:absolute;left:{lx+680}px;top:{ly}px;fill:none;stroke:#7C3AED;stroke-width:2.5;stroke-dasharray="5 5"><path d="M2 11H48" stroke-dasharray="6 5"/></svg>'); b.text(lx + 740, ly + 2, 'Link between branches', size=12, color='#334155')
# geometry
W1, H1, W2, H2, W3, H3, W4, H4 = 230, 66, 200, 40, 210, 40, 176, 34
O1 = 470
def x_edges(side):
    c1 = cx + side * O1
    in1 = c1 - side * W1 / 2; out1 = c1 + side * W1 / 2
    in2 = out1 + side * 60; out2 = in2 + side * W2
    in3 = out2 + side * 56; out3 = in3 + side * W3
    in4 = out3 + side * 46; out4 = in4 + side * W4
    return c1, out1, in2, out2, in3, out3, in4, out4
def curve(x0, y0, x1, y1, col, sw, dash=None):
    mx = (x0 + x1) / 2
    lx, ty = min(x0, x1) - 10, min(y0, y1) - 10
    da = f' stroke-dasharray="{dash}"' if dash else ''
    b.raw(f'<svg width="{abs(x1-x0)+20}" height="{abs(y1-y0)+20}" style="position:absolute;left:{lx}px;top:{ty}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linecap:round"><path d="M {x0-lx} {y0-ty} C {mx-lx} {y0-ty}, {mx-lx} {y1-ty}, {x1-lx} {y1-ty}"{da}/></svg>')
pos = {}
def box(x, y, w, h, cls_style, inner):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y-h/2}px;width:{w}px;height:{h}px;box-sizing:border-box;{cls_style}">{inner}</div>')
def markers(n, col):
    out = ''
    if n.get('more'): out += f'<span style="height:20px;padding:0 8px;border-radius:999px;background:#0F172A;color:#fff;font:800 11px/20px Inter,sans-serif">+{n["more"]}</span>'
    if n.get('p'): out += f'<span style="height:20px;padding:0 8px;border-radius:999px;background:{"#FDE4E4" if n["p"]==1 else "#FFE2B0"};color:{"#B42318" if n["p"]==1 else "#92400E"};font:800 11px/20px Inter,sans-serif">P{n["p"]}</span>'
    if n.get('done'): out += '<svg width="20" height="20" viewBox="0 0 22 22"><circle cx="11" cy="11" r="10" fill="#15803D"/><path d="M6 11.5L9.5 15L16 7.5" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    if n.get('who'):
        out += f'<span style="width:22px;height:22px;border-radius:999px;background:{TONES[{"A":"violet","L":"teal","M":"amber","S":"green","K":"green"}[n["who"]]][1]};border:2px solid #0F172A;box-sizing:border-box;font:800 9.5px/18px Inter,sans-serif;text-align:center">{n["who"]}</span>'
    return f'<span style="margin-left:auto;display:flex;gap:4px;align-items:center">{out}</span>' if out else ''
for side, branches in ((1, RIGHT), (-1, LEFT)):
    c1, out1, in2, out2, in3, out3, in4, out4 = x_edges(side)
    for (name, ic, col, tone, groups) in branches:
        by = oy[side] + br_dict[name]
        curve(cx + side * 190, CYY, out1 - side * W1, by, col, 9) if False else curve(cx + side * 190, CYY, c1 - side * W1 / 2, by, col, 9)
        for g in groups:
            gy = oy[side] + g['y']
            curve(c1 + side * W1 / 2, by, in2, gy, col, 5)
            for leaf in g['k']:
                ly_ = oy[side] + leaf['y']
                curve(out2, gy, in3, ly_, col, 3.5)
                for s in leaf['k']:
                    sy = oy[side] + s['y']
                    curve(out3, ly_, in4, sy, col, 2.5)
                    s['_y'] = sy
                leaf['_y'] = ly_
            g['_y'] = gy
# nodes
for side, branches in ((1, RIGHT), (-1, LEFT)):
    c1, out1, in2, out2, in3, out3, in4, out4 = x_edges(side)
    for (name, ic, col, tone, groups) in branches:
        by = oy[side] + br_dict[name]
        bgc, pill = TONES[tone]
        box(c1 - W1 / 2, by, W1, H1, f'border:3px solid #0F172A;border-radius:22px;background:{col};box-shadow:0 4px 0 #0F172A',
            f'<div style="position:absolute;left:8px;top:{(H1-6-52)/2}px;width:52px;height:52px;border-radius:999px;background:#fff;border:2px solid #0F172A;box-sizing:border-box">{detailicon(ic, 40, 4, 4)}</div><div style="position:absolute;left:70px;right:10px;top:0;height:{H1-6}px;display:flex;align-items:center;font-size:17px;font-weight:800;color:#fff">{name}</div>')
        for g in groups:
            lx2 = in2 if side > 0 else out2
            box(lx2, g['_y'], W2, H2, f'border:2px solid {col};border-radius:999px;background:{bgc};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800', g['t'])
            for leaf in g['k']:
                lx3 = in3 if side > 0 else out3
                box(lx3, leaf['_y'], W3, H3, f'border:2px solid {col};border-left:7px solid {col};border-radius:12px;background:#fff;display:flex;align-items:center;gap:6px;padding:0 10px;font-size:13.5px;font-weight:600',
                    f'<span style="white-space:nowrap">{H_.escape(leaf["t"])}</span>' + markers(leaf, col))
                if leaf.get('id'): pos[leaf['id']] = (side, leaf['_y'], out3 if side > 0 else out3)
                for s in leaf['k']:
                    lx4 = in4 if side > 0 else out4
                    box(lx4, s['_y'], W4, H4, f'border-radius:10px;background:{bgc};border:1.5px solid {pill};display:flex;align-items:center;gap:6px;padding:0 10px;font-size:12.5px;font-weight:600',
                        f'<span style="white-space:nowrap">{H_.escape(s["t"])}</span>' + markers(s, col))
                    if s.get('id'): pos[s['id']] = (side, s['_y'], out4)
                    s.pop('_y', None)
# centre
bg, pill = TONES['amber']
b.raw(f'<div style="position:absolute;left:{cx-190}px;top:{CYY-130}px;width:380px;height:260px;box-sizing:border-box;border:3px solid #0F172A;border-radius:24px;background:{bg}">{detailicon("Launch", 112, 134, 16)}'
      f'<div style="position:absolute;left:0;right:0;top:150px;display:flex;justify-content:center"><div style="padding:6px 18px;border:3px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 4px 0 #0F172A;font-size:19px;font-weight:800;line-height:24px">Start a delivery company</div></div>'
      f'<div style="position:absolute;left:0;right:0;top:208px;text-align:center;font-size:13px;color:#475569">Goal: 1,000 orders a day in a year</div></div>')
# cross links (dashed arcs outside)
def arc(a, c, label, color='#7C3AED'):
    sa, ya, xa = pos[a]; sc, yc, xc = pos[c]
    out = max(xa, xc) + 36 if sa > 0 else min(xa, xc) - 36
    mx = out
    x0, y0, x1, y1 = xa, ya, xc, yc
    lxm, tym = min(x0, x1, out) - 12, min(y0, y1) - 12
    wdt = max(x0, x1, out) - lxm + 12; hgt = abs(y1 - y0) + 24
    b.raw(f'<svg width="{wdt}" height="{hgt}" style="position:absolute;left:{lxm}px;top:{tym}px;overflow:visible;fill:none;stroke:{color};stroke-width:2.5;stroke-dasharray:6 5;stroke-linecap:round"><path d="M {x0-lxm} {y0-tym} C {out-lxm} {y0-tym}, {out-lxm} {y1-tym}, {x1-lxm} {y1-tym}"/></svg>')
    b.label(out, (y0 + y1) / 2, label, 'plain')
arc('lm', 'oe', 'needs'); arc('nav', 'ce', 'needs'); arc('po', 'cp', 'uses')
print(save4(b), W)
