from exlib import *
W, H = 1900, 1980
b = Board('Explainer_Payment', 'Complete explainer: paying by card online', W, H, hdr=False)
banner(b, 'What happens when you pay by card online', 'A yes or no comes back in about two seconds, but the money moves days later. Follow the numbers in A, then compare the two steps in B.', W)
TONES['rose'] = ('#FDE4E4', '#F9C2C0')
def sec(x, y, letter, title):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;display:flex;align-items:center;gap:12px"><span style="width:34px;height:34px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:800 16px/34px Inter,sans-serif;text-align:center">{letter}</span><span style="font-size:22px;font-weight:800">{html.escape(title)}</span></div>')
def mcard(cx, cy, w, h, title, desc, ic, tone, n=None):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{cx-w/2}px;top:{cy-h/2}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg}">{detailicon(ic, 56, 14, (h-56)/2)}'
          f'<div style="position:absolute;left:84px;top:12px;font-size:14px;font-weight:800;line-height:18px">{html.escape(title)}</div><div style="position:absolute;left:84px;right:12px;top:34px;font-size:12.5px;line-height:17px;color:#334155">{html.escape(desc)}</div></div>')
    if n: num(b, cx - w / 2 - 10, cy - h / 2 - 10, n)
    return Node(cx, cy, w, h)
# ---------- A: layers
sec(64, 212, 'A', 'Authorisation: a yes or no in two seconds')
ys = [410, 680, 950, 1220]
bands = [('You', 'blue'), ('The shop', 'violet'), ('The banks\' network', 'amber'), ('Your bank', 'teal')]
for (n, t), y in zip(bands, ys): band(b, 64, y - 124, 1000, y + 124, n, t)
cu = xcard(b, 380, ys[0] + 10, 'You', 'Enter the card details at checkout and press Pay.', 'User', 'blue', 1)
sh = xcard(b, 380, ys[1] + 10, 'The shop', 'Sends your order. Card details go straight to the gateway.', 'Cart', 'violet', 2)
gw = xcard(b, 760, ys[1] + 10, 'Payment gateway', 'Wraps the request in a safe, standard format.', 'Gateway', 'violet', 3)
aq = xcard(b, 760, ys[2] + 10, 'The shop\'s bank', 'Also called the acquirer. It receives the shop\'s money.', 'Money', 'amber', 4)
nw = xcard(b, 380, ys[2] + 10, 'Card network', 'Visa or Mastercard: the postman between the banks.', 'Globe', 'amber', 5)
iss = xcard(b, 380, ys[3] + 10, 'Your bank', 'Checks your money and the fraud signals, then decides.', 'Security', 'teal', 6)
ok = mcard(790, ys[3] - 25, 300, 80, 'Approved', 'The money is put on hold.', 'Success', 'green', '6a')
no = mcard(790, ys[3] + 75, 300, 80, 'Declined', 'Nothing is held. The shop is told no.', 'Error', 'rose', '6b')
g = lambda a, c: (a.cy + a.h / 2 + c.cy - c.h / 2) / 2
b.arrow([cu.b(), sh.t()], 'main', 'presses Pay', (380 + 70, g(cu, sh)))
b.arrow([sh.r(), gw.l()], 'main', 'card details', ((sh.r()[0] + gw.l()[0]) / 2, ys[1] + 10))
b.arrow([gw.b(), aq.t()], 'main', 'asks for approval', (760 + 80, g(gw, aq)))
b.arrow([aq.l(), nw.r()], 'main', 'forwards it', ((aq.l()[0] + nw.r()[0]) / 2, ys[2] + 10))
b.arrow([nw.b(), iss.t()], 'main', 'routes to your bank', (380 + 100, g(nw, iss)))
b.arrow([iss.r(), (580, iss.cy), (580, ok.cy), ok.l()], 'yes', 'yes', (580, ok.cy - 30)) if False else None
b.arrow([(iss.r()[0], ok.cy), ok.l()], 'yes', 'yes', (575, ok.cy - 16))
b.arrow([(iss.r()[0], no.cy), no.l()], 'no', 'no', (575, no.cy - 16))
b.text(80, ys[3] + 142, 'The answer travels back the same way, bank to network to bank to shop to you.', size=14, color='#0F172A', weight=700, w=900)
# ---------- B: comparison
sec(1060, 212, 'B', 'Two steps, not one')
h1 = xcard(b, 1210, 360, 'Authorisation', 'The "yes". Happens while you wait.', 'Lock', 'blue', w=250, h=200)
h2 = xcard(b, 1686, 360, 'Settlement', 'The money. Happens later.', 'Money', 'green', w=250, h=200)
b.raw('<div style="position:absolute;left:1418px;top:340px;width:60px;height:36px;border-radius:999px;background:#0F172A;color:#fff;font:800 14px/36px Inter,sans-serif;text-align:center">vs</div>')
rows = [('When', 'Right now, while you wait.', 'Later, usually the same night.'), ('What moves', 'Nothing. A hold is placed on the money.', 'The money itself, minus small fees.'),
        ('Who is involved', 'All six: you, shop, gateway, two banks, network.', 'Mostly the banks and the network.'), ('Can it be undone?', 'Yes: the hold just expires.', 'Only as a refund, which takes days.')]
for i, (lab, a, c) in enumerate(rows):
    cy = 560 + i * 104
    b.raw(f'<div style="position:absolute;left:1368px;top:{cy-17}px;width:160px;height:34px;border:2px solid #0F172A;border-radius:999px;background:#FFF1DD;box-shadow:0 3px 0 #0F172A;font:800 13px/30px Inter,sans-serif;text-align:center;white-space:nowrap;z-index:2">{lab}</div>')
    for x, txt, tone in ((1210, a, 'blue'), (1686, c, 'green')):
        bg, _ = TONES[tone]
        b.raw(f'<div style="position:absolute;left:{x-125}px;top:{cy-40}px;width:250px;height:80px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg};padding:0 16px;display:flex;align-items:center;font-size:13px;line-height:18px">{txt}</div>')
    b.raw(f'<div style="position:absolute;left:1447px;top:{cy-52}px;height:104px;border-left:1.5px dashed #94A3B8"></div>')
# ---------- C: tree
sec(1060, 1010, 'C', 'Why a payment is declined')
rt = xcard(b, 1180, 1250, 'Declined', 'The bank said no.', 'Error', 'rose', w=240, h=200)
rows = [('Not enough money', 'There is nothing to approve. Try another card.', 'Warning', 'amber'), ('Looks like fraud', 'An unusual place or amount. Call the bank to allow it.', 'Security', 'violet'), ('The bank wants proof', 'A screen asks you to confirm in your banking app (3-D Secure).', 'ID card', 'blue')]
for i, (n, d, ic, tone) in enumerate(rows):
    cy = 1130 + i * 120
    m = mcard(1618, cy, 440, 96, n, d, ic, tone)
    b.arrow([(rt.r()[0], 1250), (1340, 1250), (1340, cy), m.l()] if cy != 1250 else [(rt.r()[0], 1250), m.l()], 'next')
# ---------- D: analogy
band(b, 64, 1480, W - 64, 1860, 'Like a hotel stay', 'amber')
ci = xcard(b, 520, 1690, 'Check-in', 'The hotel holds your card as a deposit. That is authorisation.', 'Lock', 'blue', w=300, h=200)
co = xcard(b, 1380, 1690, 'Check-out', 'The hotel really charges the card. That is settlement.', 'Money', 'green', w=300, h=200)
b.arrow([ci.r(), co.l()], 'next', 'a few days later', (950, 1690))
b.text(700, 1808, 'Same idea, different clock: the promise is instant, the money is not.', size=14, color='#0F172A', weight=700, w=700)
print(save3(b))
