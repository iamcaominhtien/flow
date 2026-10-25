from archlib import *
CW_, CH_, GX, GY = 640, 360, 32, 28
b = Board('Architecture_Patterns', 'Patterns: common building blocks', 1400, 130 + 3 * (CH_ + GY) + 40,
  'Six arrangements that appear in most systems. Each one answers a question: how to protect, decouple, speed up, scale or fan out.')
SW, SH = 150, 60
def cell(i, title, desc):
    col, row = i % 2, i // 2
    x0, y0 = 64 + col * (CW_ + GX), 130 + row * (CH_ + GY)
    b.raw(f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{CW_}px;height:{CH_}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x0 + 22, y0 + 16, title, size=16, color='#0F172A', weight=800)
    b.text(x0 + 22, y0 + 40, desc, size=12, color='#475569')
    return x0, y0
def c(x, y, n, s, ic, tone): return comp(b, x, y, n, s, ic, tone, w=SW, h=SH)
def cap(x0, y0, t): b.text(x0 + 22, y0 + CH_ - 44, t, size=12, color='#334155', w=CW_ - 44, lh=18)
# 1 gateway
x0, y0 = cell(0, 'API gateway', 'One front door in front of many services.')
cl = c(x0 + 100, y0 + 190, 'Client', 'app or web', 'Mobile', 'blue'); gw = c(x0 + 320, y0 + 190, 'Gateway', 'routes, limits', 'Gateway', 'violet')
s1 = c(x0 + 540, y0 + 130, 'Orders', 'service', 'Server', 'green'); s2 = c(x0 + 540, y0 + 250, 'Users', 'service', 'Server', 'green')
b.arrow([cl.r(), gw.l()], 'main', None); b.arrow([gw.r(), (x0 + 435, y0 + 190), (x0 + 435, y0 + 130), s1.l()], 'next'); b.arrow([gw.r(), (x0 + 435, y0 + 190), (x0 + 435, y0 + 250), s2.l()], 'next')
cap(x0, y0, 'Authentication, rate limits and routing live in one place instead of in every service.')
# 2 queue
x0, y0 = cell(1, 'Queue and worker', 'Accept fast, do the slow part later.')
a = c(x0 + 100, y0 + 190, 'API', 'accepts jobs', 'Server', 'blue'); q = c(x0 + 320, y0 + 190, 'Queue', 'holds jobs', 'Queue', 'amber'); w = c(x0 + 540, y0 + 190, 'Worker', 'runs jobs', 'Function', 'green')
b.arrow([a.r(), q.l()], 'data', None); b.arrow([q.r(), w.l()], 'data', None)
cap(x0, y0, 'The caller does not wait. A burst of requests fills the queue instead of overloading the worker.')
# 3 cache-aside
x0, y0 = cell(2, 'Cache-aside', 'Ask the cache first, the database second.')
ap = c(x0 + 130, y0 + 190, 'App', 'reads data', 'Server', 'blue'); ca = c(x0 + 500, y0 + 140, 'Cache', 'fast, small', 'Cache', 'teal'); db = c(x0 + 500, y0 + 250, 'Database', 'source of truth', 'Database', 'green')
b.arrow([(ap.r()[0], y0 + 175), (x0 + 330, y0 + 175), (x0 + 330, y0 + 140), ca.l()], 'next', 'get', (x0 + 330, y0 + 155)); b.arrow([(ap.r()[0], y0 + 205), (x0 + 330, y0 + 205), (x0 + 330, y0 + 250), db.l()], 'main', 'on a miss', (x0 + 330, y0 + 228))
cap(x0, y0, 'Most reads end at the cache. Only a miss reaches the database, and then fills the cache.')
# 4 cdn
x0, y0 = cell(3, 'CDN in front of an origin', 'Serve static files from the edge.')
br = c(x0 + 100, y0 + 190, 'Browser', 'the user', 'Browser', 'gray'); cd = c(x0 + 320, y0 + 190, 'CDN', 'edge copies', 'CDN', 'violet'); bk = c(x0 + 540, y0 + 190, 'Storage', 'origin files', 'Bucket', 'amber')
b.arrow([br.r(), cd.l()], 'main', None); b.arrow([cd.r(), bk.l()], 'next', 'miss', (x0 + 435, y0 + 190 - 0))
cap(x0, y0, 'Images and scripts come from the nearest copy. The origin is only asked when the CDN has none.')
# 5 pubsub
x0, y0 = cell(4, 'Publish and subscribe', 'One event, many listeners.')
pu = c(x0 + 100, y0 + 190, 'Orders', 'publishes', 'Server', 'blue'); bu = c(x0 + 320, y0 + 190, 'Event bus', 'topic', 'Event stream', 'amber')
s = [c(x0 + 540, y0 + 120, 'Email', 'subscriber', 'Email', 'green'), c(x0 + 540, y0 + 190, 'Billing', 'subscriber', 'Card', 'green'), c(x0 + 540, y0 + 260, 'Analytics', 'subscriber', 'Bar chart', 'green')]
b.arrow([pu.r(), bu.l()], 'data', None)
for n in s: b.arrow([bu.r(), (x0 + 435, y0 + 190), (x0 + 435, n.cy), n.l()] if n.cy != y0 + 190 else [bu.r(), n.l()], 'data')
cap(x0, y0, 'The publisher does not know who listens. Adding a subscriber changes nothing else.')
# 6 replica
x0, y0 = cell(5, 'Read replica', 'Write to one copy, read from another.')
ap = c(x0 + 130, y0 + 190, 'App', 'reads and writes', 'Server', 'blue'); pr = c(x0 + 500, y0 + 130, 'Primary', 'writes', 'Database', 'green'); rp = c(x0 + 500, y0 + 260, 'Replica', 'reads', 'Database', 'teal')
b.arrow([(ap.r()[0], y0 + 175), (x0 + 330, y0 + 175), (x0 + 330, y0 + 130), pr.l()], 'main', 'write', (x0 + 330, y0 + 150)); b.arrow([(ap.r()[0], y0 + 205), (x0 + 330, y0 + 205), (x0 + 330, y0 + 260), rp.l()], 'next', 'read', (x0 + 330, y0 + 232))
b.arrow([pr.b(), rp.t()], 'back', 'copies', (x0 + 500 + 44, y0 + 195))
cap(x0, y0, 'Reads scale by adding replicas. A replica may lag a little behind the primary.')
print(save2(b))
