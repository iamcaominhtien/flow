const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
const cj = JSON.parse(fs.readFileSync(root + 'flowdesign/project/canvas.json', 'utf8'));
(async () => {
  const b = await chromium.launch(); let bad = 0;
  for (const [k, v] of Object.entries(cj.boards)) {
    const name = k.replace('.dc.html', '');
    let h = fs.readFileSync(root + 'flowdesign/project/' + k, 'utf8');
    h = h.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    fs.writeFileSync(root + 'shots/' + name + '.clip.html', h);
    const p = await b.newPage({ viewport: { width: 4200, height: 3000 } });
    await p.goto('file://' + root + 'shots/' + name + '.clip.html', { waitUntil: 'load' }).catch(() => {});
    const r = await p.evaluate(() => {
      const w = [...document.querySelectorAll('body div')].find(d => d.style.width && d.style.height && /px/.test(d.style.width));
      if(!w) return {nowrap:1}; const wr = w.getBoundingClientRect(); let mb = 0, mr = 0, who = '';
      w.querySelectorAll('*').forEach(e => { if (e.closest('svg') && e.tagName !== 'svg') return; if (e.tagName==='DIV' && e.children.length && !e.classList.contains('rc')) return; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return; if (r.bottom - wr.top > mb) { mb = r.bottom - wr.top; who = (e.textContent || '').trim().slice(0, 25) } mr = Math.max(mr, r.right - wr.left) });
      return { h: Math.round(wr.height), w: Math.round(wr.width), mb: Math.round(mb), mr: Math.round(mr), who };
    });
    if (r.nowrap) { console.log(name,'NO WRAPPER'); await p.close(); continue; }
    if (r.mb > v.h + 2 || r.mr > v.w + 2) { bad++; console.log(name, 'board', v.w + 'x' + v.h, 'content', r.mr + 'x' + r.mb, r.who); }
    await p.close();
  }
  console.log('clipped:', bad); await b.close();
})();
