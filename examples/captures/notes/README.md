# Notes example: screenshots

Synthetic screenshots for `examples/notes-built-screen-flow.spec.json`, the L4 example. They are not of a real app: `app.html` is a small page with three screens, and `capture.js` opens each one at a phone viewport (390 x 844, scale factor 1) with Playwright, saves a PNG and writes the boxes of the elements marked `data-hotspot` to `manifest.json`. The spec copies those boxes.

To take them again (Playwright and Chromium are needed):

```bash
node examples/captures/notes/capture.js
```
