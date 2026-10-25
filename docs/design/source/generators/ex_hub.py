from exlib import *
W, H = 1400, 1360
b = Board('Explainer_Concept', 'Concept: what a cache does', W, H, hdr=False)
banner(b, 'What a cache does', 'A cache keeps a copy of what you used recently, close at hand, so you do not have to fetch it again.', W)
c = xcard(b, 700, 560, 'Cache', 'A small, fast place that holds copies.', 'Cache', 'teal', w=340, h=240)
tl = xcard(b, 250, 360, 'Fast', 'Answers in a blink, because it is near.', 'Launch', 'amber', 1, w=300, h=200)
tr = xcard(b, 1150, 360, 'Small', 'Holds only a little, so it keeps what is popular.', 'Package', 'violet', 2, w=300, h=200)
bl = xcard(b, 250, 760, 'Temporary', 'Old copies expire so they never go stale.', 'Schedule', 'blue', 3, w=300, h=200)
br = xcard(b, 1150, 760, 'A copy, not the original', 'The real data stays in the database.', 'Database', 'green', 4, w=300, h=200)
for n_, pts in ((tl, [(c.l()[0], 520), (250, 520), (250, tl.cy + 100)]), (tr, [(c.r()[0], 520), (1150, 520), (1150, tr.cy + 100)]),
                (bl, [(c.l()[0], 600), (250, 600), (250, bl.cy - 100)]), (br, [(c.r()[0], 600), (1150, 600), (1150, br.cy - 100)])):
    b.arrow(pts, 'next')
band(b, 64, 920, W - 64, 1280, 'Like a desk and a library', 'amber')
dk = xcard(b, 380, 1110, 'Your desk', 'The books you use every day are within reach.', 'Cache', 'teal', w=300, h=200)
lb = xcard(b, 1020, 1110, 'The library', 'Everything is here, but it takes a walk.', 'Folder', 'blue', w=300, h=200)
b.arrow([dk.r(), lb.l()], 'next', 'not on the desk? walk', (700, 1110))
b.text(700, 1215, '', size=1)
b.text(380, 1240, 'Same idea as the cache in a web server.', size=13, color='#334155', weight=700) if False else None
print(save3(b))
