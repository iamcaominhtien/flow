from fslib import *
b = Board('Sequence_Messages', 'Message kinds', 1480, 1190,
  'Every arrow style has one meaning. The line says how the call behaves, the colour says how much it matters. A plugin picks the style from the message kind, never by hand.')
P = [dict(key='a', label='Caller', x=200, icon='user', tone='gray'),
     dict(key='b', label='Service', x=520, icon='box', tone='blue'),
     dict(key='c', label='New object', x=800, icon='star', tone='green', born=708)]
s = Seq(b, P, 150, 1120)
ax = 960
def ann(y, name, text, uml):
    b.text(ax, y - 22, name, size=13, color='#0F172A', weight=800)
    b.text(ax, y - 4, text, size=12, color='#334155')
    b.text(ax, y + 14, uml, size=11, color='#64748B', mono=True)
rows = [
 (240, 'Synchronous call', 'Solid line, filled head. The caller waits for the answer.', 'kind: sync'),
 (316, 'Return', 'Dashed line, open head. Only drawn when the value matters.', 'kind: return'),
 (392, 'Asynchronous message', 'Solid line, open head. The caller carries on.', 'kind: async'),
]
s.act('b', 240, 336)
s.msg('a', 'b', 240, 'request(order)', kind='sync')
s.msg('b', 'a', 316, 'order id', kind='ret')
s.msg('a', 'b', 392, 'publish(event)', kind='async')
s.selfcall('b', 468, 'validate', h=30)
s.msg('a', 'a', 0, '', kind='x') if False else None
s.msg('a', 'b', 560, 'timeout', kind='lost', to_x=400)
s.msg('a', 'b', 636, 'webhook', kind='found', from_x=300)
s.msg('a', 'c', 730, 'new()', kind='create')
s.destroy('c', 840)
s.msg('a', 'b', 920, 'checkout', role='main', num=1)
s.msg('b', 'a', 996, '402 declined', kind='ret', role='fail')
s.msg('b', 'a', 1072, 'stock changed', kind='async', role='event')
rows += [
 (468, 'Self call', 'The service calls itself. The loop leaves the lifeline and returns.', 'kind: self'),
 (560, 'Lost message', 'Sent, but nobody receives it. Ends in a filled dot.', 'kind: lost'),
 (636, 'Found message', 'Comes from outside the diagram. Starts from a filled dot.', 'kind: found'),
 (730, 'Create', 'Dashed line into a box that appears lower. The lifeline starts there.', 'kind: create'),
 (840, 'Destroy', 'A rose cross ends the lifeline. Nothing is drawn below it.', 'kind: destroy'),
 (920, 'Main path', 'Blue, thick, animated. The one route that matters. Return and async keep their head.', 'role: main'),
 (996, 'Failure', 'Rose. Label in rose. The branch that goes wrong.', 'role: fail'),
 (1072, 'Event stream', 'Violet, thin, slow animation. Messages that flow without waiting.', 'role: event'),
]
s.draw()
for y, n, t, u in rows: ann(y, n, t, u)
b.text(64, 1150, 'Numbers are optional. Branches use a letter: 6a, 6b. A label is one short phrase above the line, the call written like code or a short noun.', size=12, color='#475569')
print(save(b))
