"""Tests for reading an app's code into a code map, and for the drift check and the draft."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib import code_map  # noqa: E402
from flowlib.check import Code  # noqa: E402
from flowlib.code_draft import draft_spec  # noqa: E402
from flowlib.code_drift import find_drift  # noqa: E402
from flowlib.code_scan import scan  # noqa: E402
from flowlib.diagrams import layout  # noqa: E402

ANGULAR_APP = {
    "main.ts": "import { AppComponent } from './app/app.component';\n",
    "app/app.component.ts": (
        "import { HeaderComponent } from './header.component';\n"
        "@Component({ templateUrl: './app.component.html' })\nexport class AppComponent {}\n"
    ),
    "app/app.component.html": "<app-header></app-header><router-outlet></router-outlet>\n",
    "app/header.component.ts": "@Component({ templateUrl: './header.component.html' })\n",
    "app/header.component.html": (
        '<a routerLink="/">Home</a>\n<a routerLink="/settings">Settings</a>\n'
    ),
    "app/app.routes.ts": (
        "const requireAuth = () => inject(Router).createUrlTree(['/login']);\n"
        "export const routes: Routes = [\n"
        "  { path: '', loadComponent: () => import('./home.component') },\n"
        "  { path: 'login', loadComponent: () => import('./login.component') },\n"
        "  { path: 'settings', loadComponent: () => import('./settings.component'),\n"
        "    canActivate: [requireAuth] },\n"
        "  { path: 'article/:slug', loadComponent: () => import('./article.component') },\n"
        "];\n"
    ),
    "app/home.component.ts": (
        "@Component({ template: `<a [routerLink]=\"['/article', a.slug]\">Read</a>` })\n"
    ),
    "app/login.component.ts": "this.router.navigate(['/']);\n",
    "app/settings.component.ts": "export class Settings {}\n",
    "app/article.component.ts": '<a routerLink="/login">Sign in</a>\n',
}


def _write_app(folder: Path, files: dict[str, str]) -> Path:
    """Write the files of a small app under a folder; return the folder."""
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return folder


def test_the_scan_reads_routes_guards_links_and_the_top_bar(tmp_path: Path) -> None:
    """Every page is found with its component, a guard with where it sends, the bar as shared."""
    code = scan(_write_app(tmp_path, ANGULAR_APP))
    routes = {route.path: route for route in code.routes}
    assert set(routes) == {"/", "/login", "/settings", "/article/:slug"}
    assert routes["/settings"].guards == ("requireAuth",)
    assert routes["/settings"].denied == ("/login",)
    assert routes["/"].files == ("app/home.component.ts",)
    assert code.shared == ("app/header.component.html",)
    targets = {(link.file, link.target) for link in code.links}
    assert ("app/home.component.ts", "/article/*") in targets


def test_the_code_map_round_trips_through_json(tmp_path: Path) -> None:
    """What ``dump`` writes, ``load`` reads back unchanged."""
    code = scan(_write_app(tmp_path / "src", ANGULAR_APP))
    path = tmp_path / "code.json"
    code_map.dump(code, path)
    assert code_map.load(path) == code


def _spec(taps: list[dict]) -> dict:
    """Return a spec of the small app's four pages, each tied to its path, with some taps."""
    screens = [
        {"id": "home", "label": "Home", "path": "/"},
        {"id": "login", "label": "Sign in", "path": "/login"},
        {"id": "settings", "label": "Settings", "path": "/settings"},
        {"id": "article", "label": "Article", "path": "/article/hello"},
    ]
    return {"type": "screen", "screens": screens, "taps": taps}


def test_a_tap_the_code_no_longer_has_is_reported(tmp_path: Path) -> None:
    """The article page links to Sign in; once that link is gone, the tap is drift."""
    taps = [
        {"from": "home", "to": "article", "trigger": "click Read"},
        {"from": "article", "to": "login", "trigger": "click Sign in"},
    ]
    code = scan(_write_app(tmp_path / "before", ANGULAR_APP))
    before, _ = find_drift(_spec(taps), tmp_path, code)
    assert Code.TAP_NOT_IN_CODE not in [finding.code for finding in before]
    changed = {**ANGULAR_APP, "app/article.component.ts": "export class Article {}\n"}
    after, summary = find_drift(
        _spec(taps), tmp_path, scan(_write_app(tmp_path / "after", changed))
    )
    drift = [finding for finding in after if finding.code is Code.TAP_NOT_IN_CODE]
    assert [finding.items for finding in drift] == [("article", "login")]
    assert summary.startswith("drift: 2 of 2 taps checked")


def test_links_and_guards_the_diagram_leaves_out_are_reported(tmp_path: Path) -> None:
    """A link of a page with no tap, and a guarded page entered with no decision."""
    code = scan(_write_app(tmp_path, ANGULAR_APP))
    findings, _ = find_drift(
        _spec([{"from": "home", "to": "settings", "trigger": "click Settings"}]), tmp_path, code
    )
    codes = [finding.code for finding in findings]
    assert Code.LINK_NOT_DRAWN in codes  # home links to the article
    assert Code.GUARD_NOT_DRAWN in codes  # settings is guarded


def test_the_draft_builds_with_a_decision_for_each_guard(tmp_path: Path) -> None:
    """The first spec has a screen per page, the guard as a decision, and lays out."""
    code = scan(_write_app(tmp_path, ANGULAR_APP))
    spec = draft_spec(code, None, "Small app")
    ids = {item["id"]: item for item in spec["screens"]}
    assert {"home", "login", "settings", "article-slug", "guard-requireauth"} <= set(ids)
    assert {"from": "guard-requireauth", "to": "login", "guard": "fails", "kind": "failure"} in (
        spec["taps"]
    )
    scene = layout(json.loads(json.dumps(spec)))
    assert any(node.id == "guard-requireauth" for node in scene.nodes)


def test_jsx_routes_and_links_are_read(tmp_path: Path) -> None:
    """A React Router app: nested ``<Route>`` elements, ``<Link to>`` and template targets."""
    app = {
        "main.jsx": "import App from './App';\n",
        "App.jsx": (
            "import Home from './Home';\nimport Post from './Post';\n"
            '<Routes><Route path="/" element={<Layout />}>\n'
            "  <Route index element={<Home />} />\n"
            '  <Route path="posts/:id" element={<Post />} />\n'
            "</Route></Routes>\n"
        ),
        "Home.jsx": "<Link to={`/posts/${post.id}`}>Open</Link>\n",
        "Post.jsx": 'navigate("/");\n',
    }
    code = scan(_write_app(tmp_path, app))
    assert {route.path for route in code.routes} == {"/", "/posts/:id"}
    assert ("Home.jsx", "/posts/*") in {(link.file, link.target) for link in code.links}
