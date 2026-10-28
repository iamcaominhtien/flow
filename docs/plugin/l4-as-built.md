# Screen flow L4: screens as built

Status: **phase 1 built (plugin 0.13.0); phases 2 and 3 are proposals.** This page describes a fifth fidelity level for the screen flow, L4, where each screen is a real screenshot of the application, built and run from its own source code.

## 1. Decisions

| Question | Decision |
| --- | --- |
| Name | **L4 · As built**. The design has L0 to L3 (design 02 section 2.3); L4 is the next one. |
| What a screen shows | A **real screenshot** of the running application, not a wireframe rebuilt from reading the code. |
| First test set | **RealWorld "Conduit"**, the Angular implementation, run against the hosted RealWorld API. |
| Platform first | Web (desktop and phone-width viewports). Native mobile comes later. |
| Dependencies | The plugin stays standard-library Python. Capturing screenshots needs a browser; that step runs outside the plugin, in the user's project, with tools the project or the session already has. |

## 2. What L4 means

L0 to L3 answer "how far has the **design** decided this screen?". L4 answers a different question: "what does the **built** screen look like?". The source of truth is the code, not the design.

| Level | What is drawn | Meaning |
| --- | --- | --- |
| L0 | A card with id and name | Nothing is decided |
| L1 | A device frame with generic content | The screen exists |
| L2 | The elements that cause a transition | The navigation is decided |
| L3 | A full wireframe | Everything is designed |
| **L4** | **A screenshot of the running app, in the device frame** | **The screen is built; this is what it looks like now** |

The levels mix in one diagram, as the design already allows. A flow where finished screens are L4, screens in progress are L2 and planned screens are L0 shows at a glance what is built and what is only planned.

The design's rule holds: **every level has the same width and the same centre line**, so raising a screen from L2 to L4 never moves an arrow. The screenshot is fitted into the screen area of the device frame.

## 3. How it works

```
 the app's source ──► build and run it (the project's own commands)
                         │
                         ▼
               capture script (Playwright)  ── one PNG per screen and state,
                         │                     a manifest with hotspot boxes
                         ▼
 spec (screens with "fidelity": "L4" and "capture") ──► flow.py build
                         │
                         ├──► HTML: the PNG inside the frame, click to see it full size
                         ├──► draw.io: an image cell inside the frame
                         └──► check: missing, stale or wrong-size captures
```

Two steps, kept apart:

1. **Capture** (outside the plugin). The skill tells Claude how to build and run the app with the project's own commands, and gives a Playwright script template that visits each screen in its state and writes a PNG. Playwright is the tool RealWorld's shared e2e suite already uses, so a Conduit implementation has it.
2. **Embed** (the plugin). `flow.py build` reads each PNG, checks its size from the PNG header and writes it into the HTML and the draw.io file as a data URI. The draw.io renderer already embeds SVG images this way; PNG is the same mechanism. No image library is needed. The standard library cannot resize a PNG, so the capture must be made at the size the frame needs (section 5).

## 4. The spec

A screen at L4 names its capture:

```json
{
  "id": "login",
  "code": "W02",
  "label": "Sign in",
  "device": "desktop",
  "fidelity": "L4",
  "capture": {
    "image": "captures/W02-login.png",
    "source": "src/app/core/auth/auth.component.ts",
    "hotspots": [{"text": "Sign in", "box": [880, 412, 140, 48]}]
  }
}
```

- `image`: the PNG, relative to the spec.
- `source`: the file that draws the screen. It is shown on hover in the HTML and used by the staleness check.
- `hotspots`: optional. These are the boxes of the elements a transition starts from, in the screenshot's pixels, recorded by the capture script from the element's bounding box. The red dot of L2 is drawn on them, so the tapped element is marked on the real screen.

A capture manifest (`captures/manifest.json`), written by `skills/screen-flow/capture.js`, holds the same fields for every screen code. A spec names it once, `"captures": "captures/manifest.json"`, and each L4 screen by its code, `"capture": "W02"`, so taking the screenshots again needs no edit of the spec.

## 5. Drawing

- **Name.** The screen's name stays at the top of the body, as at L1 and L2; the screenshot starts under it.
- **Size.** The frame keeps its device size (desktop 240 x 170, phone 156 x 324). A screenshot of a 1280 px wide page is shrunk about 5 times, so text is recognisable but not readable. Two answers:
  - the HTML opens the full screenshot when a screen is clicked (built: the picture takes the focus and a stylesheet rule shows it over the page; no script);
  - an optional `"size": "large"` draws an L4 screen at twice the frame size, and the layout makes room as it does for any larger node (not built).
- **Capture size.** The capture script takes the screenshot at the viewport of the device (desktop 1280 x 800, phone 390 x 844) with a device scale factor of 1, so the embedded PNG stays small. Measured on Conduit's twelve desktop screens: 25 to 125 KB each, 700 KB in all.
- **Fit.** The image covers the screen area of the frame from the top, keeping its aspect ratio; what is below the frame's height is cut off. A full-page capture is for the zoom view, not for the frame.
- **draw.io.** An image cell inside the frame cell, so the screenshot moves with the frame when the diagram is edited. draw.io cannot cut an image, so a screenshot taller than the screen area is shrunk to fit inside it there.

## 6. Checks

| Code | Severity | When |
| --- | --- | --- |
| `capture-missing` | error | `image` does not exist |
| `capture-not-png` | error | the file is not a PNG |
| `capture-aspect` | warning | the image's aspect ratio is far from the device's (a phone screenshot in a desktop frame) |
| `capture-stale` | warning | the `source` file is newer than the image |
| `capture-heavy` | warning | the images of one diagram add up to more than a set budget (about 8 MB) |
| `hotspot-outside` | warning | a hotspot box lies outside the image |

## 7. Capturing well

The capture script has to give the same picture every run:

- **Data.** Use seeded or demo accounts, never a real user's data. RealWorld's hosted API provides demo accounts, and accounts there cannot see each other.
- **State.** A screen is often a route plus a state: signed in or out, an empty list, an error. The script reaches each state with the e2e helpers the project has (RealWorld has `helpers/auth.ts` and `helpers/articles.ts`), or with route interception for errors.
- **Stability.** Wait for the network to be idle, turn off animations, and hide or mask what changes on every run (dates, avatars from a random service).
- **Hotspots.** Get each element by a stable selector (RealWorld's `SELECTORS.md` is a contract every implementation keeps) and record its bounding box.

## 8. Later: the flow from the code

The code holds the flow as well as the screens: routes, guards and navigation calls. In Conduit's `app.routes.ts`, `/settings` and `/editor` have a `requireAuth` guard that redirects to `/login`. That is a decision diamond "Signed in?" in the flow. Phase 3 reads the router and the navigation calls, builds a first spec from them, and adds a check that reports where the drawn flow and the code differ.

## 9. The first test set: Conduit

RealWorld (`github.com/gothinkster/realworld`, MIT) is a Medium-like app, "Conduit", built to one spec by many front ends. Checked on 2026-10-28:

- The routes are fixed by the spec: `/`, `/tag/:tag`, `/login`, `/register`, `/settings`, `/editor`, `/editor/:slug`, `/article/:slug`, `/profile/:username`, `/profile/:username/favorites`.
- `specs/e2e/SELECTORS.md` lists the CSS classes, input names and button texts every implementation must provide, and the shared Playwright suite uses them.
- The hosted API `api.realworld.show` and the Angular demo `demo.realworld.show` answered on that day.
- The Angular implementation (`github.com/realworld-apps/angular-realworld-example-app`, MIT, Angular 21) calls the hosted API, and declares its routes and guards in `src/app/app.routes.ts`.

Not done yet: **the app was not built or run here.** Installing its packages needs the session's permission to run code from outside the repository. That permission was not granted in the session that wrote this page.

### Brief `screen-L4-A-01` (draft)

Twelve web screens of Conduit at L4. Codes are W plus two digits.

| Code | Screen | Route and state |
| --- | --- | --- |
| W01 | Home, signed out | `/`, global feed |
| W02 | Sign in | `/login` |
| W03 | Sign up | `/register` |
| W04 | Sign in error | `/login` after a wrong password |
| W05 | Home, your feed | `/?feed=following`, signed in |
| W06 | Tag feed | `/tag/:tag` |
| W07 | Article, as a reader | `/article/:slug` |
| W08 | Article, as its author | `/article/:slug`, with edit and delete |
| W09 | New article | `/editor` |
| W10 | Edit article | `/editor/:slug` |
| W11 | Profile | `/profile/:username` |
| W12 | Settings | `/settings` |

The transitions come from the navbar and the buttons. There are about 25; to be counted from the code when the brief is written. One decision comes from the guards: "Signed in?" before Settings and the editor.

What a run is scored on:

1. every screen captured in the stated state;
2. every transition drawn, matched against the router and the navigation calls;
3. every hotspot on the right element;
4. the check's findings.

## 10. Phases

| Phase | Content | Done when |
| --- | --- | --- |
| 1 (built) | Plugin: `fidelity: "L4"` with `capture`; PNG embedding in HTML and draw.io; the checks in section 6; click to zoom in the HTML; an example built from synthetic captures (`examples/notes-built-screen-flow.spec.json`, screenshots of a small HTML page taken by `examples/captures/notes/capture.js`) | The tests pass with generated PNGs and an L4 example builds with no error |
| 2 | Skill: how to build and run the app, the Playwright capture template, the manifest, hotspots from selectors | A blind agent captures Conduit and draws `screen-L4-A-01` |
| 3 | Flow from code: routes and guards to a first spec; a check for drift between the diagram and the code | The drift check finds a transition removed from the code |

## 11. Open questions

- Whether `"size": "large"` is enough for reading, or the zoom view is the main way to read an L4 screen.
- Whether a full-page capture (long pages) should be shown as a scrolling frame in the HTML.
- Native mobile: emulator screenshots, or the project's own screenshot tests (Compose, SwiftUI previews). Not started.
