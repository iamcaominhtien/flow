const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
const cj = JSON.parse(fs.readFileSync(root + 'flowdesign/project/canvas.json', 'utf8'));
(async () => {
  const b = await chromium.launch();
  for (const name of process.argv.slice(2)) {
    const v = cj.boards[name + '.dc.html'];
    let raw = fs.readFileSync(root + 'flowdesign/project/' + name + '.dc.html', 'utf8');
    const script = (raw.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/) || [])[1] || '';
    let h = raw.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    fs.writeFileSync(root + 'shots/' + name + '.tpl.html', h);
    const p = await b.newPage({ viewport: { width: v.w, height: v.h } });
    p.on('pageerror', e => console.log('ERR', e.message));
    await p.goto('file://' + root + 'shots/' + name + '.tpl.html', { waitUntil: 'load' }).catch(() => {});
    await p.evaluate((script) => {
      class DCLogic {}
      const vals = new Function('DCLogic', script + '; return new Component().renderVals();')(DCLogic);
      const res = (expr, scope) => { let cur; const parts = expr.trim().split('.'); cur = scope[parts[0]]; for (let i = 1; i < parts.length && cur != null; i++) cur = cur[parts[i]]; return cur; };
      const sub = (s, scope) => s.replace(/\{\{\s*([^}]+?)\s*\}\}/g, (m, e) => { const r = res(e, scope); return r == null ? '' : String(r); });
      const render = (node, scope) => {
        for (const ch of [...node.childNodes]) {
          if (ch.nodeType === 3) { ch.nodeValue = sub(ch.nodeValue, scope); continue; }
          if (ch.nodeType !== 1) continue;
          const tag = ch.tagName.toLowerCase();
          if (tag === 'sc-for') {
            const m = ch.getAttribute('list').match(/\{\{\s*([^}]+?)\s*\}\}/); const list = res(m[1], scope) || []; const as = ch.getAttribute('as');
            const frag = document.createDocumentFragment();
            list.forEach(item => { const c = ch.cloneNode(true); render(c, { ...scope, [as]: item }); while (c.firstChild) frag.appendChild(c.firstChild); });
            ch.replaceWith(frag);
          } else if (tag === 'sc-if') {
            const m = ch.getAttribute('value').match(/\{\{\s*([^}]+?)\s*\}\}/); const val = res(m[1], scope);
            if (val) { render(ch, scope); const frag = document.createDocumentFragment(); while (ch.firstChild) frag.appendChild(ch.firstChild); ch.replaceWith(frag); } else ch.remove();
          } else {
            for (const a of [...ch.attributes]) if (a.value.includes('{{')) ch.setAttribute(a.name, sub(a.value, scope));
            render(ch, scope);
          }
        }
      };
      render(document.body, vals);
    }, script);
    await p.waitForTimeout(200);
    await p.screenshot({ path: root + 'docimg/' + name + '.png', clip: { x: 0, y: 0, width: v.w, height: v.h } });
    await p.close();
  }
  await b.close();
})();
