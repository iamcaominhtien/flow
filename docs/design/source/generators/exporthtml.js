const { chromium } = require('playwright'); const fs = require('fs');
const root = '/path/to/work/';
const out = '/path/to/flow/docs/design/source/';
fs.mkdirSync(out + 'html', { recursive: true }); fs.mkdirSync(out + 'canvas', { recursive: true });
const cj = JSON.parse(fs.readFileSync(root + 'flowdesign/project/canvas.json', 'utf8'));
const TPL = ['Main', 'Components_Process', 'Components_Structure', 'Icons'];
(async () => {
  const b = await chromium.launch();
  for (const k of Object.keys(cj.boards)) {
    const name = k.replace('.dc.html', '');
    const raw = fs.readFileSync(root + 'flowdesign/project/' + k, 'utf8');
    fs.copyFileSync(root + 'flowdesign/project/' + k, out + 'canvas/' + k);
    const script = (raw.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/) || [])[1] || '';
    let h = raw.replace(/<script src="\.\/support\.js"><\/script>/, '').replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1').replace(/<\/?x-dc>/g, '').replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '');
    if (TPL.includes(name)) {
      fs.writeFileSync(root + 'shots/' + name + '.exp.html', h);
      const p = await b.newPage({ viewport: { width: 1300, height: 900 } });
      await p.goto('file://' + root + 'shots/' + name + '.exp.html', { waitUntil: 'load' }).catch(() => {});
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
            } else { for (const a of [...ch.attributes]) if (a.value.includes('{{')) ch.setAttribute(a.name, sub(a.value, scope)); render(ch, scope); }
          }
        };
        render(document.body, vals);
      }, script);
      h = '<!doctype html>\n' + await p.evaluate(() => document.documentElement.outerHTML);
      await p.close();
    }
    h = h.replace('<head>', '<head>\n<!-- Standalone copy of the design-canvas board "' + name + '". Generated from source/canvas/' + k + '; opens in any browser. -->');
    fs.writeFileSync(out + 'html/' + name + '.html', h);
  }
  await b.close(); console.log('exported', Object.keys(cj.boards).length);
})();
