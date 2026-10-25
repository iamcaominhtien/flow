const { chromium } = require('playwright'); const root='/path/to/work/shots/';
(async()=>{const [name,x,y,w,h]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:3800,height:2500}});
await p.goto('file://'+root+name+'.html');await p.screenshot({path:root+name+'_'+x+'_'+y+'.png',clip:{x:+x,y:+y,width:+w,height:+h}});await b.close()})()
