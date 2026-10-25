// usage: node shot.js Name  -> renders project/Name.dc.html without x-dc runtime to scratchpad/shots/Name.png
const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
(async () => {
  const b = await chromium.launch(); 
  for (const name of process.argv.slice(2)) {
    let h = fs.readFileSync(root + 'flowdesign/project/' + name + '.dc.html', 'utf8');
    h = h.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    fs.mkdirSync(root + 'shots', { recursive: true }); fs.writeFileSync(root + 'shots/' + name + '.html', h);
    const p = await b.newPage({ viewport: { width: 1900, height: 900 } });
    await p.goto('file://' + root + 'shots/' + name + '.html', { waitUntil: 'load', timeout: 15000 }).catch(() => {});
    await p.screenshot({ path: root + 'shots/' + name + '.png', fullPage: true });
    await p.close();
  }
  await b.close();
})();
