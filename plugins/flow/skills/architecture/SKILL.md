---
description: Draw a system architecture diagram (components, the zones they live in, and how they call each other) as an animated HTML page and a draw.io file. Use when the user asks for an architecture, infrastructure or cloud diagram, or a system overview.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Architecture diagram

You write a short **spec**: the zones (layers), the components and the links. A script puts each layer on a row, places the components, draws a frame around each zone, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself. For regions, subnets and trust levels use the `cloud` skill; for a fixed vocabulary and levels of zoom use `c4`.

## Steps

1. List the layers top to bottom (clients, edge, services, data), the third parties, the components in each, and the calls, events and copies between them. Name parts in the team's words (*Order service*) with the technology or the job in `detail`.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "architecture",
  "title": "Architecture: online shop",
  "desc": "One sentence that says what the diagram shows.",
  "zones": [
    {"id": "clients", "label": "Clients", "tone": "blue"},
    {"id": "edge", "label": "Edge", "tone": "violet"},
    {"id": "services", "label": "Services", "tone": "green"},
    {"id": "data", "label": "Data", "tone": "amber"},
    {"id": "third", "label": "Third party", "tone": "gray", "beside": "services"}
  ],
  "components": [
    {"id": "web", "label": "Web app", "detail": "React", "icon": "phone", "zone": "clients"},
    {"id": "gateway", "label": "API gateway", "detail": "routing, limits", "icon": "api-gateway", "zone": "edge"},
    {"id": "orders", "label": "Order service", "detail": "checkout", "icon": "server", "zone": "services"},
    {"id": "psp", "label": "Payment provider", "detail": "card network", "icon": "card", "zone": "third"},
    {"id": "db", "label": "Orders database", "detail": "PostgreSQL", "icon": "sql-database", "zone": "data"}
  ],
  "links": [
    {"from": "web", "to": "gateway", "label": "HTTPS", "main": true},
    {"from": "gateway", "to": "orders", "label": "create order", "main": true},
    {"from": "orders", "to": "db", "label": "write"},
    {"from": "orders", "to": "psp", "label": "charge", "kind": "event"}
  ]
}
```

- **Zone**: `id`, `label`, `tone`, optional `parent` (another zone: it sits inside it, in its row) or `beside` (the id of a layer: a **third party**, in the row of that layer and to its right; use it for outside parties). Each top-level zone without `beside` is one **layer** and one row, in the order of the spec. The layer tints are: clients blue, edge violet, services green, data amber, third parties grey. A frame is dashed with a dark pill on its top left edge; zones nest with 30 px between the outer and the inner edge.
- **Component**: `id`, `label`, `detail` (the technology or the job, never a sentence), `icon`, `tone` (by domain or owner, not by layer: the same part has the same tint everywhere), `zone` (the smallest zone that holds it; none puts it in a row above every layer), `at: [row, column]`. Plain parts are 196 x 68 and layers are 260 px apart; parts of a layer share a centre line and are placed in the order of the spec, the row centred under the widest one. Use `at` to line parts up in columns (a gateway under its callers) or to put a part in another row.
- **Link**: `from` and `to` (a component, **or a zone** for "any part inside": the line then starts or ends on the edge of the frame, drawn once and labelled once, as in *every service sends metrics here*), `label` (required: a protocol or an action), `kind` or `main: true`. An arrow shows who starts the call, not which way data flows: a read is an arrow *to* the database. Kinds: `call` (ink, thin), `main` (blue, thick, animated; the one route the diagram is about), `event` (violet, thin, slow: queues, topics, streams), `copy` (dashed slate: replication, a fallback, a return you want to show). A second blue route cancels the effect.
- Leave 90 px of line for a label; parts in a row sit 436 px apart (centres), so 240 px of line when they are joined by a labelled line. Eight to twelve parts is a good size; past about fifteen, split by layer or domain.
- `theme` (optional): `pastel` (default), `technical` or `midnight`.

## Patterns

Six arrangements appear in most systems. Add one by writing its parts and links, then connect it to the rest. Name the pattern in `desc`, never in the label of a part.

| Pattern | Question | Write |
| --- | --- | --- |
| API gateway | How do I protect many services? | One gateway part in the edge layer; a link from the clients' zone to it (`"from": "clients", "to": "gateway"`) and links from it to each service. Authentication, rate limits and routing live there. |
| Queue and worker | How do I do the slow part later? | `api` -> `queue` (`event`, label `enqueue`), `queue` -> `worker` (`event`, label `job`). The caller does not wait. |
| Cache-aside | How do I speed up reads? | `service` -> `cache` (`call`, `get`), then `service` -> `db` (`call`, `read on a miss`). Only a miss reaches the database, and the service fills the cache from the answer. Two lines between the same two parts are not drawn well: do not add a second one for the fill. |
| CDN in front of an origin | How do I serve static files fast? | `clients` -> `cdn` (`main` or `call`, `HTTPS`), `cdn` -> `origin` (`copy`, `on a miss`). |
| Publish and subscribe | How do I fan out one event? | `publisher` -> `topic` (`event`, `publish`), then one `topic` -> `subscriber` (`event`, `consume`) per listener. Adding a subscriber changes nothing else. |
| Read replica | How do I scale reads? | `service` -> `primary` (`call`, `write`), `service` -> `replica` (`call`, `read`), `primary` -> `replica` (`copy`, `replication`). Replicas may lag a little. |

## Illustrated style

Add `"style": "illustrated"` at the top level to draw every component as a card: the name in a pill at the left, the `detail` under it and a large 64 px icon at the right. Cards are 232 x 96 and layers are 240 px apart; lines, labels, zones and tints are identical, so a diagram changes style by changing this one key. Give each component an `icon`, a `tone` and a short `detail`, and keep names short. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on the card: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

## Limits to tell the user

- A zone is a frame around its parts and inner frames. A part of another zone that falls inside the box of a frame (for example a third party placed with `at` among the layers) is not moved out; look at the picture. A line that ends on a frame ends in the middle of one side; the optional entry side is not built.
- The patterns are written by hand from the table; there is no `pattern` key.
- The old keys `kind` on a component, `style: async` on a link and `direction` are gone: use `icon` and `tone`, `kind: event` and the layers.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout can give long lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
