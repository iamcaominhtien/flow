from fcdetail import *
names=list(D)
html='<body style="background:#fff;margin:0;font-family:sans-serif">'+''.join(f'<div style="display:inline-block;width:150px;height:170px;position:relative">{detail(n,120,15,5)}<div style="position:absolute;top:135px;width:150px;text-align:center;font-size:12px">{n}</div></div>' for n in names)
html+='<div style="padding:10px">'+''.join(detail(n,56,0,0,False)+' ' for n in names)+'</div>'
open('/path/to/work/shots/dtest.html','w').write(html)
