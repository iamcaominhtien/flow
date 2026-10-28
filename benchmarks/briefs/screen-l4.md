# Briefs: Screen flow at L4 (as built)

One brief at level A, for screens drawn from screenshots of the app running from its own source (`docs/plugin/l4-as-built.md`). Written for this repository. It is **not** read by `check_briefs.py`. The structure below was read by hand from the code of the Angular implementation of RealWorld Conduit (`realworld-apps/angular-realworld-example-app`, commit `dd99ed2`): `src/app/app.routes.ts`, the `routerLink` and `navigate` calls of the pages, and `core/layout/header.component.html`.

The app needs to be built and served before a run; the brief gives the address. A run is scored on the screens captured in the right state, the transitions against the structure, the hotspots on the right elements, and the check.

---

## screen-L4-A-01 — Conduit, signed out and signed in, as built

* **type:** screen
* **level:** A
* **elements:** 15 (12 screens, 1 decision, 2 entry points)
* **connections:** 29
* **groups:** Entry points, Signed out, Signed in

### Brief

Draw the screen flow of Conduit, a small blogging app (the RealWorld demo), as it is built today: every screen at L4, a screenshot of the app running from its source. The source is in `<source folder>` (an Angular app; the routes are in `src/app/app.routes.ts`) and it is already built and served at `<address>`; it talks to a public demo API, where a new account sees only its own articles and the demo ones. Use made-up accounts only.

The flow has two groups. Signed out: the home page with the global feed, Sign in, Sign up, Sign in after a wrong password, a tag's feed, and an article read by a visitor. Signed in: the home page, an article seen by its author (with Edit and Delete), the editor for a new article, the editor for an existing one, the user's profile and Settings. The web screens are desktop browser screens. There are two ways in: opening the site, and a link straight to the editor, which the app lets through only when someone is signed in. Draw every way between these screens that the app offers, with the button or link that leads there; a click is something the person does, and an answer of the API is something the system does.

### Must show

* Twelve screens at L4, each a screenshot of the stated page in the stated state; codes W01 to W12.
* A decision "Signed in?" between the editor link and the editor, from the route guard (`requireAuth`), with its "no" exit to Sign in.
* Two entry points on the left: the site, and the link to the editor.
* Red dots on the elements the transitions start from, on the right element of each screenshot.
* Two zones: Signed out and Signed in. Sign in and Sign up lead from the first to the second.

### Traps

* Sign in has three exits: to the home page signed in, to the error state of the same page, and back to Sign up. The error state is a state of Sign in, not a new page.
* The home page appears twice (signed out and signed in) and is reached from many screens; logout returns to the signed-out one.
* The navbar is on every page; drawing every navbar link from every page gives a bundle of lines. The structure keeps the links a person uses from each page.
* The article seen by its author and by a visitor is one route in two states.

### Structure

**Elements**

- Entry points: Site (open the site), EditorLink (a link to /editor)
- Signed out: W01 Home (global feed), W02 Sign in, W03 Sign up, W04 Sign in error, W06 Tag feed, W07 Article (visitor), Signed in? (decision)
- Signed in: W05 Home (signed in), W08 Article (author), W09 New article, W10 Edit article, W11 Profile, W12 Settings

**Connections**

- Site -> W01 (open the site)
- EditorLink -> Signed in? (open the link)
- Signed in? -> W09 ([signed in])
- Signed in? -> W02 ([signed out])
- W01 -> W02 (click Sign in)
- W01 -> W03 (click Sign up)
- W01 -> W06 (click a tag)
- W01 -> W07 (click an article)
- W06 -> W07 (click an article)
- W06 -> W01 (click Global Feed)
- W02 -> W03 (click Need an account?)
- W03 -> W02 (click Have an account?)
- W02 -> W04 (click Sign in [credentials invalid])
- W02 -> W05 (click Sign in [credentials valid])
- W04 -> W05 (click Sign in [credentials valid])
- W03 -> W05 (click Sign up [account created])
- W07 -> W02 (click Sign in, under the comments)
- W05 -> W09 (click New Article)
- W05 -> W12 (click Settings)
- W05 -> W11 (click the user's name)
- W05 -> W08 (click the user's article)
- W09 -> W08 (click Publish Article [saved])
- W08 -> W10 (click Edit Article)
- W10 -> W08 (click Publish Article [saved])
- W08 -> W05 (click Delete Article)
- W11 -> W12 (click Edit Profile Settings)
- W11 -> W08 (click an article)
- W12 -> W11 (click Update Settings [saved])
- W12 -> W01 (click Or click here to logout)

### Sources

* RealWorld routing spec, `docs/src/content/docs/specifications/frontend/routing.md`, and `specs/e2e/SELECTORS.md` of `realworld-apps/realworld`.
* The Angular implementation's `app.routes.ts`, `header.component.html`, `auth.component.*`, `editor.component.ts`, `article.component.*`, `profile.component.html`, `settings.component.ts`, `user.service.ts`.

### Uncertain

* The structure was read by hand, not by a tool. Links the app offers that the brief does not ask for (the logo, the footer, the profile's Favorited tab, Follow and Favorite) are left out.
* The app was checked running from source on 2026-10-28 against `api.realworld.show`; the demo content of that API can change.
* The page loads its icon font over plain `http://`, which this environment does not reach, so icons are missing from the screenshots.
