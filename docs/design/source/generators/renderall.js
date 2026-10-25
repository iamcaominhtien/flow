const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
const cj = JSON.parse(fs.readFileSync(root + 'flowdesign/project/canvas.json', 'utf8'));
(async () => {
  const b = await chromium.launch();
  for (const [k, v] of Object.entries(cj.boards)) {
    const name = k.replace('.dc.html', '');
    let h = fs.readFileSync(root + 'flowdesign/project/' + k, 'utf8');
    h = h.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    fs.writeFileSync(root + 'shots/' + name + '.doc.html', h);
    const p = await b.newPage({ viewport: { width: v.w, height: v.h } });
    await p.goto('file://' + root + 'shots/' + name + '.doc.html', { waitUntil: 'load', timeout: 20000 }).catch(() => {});
    await p.waitForTimeout(150);
    await p.screenshot({ path: root + 'docimg/' + name + '.png', clip: { x: 0, y: 0, width: v.w, height: v.h } });
    await p.close();
  }
  await b.close(); console.log('done');
})();
