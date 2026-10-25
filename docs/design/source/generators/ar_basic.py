from archlib import *
b = Board('Architecture_Basic', 'Basic architecture: a web app', 1620, 620,
  'The classic three tiers. A user reaches the app through a load balancer; the app reads from a cache first and falls back to the database. Zones show where each part lives.')
y = 330
zone(b, 380, 150, 1520, 520, 'Cloud region', 'blue')
zone(b, 1210, 190, 1490, 490, 'Private network', 'amber')
br = comp(b, 190, y, 'Browser', 'the user', 'Browser', 'gray')
lb = comp(b, 560, y, 'Load balancer', 'spreads traffic', 'Load balancer', 'violet')
wa = comp(b, 930, y, 'Web app', 'business logic', 'Server', 'blue')
ca = comp(b, 1350, 250, 'Cache', 'Redis', 'Cache', 'teal')
db = comp(b, 1350, 430, 'Database', 'PostgreSQL', 'Database', 'green')
b.arrow([br.r(), lb.l()], 'main', 'HTTPS', ((br.r()[0] + lb.l()[0]) / 2, y))
b.arrow([lb.r(), wa.l()], 'main', 'HTTP', ((lb.r()[0] + wa.l()[0]) / 2, y))
b.arrow([(wa.r()[0], y - 20), (1100, y - 20), (1100, 250), ca.l()], 'next', 'get', (1100, 290))
b.arrow([wa.r(0), (1100, y), (1100, 430), db.l()], 'main', 'SQL, on a miss', (1100, 390)) if False else None
b.arrow([(wa.r()[0], y + 20), (1130, y + 20), (1130, 430), db.l()], 'main', 'SQL', (1130, 395))
b.raw('<div style="position:absolute;left:380px;top:560px;font-size:12px;line-height:18px;color:#475569">The blue path is a request that has to reach the data. The cache line is thin because it is an optimisation, not a requirement.</div>')
print(save2(b))
