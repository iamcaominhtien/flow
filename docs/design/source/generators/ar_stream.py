from archlib import *
def build(style):
    ill = style == 'detail'
    hw, hh = (116, 48) if ill else (98, 34)
    PX, PY, x0 = (400, 310, 360) if ill else (320, 260, 330)
    Y = [250 + (30 if ill else 0) + PY * i for i in range(7)]
    P = hh + 36
    X = lambda i: x0 + PX * i
    L = X(0) - hw - 14
    RF = X(7) + hw + 112
    W, H = RF + 80, Y[-1] + P + 100
    name = 'Architecture_Streaming' + ('_Illustrated' if ill else '')
    b = Board(name, 'Complete system: video streaming platform' + (', illustrated' if ill else ', plain'), W, H,
      'A large system in seven layers. Blue is the path of one tap on Play: app, gateway, playback service, catalog, catalog database. Ink lines are calls, violet lines are events and jobs, dashed lines are reads and copies. A line from a frame edge means "from any part inside".')
    S = style
    zone(b, L, Y[0] - P, RF, Y[0] + P, 'Clients', 'blue')
    zone(b, L, Y[1] - P, RF, Y[1] + P, 'Edge', 'violet')
    zone(b, X(4) - hw - 12, Y[1] - hh - 18, X(4) + hw + 12, Y[1] + hh + 18, 'Third party', 'gray')
    zone(b, L, Y[2] - P, X(5) + hw + 72, Y[2] + P, 'Services', 'green')
    zone(b, L, Y[4] - P, X(5) + hw + 72, Y[4] + P, 'Data', 'amber')
    ax = lambda k: X(0) + PX * k   # analytics slots between columns
    zone(b, L, Y[5] - P, ax(5.5) + hw + 42, Y[5] + P, 'Analytics', 'teal')
    zone(b, L, Y[6] - P, ax(5.5) + hw + 42, Y[6] + P, 'Observability', 'gray')
    zone(b, X(6) - hw - 22, Y[2] - P, RF + 20, Y[3] + P, 'Video pipeline', 'violet')
    c = lambda *a: comp(b, *a, S)
    web = c(X(0), Y[0], 'Web player', 'browser', 'Browser', 'blue')
    mob = c(X(1), Y[0], 'Mobile app', 'iOS, Android', 'Mobile', 'blue')
    tv = c(X(2), Y[0], 'Smart TV app', 'living room', 'Laptop', 'blue')
    stu = c(X(6), Y[0], 'Creator studio', 'upload and edit', 'Laptop', 'violet')
    cdn = c(X(0), Y[1], 'CDN', 'video segments', 'CDN', 'violet')
    gw = c(X(1), Y[1], 'API gateway', 'routing, limits', 'Gateway', 'violet')
    au = c(X(2), Y[1], 'Auth', 'tokens, sessions', 'Identity (IAM)', 'gray')
    pp = c(X(4), Y[1], 'Payment provider', 'card network', 'Card', 'gray')
    ug = c(X(6), Y[1], 'Upload gateway', 'resumable uploads', 'Gateway', 'violet')
    pl = c(X(1), Y[2], 'Playback', 'manifests, licences', 'Server', 'green')
    ca = c(X(2), Y[2], 'Catalog', 'titles, metadata', 'Server', 'green')
    pr = c(X(3), Y[2], 'Profiles', 'accounts, history', 'Server', 'green')
    bi = c(X(4), Y[2], 'Billing', 'plans, invoices', 'Card', 'amber')
    se = c(X(5), Y[2], 'Search', 'queries, suggest', 'Search', 'green')
    ing = c(X(6), Y[2], 'Ingest', 'validates files', 'Server', 'violet')
    raw = c(X(7), Y[2], 'Raw uploads', 'original files', 'Bucket', 'violet')
    jq = c(X(6), Y[3], 'Job queue', 'transcode jobs', 'Queue', 'violet')
    tr = c(X(7), Y[3], 'Transcoder', 'worker containers', 'Container', 'violet')
    vl = c(X(0), Y[4], 'Video library', 'HLS segments', 'Bucket', 'violet')
    cc = c(X(1), Y[4], 'Session cache', 'Redis', 'Cache', 'green')
    cd = c(X(2), Y[4], 'Catalog DB', 'document store', 'NoSQL database', 'green')
    ud = c(X(3), Y[4], 'Profiles DB', 'PostgreSQL', 'Database', 'green')
    bd = c(X(4), Y[4], 'Billing DB', 'PostgreSQL', 'Database', 'amber')
    si = c(X(5), Y[4], 'Search index', 'inverted index', 'Table', 'green')
    es = c(ax(1.5), Y[5], 'Event stream', 'play, search, billing', 'Event stream', 'teal')
    sp = c(ax(2.5), Y[5], 'Stream processor', 'windows, joins', 'Function', 'teal')
    dl = c(ax(3.5), Y[5], 'Data lake', 'raw events', 'Data lake', 'teal')
    dw = c(ax(4.5), Y[5], 'Data warehouse', 'reports', 'Data warehouse', 'teal')
    dbd = c(ax(5.5), Y[5], 'Dashboards', 'for the business', 'Dashboard', 'teal')
    mo = c(X(1), Y[6], 'Monitoring', 'metrics, alerts', 'Monitoring', 'gray')
    lo = c(X(2), Y[6], 'Logging', 'central logs', 'Logging', 'gray')
    zb = Y[0] + P
    mid = lambda a, b_: (a + b_) / 2
    b.arrow([mob.b(), gw.t()], 'main', 'HTTPS', (mob.cx - 36, mid(mob.b()[1], gw.t()[1])))
    b.arrow([(gw.cx + 60, zb), (gw.cx + 60, gw.t()[1])], 'next', 'HTTPS, web and TV', (gw.cx + 150, mid(zb, gw.t()[1]) + 12))
    b.arrow([(cdn.cx, zb), cdn.t()], 'next', 'video segments', (cdn.cx + 70, mid(zb, cdn.t()[1]) + 12))
    b.arrow([stu.b(), ug.t()], 'next', 'upload', (stu.cx + 40, mid(stu.b()[1], ug.t()[1])))
    b.arrow([gw.r(), au.l()], 'next', 'verify token', (mid(gw.r()[0], au.l()[0]), Y[1]))
    b.arrow([ug.b(), ing.t()], 'next', 'chunks', (ug.cx + 40, mid(ug.b()[1], ing.t()[1])))
    m = mid(gw.b()[1], pl.t()[1]) + 6
    b.arrow([gw.b(), pl.t()], 'main', 'start playback', (gw.cx + 78, m + 36))
    for s_ in (ca, pr, bi, se):
        b.arrow([(gw.cx + 50, gw.b()[1]), (gw.cx + 50, m), (s_.cx, m), s_.t()], 'next')
    b.label(mid(X(2), X(3)) + 40, m, 'REST, gRPC', 'plain')
    b.arrow([pl.r(), ca.l()], 'main', 'title info', (mid(pl.r()[0], ca.l()[0]), Y[2]))
    b.arrow([(bi.cx + 60, bi.t()[1]), (bi.cx + 60, pp.b()[1])], 'next', 'charge', (bi.cx + 100, mid(pp.b()[1], m) ))
    def down(a, c_, label, role='next'):
        b.arrow([a.b(), c_.t()], role, label, (a.cx + 55, mid(a.b()[1], c_.t()[1])))
    down(pl, cc, 'sessions'); down(ca, cd, 'read', 'main'); down(pr, ud, 'accounts'); down(bi, bd, 'ledger'); down(se, si, 'query')
    b.arrow([(cdn.cx, cdn.b()[1]), (vl.cx, vl.t()[1])], 'back', 'origin fetch', (cdn.cx + 60, mid(Y[1], Y[2]) + 10))
    b.arrow([ing.r(), raw.l()], 'next', 'original', (mid(ing.r()[0], raw.l()[0]), Y[2]))
    b.arrow([ing.b(), jq.t()], 'data', 'new job', (ing.cx + 50, mid(ing.b()[1], jq.t()[1])))
    b.arrow([jq.r(), tr.l()], 'data', 'job', (mid(jq.r()[0], tr.l()[0]), Y[3]))
    b.arrow([raw.b(), tr.t()], 'back', 'read', (raw.cx + 40, mid(raw.b()[1], tr.t()[1])))
    cor = Y[4] + P + 60
    b.arrow([tr.b(), (tr.cx, cor), (vl.cx, cor), vl.b()], 'next', 'HLS segments', (mid(X(0), X(7)), cor))
    zb2 = Y[2] + P
    b.arrow([(es.cx, zb2), (es.cx, es.t()[1])], 'data', 'play and search events', (es.cx + 90, mid(Y[3], Y[4]) + 20))
    b.arrow([es.r(), sp.l()], 'data', 'events', (mid(es.r()[0], sp.l()[0]), Y[5]))
    b.arrow([sp.r(), dl.l()], 'data', 'sink', (mid(sp.r()[0], dl.l()[0]), Y[5]))
    b.arrow([dl.r(), dw.l()], 'next', 'ETL', (mid(dl.r()[0], dw.l()[0]), Y[5]))
    b.arrow([dw.r(), dbd.l()], 'next', 'SQL', (mid(dw.r()[0], dbd.l()[0]), Y[5]))
    b.text(X(3) + 40, Y[6] - 12, 'Every service sends metrics and logs here.', size=12, color='#475569')
    return b, W, H
for st in ('plain', 'detail'):
    b, W, H = build(st)
    print(save2(b), W, H)
