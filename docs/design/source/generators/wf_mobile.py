from wflib import *
W, H = 1520, 1180
b = Board('Wireframe_Mobile', 'Annotated wireframe: checkout on a phone', W, H,
  'Three screens of one task, in grey with blue for the primary action. Numbers point at details, the red dot is the tap target, and the notes below say what each detail does.')
PW, PH, PY = 330, 680, 200
X = [100, 590, 1080]
for x, lab in zip(X, ['1 · Cart', '2 · Address and payment', '3 · Confirmation']): phone(b, x, PY, PW, PH, lab)
sx = lambda i: X[i] + 16
sw = PW - 32
# --- screen 1 cart
x0 = sx(0); appbar(b, x0, PY + 36, sw, 'Your order')
for i, (n, s, p) in enumerate([('Pad thai', 'No peanuts', '$9.50'), ('Spring rolls', 'x2', '$6.00'), ('Iced tea', 'Large', '$3.50')]):
    y = PY + 100 + i * 78
    R(b, x0, y, sw, 68, '#fff', G3, 10)
    img(b, x0 + 10, y + 10, 48, 48, 8)
    T(b, x0 + 68, y + 12, n, 13, 700, '#0F172A'); T(b, x0 + 68, y + 32, s, 11, 500, '#64748B')
    T(b, x0 + sw - 62, y + 12, p, 13, 700, '#0F172A')
    R(b, x0 + sw - 96, y + 38, 84, 22, '#fff', G4, 11); T(b, x0 + sw - 90, y + 40, '−', 14, 800, '#334155'); T(b, x0 + sw - 62, y + 41, '1', 12, 700, '#0F172A', w=20, center=True); T(b, x0 + sw - 28, y + 40, '+', 14, 800, '#334155')
field(b, x0, PY + 346, sw - 90, 'Promo code', '', False)
btn(b, x0 + sw - 80, PY + 364, 80, 'Apply', 'secondary', 38)
for i, (k, v) in enumerate([('Subtotal', '$19.00'), ('Delivery', '$2.50'), ('Total', '$21.50')]):
    y = PY + 440 + i * 26
    T(b, x0 + 4, y, k, 13, 700 if i == 2 else 500, '#0F172A'); T(b, x0 + sw - 70, y, v, 13, 800 if i == 2 else 600, '#0F172A', w=66, center=False)
btn(b, x0, PY + PH - 112, sw, 'Checkout · $21.50', 'primary', 48)
hotspot(b, x0 + sw * 0.78, PY + PH - 88)
callout(b, x0 + sw - 114, PY + 149, 1); callout(b, x0 + sw - 68, PY + 104, 2); callout(b, x0 + 120, PY + 346, 3); callout(b, x0 + sw - 6, PY + PH - 112, 4)
# --- screen 2 address and payment
x0 = sx(1); appbar(b, x0, PY + 36, sw, 'Checkout')
T(b, x0 + 2, PY + 100, 'Deliver to', 12, 800, '#0F172A')
R(b, x0, PY + 122, sw, 66, '#fff', G3, 10); icon_dot(b, x0 + 12, PY + 136, 38, 'pin'); T(b, x0 + 62, PY + 138, 'Home', 13, 700, '#0F172A'); T(b, x0 + 62, PY + 158, '12 Garden Street, flat 4', 11, 500, '#64748B'); T(b, x0 + sw - 60, PY + 146, 'Change', 12, 700, BLUE)
T(b, x0 + 2, PY + 206, 'When', 12, 800, '#0F172A')
for i, (t_, on, w_, xx_) in enumerate([('ASAP', True, 70, 0), ('In 30 min', False, 92, 78), ('Schedule', False, 92, 178)]):
    R(b, x0 + xx_, PY + 228, w_, 32, '#DCEEFB' if on else '#fff', BLUE if on else G4, 16, 2 if on else 1.5); T(b, x0 + xx_, PY + 235, t_, 11.5, 700, BLUE if on else '#334155', w=w_, center=True)
T(b, x0 + 2, PY + 282, 'Pay with', 12, 800, '#0F172A')
for i, (t, s, on) in enumerate([('Card', '•••• 4242', True), ('Wallet', 'Balance $12.00', False), ('Cash', 'Pay the courier', False)]):
    y = PY + 304 + i * 66
    R(b, x0, y, sw, 56, '#fff', BLUE if on else G3, 10, 2 if on else 1.5)
    R(b, x0 + 14, y + 19, 18, 18, '#fff', BLUE if on else G4, 9, 2)
    if on: R(b, x0 + 19, y + 24, 8, 8, BLUE, BLUE, 4, 0)
    T(b, x0 + 46, y + 10, t, 13, 700, '#0F172A'); T(b, x0 + 46, y + 30, s, 11, 500, '#64748B')
btn(b, x0, PY + PH - 112, sw, 'Place order · $21.50', 'primary', 48)
hotspot(b, x0 + sw * 0.84, PY + PH - 88)
callout(b, x0 + sw - 12, PY + 122, 5); callout(b, x0 - 2, PY + 226, 6); callout(b, x0 + sw - 8, PY + 304, 7); callout(b, x0 + sw - 6, PY + PH - 112, 8)
# --- screen 3 confirmation
x0 = sx(2)
b.raw(f'<div style="position:absolute;left:{x0+sw/2-34}px;top:{PY+70}px;width:68px;height:68px;border-radius:999px;background:#DCF5E1;border:2px solid #15803D"></div>')
b.raw(f'<svg width="34" height="34" viewBox="0 0 24 24" style="position:absolute;left:{x0+sw/2-17}px;top:{PY+87}px;fill:none;stroke:#15803D;stroke-width:3;stroke-linecap:round;stroke-linejoin:round"><path d="M5 12.5L10 17.5L19 7"/></svg>')
T(b, x0, PY + 150, 'Order placed', 20, 800, '#0F172A', w=sw, center=True); T(b, x0, PY + 180, 'Pad Thai House is preparing it', 12, 500, '#64748B', w=sw, center=True)
R(b, x0, PY + 214, sw, 120, '#fff', G3, 12); img(b, x0 + 10, PY + 224, sw - 20, 64, 8); T(b, x0 + 14, PY + 298, 'Arriving in', 11, 500, '#64748B'); T(b, x0 + 14 + 70, PY + 295, '25 to 35 min', 15, 800, '#0F172A')
listitem(b, x0, PY + 350, sw, 'Mai will deliver it', 'Bike · arrives 11:02', None, 64)
btn(b, x0, PY + PH - 170, sw, 'Track order', 'primary', 48); btn(b, x0, PY + PH - 112, sw, 'Done', 'secondary', 48)
callout(b, x0 + sw/2 - 36, PY + 74, 9); callout(b, x0 + sw - 8, PY + 224, 10); callout(b, x0 + sw - 8, PY + 350, 11); callout(b, x0 + sw - 6, PY + PH - 170, 12)
notes(b, 100, 920, 1300, [
 (1, 'Quantity stepper', 'Changes the line and the total at once. Down to 0 removes the item.'), (2, 'Price per line', 'Shows the price for the quantity chosen, not per unit.'),
 (3, 'Promo code', 'Field and button on one row. Wrong code shows a rose message below.'), (4, 'Primary action', 'One per screen, at the bottom, with the total in the label.'),
 (5, 'Address', 'Saved address first; Change opens a list in a bottom sheet.'), (6, 'Delivery time', 'One choice at a time. Schedule opens a date picker.'),
 (7, 'Payment', 'Selected method has a blue border. Cash hides the card fields.'), (8, 'Place order', 'Disabled until address and payment are set.'),
 (9, 'Success mark', 'Green check; no auto-redirect, so the person can read it.'), (10, 'Live ETA', 'Map and time range update as the courier moves.'),
 (11, 'Courier', 'Name, vehicle and arrival time. Tap opens the courier screen.'), (12, 'Next step', 'Track order is the main action, Done the quiet exit.')], cols=3, gap=4)
print(save6(b))
