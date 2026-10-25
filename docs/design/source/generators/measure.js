const { chromium } = require('playwright'); const root='/path/to/work/shots/';
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1400,height:900}});await p.goto('file://'+root+process.argv[2]+'.html');
console.log(await p.evaluate(()=>{let m=0;document.querySelectorAll('div').forEach(d=>{m=Math.max(m,d.getBoundingClientRect().bottom)});return m}));await b.close()})()
