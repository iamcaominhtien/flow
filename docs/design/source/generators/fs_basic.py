from fslib import *
b = Board('Sequence_Basic', 'Basic sequence: sign in', 1460, 900,
  'Time runs down. Each lifeline is one participant, each arrow one message. The happy path is blue and animated; the failure branch is rose. An alt frame splits the two outcomes.')
xs = [200, 470, 740, 1010, 1260]
P = [dict(key='u', label='User', x=xs[0], icon='user', tone='gray'),
     dict(key='a', label='App', x=xs[1], icon='phone', tone='blue'),
     dict(key='api', label='API', x=xs[2], icon='box', tone='violet'),
     dict(key='au', label='Auth service', x=xs[3], icon='check', tone='amber'),
     dict(key='db', label='Database', x=xs[4], icon='doc', tone='green')]
s = Seq(b, P, 150, 868)
s.frame('alt', 150, 1330, 486, 820, '[password matches]', div=[(650, '[else]')])
s.act('a', 250, 800); s.act('api', 302, 750); s.act('au', 354, 705); s.act('db', 406, 458)
s.msg('u', 'a', 250, 'Tap Sign in', role='main', num=1)
s.msg('a', 'api', 302, 'POST /login', role='main', num=2)
s.msg('api', 'au', 354, 'Verify credentials', role='main', num=3)
s.msg('au', 'db', 406, 'Find user by email', num=4)
s.msg('db', 'au', 458, 'User record', kind='ret', num=5)
s.msg('au', 'api', 532, 'Token', kind='ret', role='main', num='6a')
s.msg('api', 'a', 578, '200 + session', kind='ret', role='main', num='7a')
s.msg('a', 'u', 624, 'Open dashboard', role='main', num='8a')
s.msg('au', 'api', 696, 'Invalid', kind='ret', role='fail', num='6b')
s.msg('api', 'a', 742, '401', kind='ret', role='fail', num='7b')
s.msg('a', 'u', 788, 'Show error', role='fail', num='8b')
s.note(1280, 330, 150, 'Passwords are compared as hashes', 60)
s.draw()
print(save(b))
