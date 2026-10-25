from dfdlib import *
b = Board('DFD_Context', 'Level 0, context: food delivery', 1900, 1150,
  'The whole system is one process. The diagram shows only what crosses its border: data in and data out, between the system and the four outside parties.')
cu = ext(b, 280, 560, 'E1', 'Customer', 'User', 'blue')
rs = ext(b, 950, 220, 'E2', 'Restaurant', 'Team', 'green', w=360)
co = ext(b, 1620, 560, 'E3', 'Courier', 'Courier', 'teal')
pp = ext(b, 950, 920, 'E4', 'Payment provider', 'Card', 'gray', w=360)
sy = proc(b, 950, 560, '0', 'Delivery system', 'takes orders, charges, dispatches', w=300, h=160)
b.arrow([(cu.r()[0], 515), (sy.l()[0], 515)], 'main', 'Basket, card details', (565, 515))
b.arrow([(sy.l()[0], 605), (cu.r()[0], 605)], 'next', 'Confirmation, tracking', (565, 605))
b.arrow([(810, rs.b()[1]), (810, sy.t()[1])], 'next', 'Order ticket', (810, 335)) if False else None
b.arrow([(800, sy.t()[1]), (800, rs.b()[1])], 'next', 'Order ticket', (800, 335))
b.arrow([(1100, rs.b()[1]), (1100, sy.t()[1])], 'next', 'Ready signal', (1100, 335))
b.arrow([(sy.r()[0], 515), (co.l()[0], 515)], 'next', 'Delivery job', (1335, 515))
b.arrow([(co.l()[0], 605), (sy.r()[0], 605)], 'next', 'Job reply, location, drop-off proof', (1335, 605))
b.arrow([(800, sy.b()[1]), (800, pp.t()[1])], 'main', 'Charge request', (800, 790))
b.arrow([(1100, pp.t()[1]), (1100, sy.b()[1])], 'main', 'Payment result', (1100, 790))
print(save10(b))
