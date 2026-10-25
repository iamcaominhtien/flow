const { chromium } = require('playwright'); const root='/path/to/work/shots/';
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:980,height:560}});await p.goto('file://'+root+process.argv[2]+'.html');await p.screenshot({path:root+process.argv[2]+'.png'});await b.close()})()
