// usage: node lint.js Name [Name...]  -> reports nodes (text labels, small shapes) that straddle a box border (data-lint=box) or lane divider (data-lint=edge)
const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
(async () => {
  const b = await chromium.launch(); let bad = 0;
  for (const name of process.argv.slice(2)) {
    let h = fs.readFileSync(root + 'flowdesign/project/' + name + '.dc.html', 'utf8');
    h = h.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    fs.mkdirSync(root + 'shots', { recursive: true }); fs.writeFileSync(root + 'shots/' + name + '.lint.html', h);
    const p = await b.newPage({ viewport: { width: 1900, height: 900 } });
    await p.goto('file://' + root + 'shots/' + name + '.lint.html', { waitUntil: 'load' }).catch(() => {});
    const res = await p.evaluate(() => {
      const out = [];
      const rect = e => { const r = e.getBoundingClientRect(); return { l: r.left + scrollX, t: r.top + scrollY, r: r.right + scrollX, b: r.bottom + scrollY }; };
      const boxes = [...document.querySelectorAll('[data-lint=box]')].map(rect);
      const edges = [...document.querySelectorAll('[data-lint=edge]')].map(rect);
      const nodes = [];
      document.querySelectorAll('div').forEach(d => {
        if (d.dataset.lint) return;
        const txt = d.textContent.trim();
        if (!txt || [...d.children].some(c => c.tagName === 'DIV' && c.textContent.trim())) return;
        if (d.style.writingMode) return;
        const r = rect(d); if (r.r - r.l < 2) return;
        // use the visible text extent for wide containers: skip empty padding by using width of text range
        const rg = document.createRange(); rg.selectNodeContents(d); const tr = rg.getBoundingClientRect();
        nodes.push({ id: txt.slice(0, 30), l: Math.max(r.l, tr.left + scrollX), t: Math.max(r.t, tr.top + scrollY), r: Math.min(r.r, tr.right + scrollX), b: Math.min(r.b, tr.bottom + scrollY) });
      });
      document.querySelectorAll('svg').forEach(s => {
        const r = rect(s); const w = r.r - r.l, h = r.b - r.t;
        if (Math.min(w, h) >= 30 && Math.max(w, h) <= 80) nodes.push({ id: 'shape@' + Math.round(r.l) + ',' + Math.round(r.t), ...r });
      });
      for (const n of nodes) {
        for (const bx of boxes) {
          const inter = n.l < bx.r && bx.l < n.r && n.t < bx.b && bx.t < n.b;
          const inside = n.l >= bx.l && n.r <= bx.r && n.t >= bx.t && n.b <= bx.b;
          if (inter && !inside) out.push('crosses box border: ' + n.id);
        }
        for (const e of edges) {
          const y = (e.t + e.b) / 2;
          if (n.l < e.r && e.l < n.r && n.t < y + 1 && y - 1 < n.b) out.push('sits on divider: ' + n.id);
        }
      }
      return out;
    });
    res.forEach(r => { console.log(name + ': ' + r); bad++; });
  }
  console.log(bad ? bad + ' issue(s)' : 'lint clean');
  await b.close();
})();
