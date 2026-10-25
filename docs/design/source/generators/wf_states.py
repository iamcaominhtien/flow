from wflib import *
W, H = 1560, 1090
b = Board('Wireframe_States', 'Wireframe states: one screen, four situations', W, H,
  'Every screen that loads data has four faces: the list itself, loading, nothing yet, and an error. Design all four, not just the first.')
PW, PH, PY = 300, 620, 200
X = [80, 460, 840, 1220 - 20]
labs = ['Normal', 'Loading', 'Empty', 'Error']
for x, l in zip(X, labs): phone(b, x, PY, PW, PH, l)
sw = PW - 32
def common(x):
    appbar(b, x + 16, PY + 36, sw, 'My orders', back=False)
    navtabs(b, x + 3, PY + PH - 78, PW - 6, ['Home', 'Search', 'Orders', 'Me'], 2, ['store', 'pin', 'cart', 'user'])
for x in X: common(x)
# normal
x0 = X[0] + 16
for i, (n, s, st, tone) in enumerate([('Pad Thai House', '2 items · $21.50', 'On the way', 'blue'), ('Green Bowl', '1 item · $12.00', 'Delivered', 'green'), ('Noodle Bar', '3 items · $30.20', 'Cancelled', 'rose')]):
    y = PY + 100 + i * 82
    listitem(b, x0, y, sw, n, s, None, 72)
    chip(b, x0 + sw - 14 - (14 + 7 * len(st)), y + 25, st, tone)
# loading
x0 = X[1] + 16
for i in range(4):
    y = PY + 100 + i * 82
    R(b, x0, y, sw, 72, '#fff', G3, 10); R(b, x0 + 12, y + 17, 38, 38, G2, G2, 19, 0); bar(b, x0 + 62, y + 22, sw * 0.45, 9, G2); bar(b, x0 + 62, y + 42, sw * 0.28, 7, G2)
b.raw(f'<svg width="44" height="44" viewBox="0 0 44 44" style="position:absolute;left:{x0+sw/2-22}px;top:{PY+PH-168}px;fill:none;stroke-linecap:round;stroke-width:4"><circle cx="22" cy="22" r="17" stroke="{G2}"/><path d="M22 5A17 17 0 0 1 39 22" stroke="{BLUE}"/></svg>')
T(b, x0, PY + PH - 116, 'Loading your orders…', 12, 600, '#64748B', w=sw, center=True)
# empty
x0 = X[2] + 16
b.raw(f'<div style="position:absolute;left:{x0+sw/2-44}px;top:{PY+130}px;width:88px;height:88px;border-radius:999px;border:3px dashed {G4}"></div>')
b.raw(icon_svg('cart', x0 + sw / 2 - 20, PY + 154, 40, G4))
T(b, x0, PY + 244, 'No orders yet', 18, 800, '#0F172A', w=sw, center=True); T(b, x0, PY + 276, 'When you order, it shows up here so you can track it.', 12.5, 500, '#64748B', w=sw, center=True, lh=18)
btn(b, x0 + 30, PY + 340, sw - 60, 'Browse restaurants', 'primary', 46)
# error
x0 = X[3] + 16
b.raw(f'<div style="position:absolute;left:{x0+sw/2-44}px;top:{PY+130}px;width:88px;height:88px;border-radius:999px;background:#FDE4E4;border:3px solid #B42318;color:#B42318;font:800 44px/82px Inter,sans-serif;text-align:center">!</div>')
T(b, x0, PY + 244, 'Something went wrong', 18, 800, '#0F172A', w=sw, center=True); T(b, x0, PY + 276, 'We could not load your orders. Check your connection and try again.', 12.5, 500, '#64748B', w=sw, center=True, lh=18)
btn(b, x0 + 30, PY + 340, sw - 60, 'Try again', 'primary', 46); btn(b, x0 + 30, PY + 398, sw - 60, 'Contact support', 'secondary', 46)
hotspot(b, x0 + sw - 70, PY + 363)
callout(b, X[0] + 16 + sw - 4, PY + 125, 1); callout(b, X[1] + 16 + 6, PY + 100, 2); callout(b, X[1] + 16 + sw / 2, PY + PH - 168, 3); callout(b, X[2] + 16 + sw / 2 - 44, PY + 130, 4); callout(b, X[2] + 16 + 30, PY + 340, 5); callout(b, X[3] + 16 + sw / 2 + 44, PY + 130, 6); callout(b, X[3] + 16 + 30, PY + 340, 7)
notes(b, 80, 880, 1400, [(1, 'Status chip', 'Colour and word, never colour alone.'), (2, 'Skeleton', 'Grey bars in the shape of the real rows, so nothing jumps when data arrives.'), (3, 'Spinner and text', 'Shown after about a second. The skeleton alone is enough before that.'),
                          (4, 'Empty icon', 'Dashed, quiet. Nothing is wrong; there is just nothing yet.'), (5, 'One action', 'Empty states offer the next useful step, not a dead end.'), (6, 'Error icon', 'Rose, solid, with an exclamation mark. Plain words, no codes.'), (7, 'Retry first', 'Retry is primary. A second route, such as support, is secondary.')], cols=4, gap=4)
print(save6(b))
