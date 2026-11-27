// Usage: node resize.js IN.png OUT.png CSS_WIDTH DPR
// Shows a PNG at the width it would be read at (fit to width) and saves that view.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const [input, output, width, dpr] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width), height: 100 }, deviceScaleFactor: Number(dpr) });
  await page.setContent(`<html><body style="margin:0"><img id="i" style="width:${width}px;display:block" src="data:image/png;base64,${fs.readFileSync(path.resolve(input)).toString('base64')}"></body></html>`);
  await page.waitForFunction(() => document.getElementById('i').complete);
  await page.screenshot({ path: output, fullPage: true });
  await browser.close();
})();
