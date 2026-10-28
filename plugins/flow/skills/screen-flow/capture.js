// Take the screenshots of an L4 screen flow from a running web app, driven by a plan file.
//
//   node capture.js plan.json [out-folder]
//
// The plan names the app's address, the viewport, the sessions the screens need (a signed-in
// user, made by steps such as filling a form) and one entry per screen: where to go, what to do
// first, what to wait for, which elements are hotspots and which changing parts to mask. Each
// screen is shot in a fresh browser context, so one screen's state never leaks into the next.
// The script writes one PNG per screen and manifest.json, which a spec reads with
// "captures": "<folder>/manifest.json" and "capture": "<code>".
//
// It needs Playwright and Chromium (the project's own, or `require('playwright')` in the
// session). It runs code of the app being drawn: run it only on an app you are allowed to run,
// with seeded or demo data.
//
// A screen is {"code", "goto" or "steps", "session", "wait", "source", "hotspots", "mask"}:
// "hotspots" maps the words of each element a transition starts from to a selector, "mask"
// lists selectors of parts that change on every run (dates, random avatars).
//
// Steps, in order, each an object with one action:
//   {"goto": "/path"}                     open a path of base_url (or a full address)
//   {"fill": "selector", "value": "text"} type into a field
//   {"click": "selector"}                 click an element
//   {"press": "selector", "key": "Enter"} press a key in an element
//   {"wait": "selector"}                  wait until an element is visible
//   {"wait_url": "regex"}                 wait until the address matches
//   {"remember": "name", "pattern": "regex with one group"}
//                                         keep a part of the current address as ${name}
// "${run}" in any text is a number unique to this run (for a new user name), and "${name}" is a
// value kept by "remember".

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const SETTLE_MS = 300; // after the network is idle, for fonts and late layout

async function main() {
  const planPath = path.resolve(process.argv[2]);
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const out = path.resolve(process.argv[3] || path.join(path.dirname(planPath), 'captures'));
  fs.mkdirSync(out, { recursive: true });
  const values = { run: String(Date.now()) };
  const [width, height] = plan.viewport || [1280, 800];
  const browser = await chromium.launch();
  const states = {};
  try {
    for (const [name, session] of Object.entries(plan.sessions || {})) {
      states[name] = await makeSession(browser, plan, session, values, { width, height });
    }
    const manifest = { viewport: [width, height], screens: {} };
    for (const screen of plan.screens) {
      manifest.screens[screen.code] = await shoot(browser, plan, screen, { states, values, out, width, height });
      console.log(`${screen.code}: ${manifest.screens[screen.code].url}`);
    }
    fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  } finally {
    await browser.close();
  }
}

async function makeSession(browser, plan, session, values, viewport) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  await runSteps(page, plan, session.steps || [], values);
  const state = await context.storageState();
  await context.close();
  return state;
}

async function shoot(browser, plan, screen, run) {
  const options = { viewport: { width: run.width, height: run.height }, deviceScaleFactor: 1 };
  if (screen.session) options.storageState = run.states[screen.session];
  const context = await browser.newContext(options);
  const page = await context.newPage();
  try {
    await runSteps(page, plan, screen.steps || [{ goto: screen.goto || '/' }], run.values);
    if (screen.wait) await page.locator(fill(screen.wait, run.values)).first().waitFor();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(SETTLE_MS);
    const image = `${screen.code}.png`;
    const mask = (screen.mask || []).map((selector) => page.locator(selector));
    await page.screenshot({ path: path.join(run.out, image), animations: 'disabled', caret: 'hide', mask });
    const hotspots = [];
    const missing = [];
    for (const [text, selector] of Object.entries(screen.hotspots || {})) {
      const box = await page.locator(fill(selector, run.values)).first().boundingBox().catch(() => null);
      if (box) hotspots.push({ text, box: [box.x, box.y, box.width, box.height].map(Math.round) });
      else missing.push(text);
    }
    return { image, url: page.url(), source: screen.source || "", hotspots, missing };
  } finally {
    await context.close();
  }
}

async function runSteps(page, plan, steps, values) {
  for (const step of steps) {
    if (step.goto !== undefined) await page.goto(address(plan, fill(step.goto, values)), { waitUntil: 'networkidle' });
    else if (step.fill !== undefined) await page.fill(fill(step.fill, values), fill(step.value, values));
    else if (step.click !== undefined) await page.locator(fill(step.click, values)).first().click();
    else if (step.press !== undefined) await page.press(fill(step.press, values), step.key);
    else if (step.wait !== undefined) await page.locator(fill(step.wait, values)).first().waitFor();
    else if (step.wait_url !== undefined) await page.waitForURL(new RegExp(fill(step.wait_url, values)));
    else if (step.remember !== undefined) values[step.remember] = remembered(page.url(), step.pattern);
    else throw new Error(`unknown step: ${JSON.stringify(step)}`);
  }
}

function remembered(url, pattern) {
  const found = new RegExp(pattern).exec(url);
  if (!found) throw new Error(`'${pattern}' does not match ${url}`);
  return found[1];
}

function address(plan, target) {
  return /^https?:/.test(target) ? target : plan.base_url.replace(/\/$/, '') + target;
}

function fill(text, values) {
  return String(text).replace(/\$\{(\w+)\}/g, (_, name) => {
    if (!(name in values)) throw new Error(`no value for \${${name}}`);
    return values[name];
  });
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
