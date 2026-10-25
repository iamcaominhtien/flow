from erlib import *
b = Board('ER_Basic', 'Basic ER diagram: a blog', 1400, 720,
  'Each box is a table. Key badges mark the primary key, foreign keys and unique columns. A line is a relationship, read with the marks at its ends. A many-to-many link goes through a junction table.')
U = entity(b, 80, 200, 'User', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('email', 'text', 'uq'), ('created_at', 'timestamp', '')], 'blue', 'user')
P = entity(b, 560, 200, 'Post', [('id', 'uuid', 'pk'), ('author_id', 'uuid', 'fk'), ('title', 'text', ''), ('body', 'text', ''), ('published_at', 'timestamp', 'null')], 'violet', 'doc')
C = entity(b, 560, 500, 'Comment', [('id', 'uuid', 'pk'), ('post_id', 'uuid', 'fk'), ('author_id', 'uuid', 'fk'), ('body', 'text', '')], 'amber', 'bell')
PT = entity(b, 1040, 200, 'PostTag', [('post_id', 'uuid', 'pk,fk'), ('tag_id', 'uuid', 'pk,fk')], 'gray', 'box')
T = entity(b, 1040, 400, 'Tag', [('id', 'uuid', 'pk'), ('name', 'text', 'uq')], 'green', 'star')
# User 1 - 0..N Post
rel(b, hv((U.r, U.row('id')), (P.l, P.row('author_id')), 440), 'one', 'zero_many', 'writes', (380, U.row('id') - 14), main=True)
# Post 1 - 0..N Comment
rel(b, [(P.cx - 60, P.bot), (P.cx - 60, C.y)], 'one', 'zero_many', 'has', (P.cx - 60 + 28, (P.bot + C.y) / 2))
# User 1 - 0..N Comment
rel(b, [(U.cx, U.bot), (U.cx, C.row('author_id')), (C.l, C.row('author_id'))], 'one', 'zero_many', 'comments', (260, C.row('author_id') - 14))
# Post 1 - 0..N PostTag
rel(b, [(P.r, P.row('id')), (PT.l, PT.row('post_id'))], 'one', 'zero_many', 'tagged by', (920, P.row('id') - 14))
# Tag 1 - 0..N PostTag
rel(b, [(T.cx, T.y), (T.cx, PT.y + PT.h)], 'one', 'zero_many')
b.raw('<div style="position:absolute;left:1080px;top:610px;width:260px;font-size:12px;line-height:18px;color:#475569">PostTag is a junction table: its two foreign keys together form the primary key.</div>')
print(save(b))
