from exlib import *
W = 1500
RP = 290
Y0 = 330
ys = [Y0 + RP * i for i in range(5)]
H = ys[-1] + 160
b = Board('Explainer_Layers', 'Layered flow: how a web page reaches you', W, H, hdr=False)
banner(b, 'How a web page reaches you', 'Type an address and a few things happen in about a tenth of a second. Follow the numbers from top to bottom.', W)
bands = [('You', 'blue'), ('Finding the address', 'violet'), ('The edge', 'amber'), ('The app', 'green'), ('The data', 'teal')]
for (n, t), y in zip(bands, ys):
    band(b, 64, y - 124, W - 64, y + 124, n, t)
X1, X2, X3 = 420, 820, 1220
br = xcard(b, X1, ys[0] + 10, 'Your browser', 'You type a web address and press Enter.', 'Browser', 'blue', 1)
dn = xcard(b, X1, ys[1] + 10, 'DNS', 'Turns the name into a number, the IP address.', 'DNS', 'violet', 2)
cd = xcard(b, X1, ys[2] + 10, 'CDN', 'A copy near you. If it has the page, it answers here.', 'CDN', 'amber', 3)
lb = xcard(b, X2, ys[2] + 10, 'Load balancer', 'Otherwise it picks a server that is not busy.', 'Load balancer', 'amber', 4)
sv = xcard(b, X2, ys[3] + 10, 'Web server', 'Builds the page from the pieces it needs.', 'Server', 'green', 5)
ch = xcard(b, X3, ys[3] + 10, 'Cache', 'Remembers recent answers so it can skip the database.', 'Cache', 'green', 6)
db = xcard(b, X2, ys[4] + 10, 'Database', 'Holds the real information: products, accounts, orders.', 'Database', 'teal', 7)
g = lambda a, c: ((a.cy + a.h / 2 + c.cy - c.h / 2) / 2)
b.arrow([br.b(), dn.t()], 'main', 'asks "where is it?"', (X1 + 90, g(br, dn)))
b.arrow([dn.b(), cd.t()], 'main', 'here is the address', (X1 + 90, g(dn, cd)))
b.arrow([cd.r(), lb.l()], 'next', 'no copy', ((cd.r()[0] + lb.l()[0]) / 2, cd.cy))
b.arrow([lb.b(), sv.t()], 'main', 'sends the request', (X2 + 90, g(lb, sv)))
b.arrow([sv.r(), ch.l()], 'next', 'asks first', ((sv.r()[0] + ch.l()[0]) / 2, sv.cy))
b.arrow([sv.b(), db.t()], 'main', 'if not remembered', (X2 + 90, g(sv, db)))
b.text(1020, ys[2] - 16, 'Fast path: with a copy at the CDN, the trip ends at step 3.', size=14, color='#0F172A', weight=700, w=420, lh=20)
b.text(1020, ys[4] - 16, 'The answer travels back the same way, and the browser draws the page.', size=14, color='#0F172A', weight=700, w=420, lh=20)
b.text(700, ys[0] - 8, 'Your browser knows only the name of the site, like shop.com.', size=14, color='#0F172A', weight=700, w=640, lh=20)
b.text(700, ys[1] - 8, 'Names are for people. Computers need numbers, so this lookup comes first.', size=14, color='#0F172A', weight=700, w=640, lh=20)
print(save3(b))
