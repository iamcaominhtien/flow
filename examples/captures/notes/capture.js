// Take the screenshots of the notes example: one PNG per screen at a phone viewport, and the
// boxes of the elements marked data-hotspot, written to manifest.json. Run with node from any
// folder; it needs Playwright and Chromium.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENS = ['sign-in', 'notes', 'note'];
const VIEWPORT = { width: 390, height: 844 };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: 1 });
  const manifest = {};
  for (const screen of SCREENS) {
    await page.goto(`file://${path.join(__dirname, 'app.html')}#${screen}`);
    await page.waitForLoadState('networkidle');
    const file = `${screen}.png`;
    await page.screenshot({ path: path.join(__dirname, file) });
    const hotspots = await page.$$eval(`#${screen} [data-hotspot]`, (elements) =>
      elements.map((element) => {
        const box = element.getBoundingClientRect();
        return { text: element.dataset.hotspot, box: [box.x, box.y, box.width, box.height].map(Math.round) };
      }),
    );
    manifest[screen] = { image: file, hotspots };
  }
  fs.writeFileSync(path.join(__dirname, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  await browser.close();
})();
