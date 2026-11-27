// Render a Flow page to PNG, whole and as it will be seen on its medium.
//
//   node view.js page.html [medium]
//
// medium: phone, screen (the default), slide or editor. It writes, next to the page:
//   <name>.png           the whole diagram at twice its size, to deliver or to inspect
//   <name>.<medium>.png  the whole diagram fitted to the medium's width, as a reader first sees it
//                        (phone: 390 css px at 3x; screen and editor: 1440; slide: 1280)
// Open the second file and read it at that size: if a label cannot be read there, the reader
// cannot read it either. Animations are stilled (reduced motion), so the picture is final.
//
// It needs Playwright and Chromium (the project's own, or `require('playwright')` in the session).

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const { chromium } = loadPlaywright();

const MEDIA = {
  phone: { width: 390, scale: 3 },
  screen: { width: 1440, scale: 1 },
  editor: { width: 1440, scale: 1 },
  slide: { width: 1280, scale: 1 },
};
const WHOLE_SCALE = 2; // the delivered picture is sharp when zoomed in
const MEASURE_WIDTH = 320; // css px; narrower than any diagram

async function main() {
  const [page, mediumName = 'screen'] = process.argv.slice(2);
  const medium = MEDIA[mediumName];
  if (!page || !medium) {
    console.error(`usage: node view.js page.html [${Object.keys(MEDIA).join('|')}]`);
    process.exit(1);
  }
  const source = path.resolve(page);
  const base = source.replace(/\.html$/, '');
  const browser = await chromium.launch();
  const whole = `${base}.png`;
  const size = await shootWhole(browser, source, whole);
  const seen = `${base}.${mediumName}.png`;
  await shootFitted(browser, whole, size, medium, seen);
  await browser.close();
  const shown = Math.min(1, medium.width / size.width);
  console.log(`wrote ${whole} (${size.width} x ${size.height} css px)`);
  console.log(`wrote ${seen}: the diagram shown at ${Math.round(shown * 100)}% to fit ${medium.width} px`);
}

async function shootWhole(browser, source, target) {
  // Start narrow: the page then takes its own width, not the window's.
  const context = await browser.newContext({
    viewport: { width: MEASURE_WIDTH, height: 600 },
    deviceScaleFactor: WHOLE_SCALE,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  await page.goto(`file://${source}`);
  await page.waitForLoadState('networkidle');
  const size = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    height: document.documentElement.scrollHeight,
  }));
  await page.setViewportSize(size);
  await page.screenshot({ path: target, fullPage: true });
  await context.close();
  return size;
}

async function shootFitted(browser, picture, size, medium, target) {
  const width = Math.min(medium.width, size.width);
  const context = await browser.newContext({
    viewport: { width: medium.width, height: 100 },
    deviceScaleFactor: medium.scale,
  });
  const page = await context.newPage();
  await page.setContent(
    `<body style="margin:0;background:#fff"><img id="d" style="display:block;width:${width}px" src="${dataUrl(picture)}"></body>`,
  );
  await page.waitForFunction(() => document.getElementById('d').complete);
  await page.screenshot({ path: target, fullPage: true });
  await context.close();
}

function dataUrl(picture) {
  // A page made with setContent may not load file:// images, so the picture is inlined.
  return `data:image/png;base64,${fs.readFileSync(picture).toString('base64')}`;
}

function loadPlaywright() {
  // The project's own Playwright first, then the one installed for the whole machine.
  try {
    return require('playwright');
  } catch (error) {
    const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
    return require(path.join(root, 'playwright'));
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
