from fslib import *
import sys
def build(style, H=1560):
    name = 'Sequence_Delivery' + ('_Illustrated' if style == 'detail' else '')
    title = 'Complete flow: food delivery' + (', illustrated' if style == 'detail' else ', plain')
    W = 1500
    b = Board(name, title, W, H,
      'One order from tap to rating, across six participants. It uses every kind of message and frame: sync and return, async events, a break, par, loop, critical, a self call and a note. Blue is the happy path; rose is the failure.')
    X = [190, 420, 650, 880, 1110, 1340]
    P = [dict(key='c', label='Customer', x=X[0], icon='user', dicon='User', tone='blue'),
         dict(key='a', label='App', x=X[1], icon='phone', dicon='Mobile', tone='violet'),
         dict(key='api', label='Order API', x=X[2], icon='box', dicon='Server', tone='gray'),
         dict(key='p', label='Payment', x=X[3], icon='card', dicon='Card', tone='amber'),
         dict(key='r', label='Restaurant', x=X[4], icon='store', dicon='Restaurant', tone='green'),
         dict(key='d', label='Courier', x=X[5], icon='bike', dicon='Courier', tone='teal')]
    s = Seq(b, P, 150, H - 40, style='plain' if style != 'detail' else 'detail')
    y = 150 + s.hh + 58
    def nxt(d=52):
        nonlocal y
        r = y; y += d; return r
    FX0, FX1 = 120, 1410
    ys = {}
    s.msg('c', 'a', nxt(), 'Place order', role='main', num=1, ic='cart')
    s.msg('a', 'api', nxt(), 'POST /orders', role='main', num=2)
    s.msg('api', 'p', nxt(), 'Charge card', role='main', num=3, ic='card')
    ys['brk'] = y - 18
    y += 14
    s.msg('p', 'api', nxt(), 'Declined', kind='ret', role='fail', num='4a')
    s.msg('api', 'a', nxt(), '402', kind='ret', role='fail', num='5a')
    s.msg('a', 'c', nxt(), 'Try another card', role='fail', num='6a')
    s.frame('break', FX0, FX1, ys['brk'], y - 10, '[card declined]')
    y += 34
    s.msg('p', 'api', nxt(), 'Authorised', kind='ret', role='main', num=4)
    s.msg('api', 'a', nxt(), 'Order confirmed', kind='ret', role='main', num=5)
    s.msg('a', 'c', nxt(70), 'Show confirmation', num=6, ic='check')
    # par
    py = y - 12
    y += 22
    s.msg('api', 'r', nxt(), 'New order', role='main', num='7a', ic='doc')
    cook = y - 8
    s.selfcall('r', nxt(50), 'Cook', h=28, num='8a')
    s.msg('r', 'api', nxt(), 'Ready', kind='ret', num='9a')
    py_div = y - 12
    y += 34
    s.msg('api', 'd', nxt(), 'Find a courier', role='main', num='7b', ic='bike')
    s.msg('d', 'api', nxt(), 'Accepted', kind='ret', num='8b')
    s.frame('par', FX0, FX1, py, y - 12, '', div=[(py_div + 3, '')])
    y += 34
    s.msg('api', 'a', nxt(), 'Courier on the way', kind='async', role='event', num=10, ic='bike')
    # loop
    ly = y - 10
    y += 24
    s.msg('d', 'api', nxt(), 'Location', kind='async', role='event', num=11)
    s.msg('api', 'a', nxt(), 'Update map', kind='async', role='event', num=12, ic='pin')
    s.frame('loop', FX0, FX1, ly, y - 12, '[every 10 s while delivering]')
    y += 34
    handy = y
    s.msg('d', 'c', nxt(70), 'Hand over order', role='main', num=13, ic='box')
    # critical
    cy = y - 10
    y += 38
    s.msg('api', 'p', nxt(), 'Capture payment', role='main', num=14, ic='card')
    s.msg('p', 'api', nxt(), 'Captured', kind='ret', num=15)
    s.frame('critical', 590, 980, cy, y - 12, '[capture once]', name='critical')
    y += 34
    s.msg('api', 'a', nxt(), 'Order delivered', kind='ret', role='main', num=16)
    s.msg('a', 'c', nxt(), 'Rate your meal', num=17, ic='star')
    s.destroy('d', handy + 36)
    s.act('a', 150 + s.hh + 58 - 0, y - 20); s.act('api', 150 + s.hh + 58 + 52, y - 20)
    s.note(1250, handy + 70, 200, 'The courier leaves the diagram once the order is handed over', 60)
    s.draw()
    return b, y
if __name__ == '__main__':
    for st in ('plain', 'detail'):
        b, y = build(st)
        b, y = build(st, y + 60)
        print(save(b))
