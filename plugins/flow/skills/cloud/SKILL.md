---
description: Draw a cloud infrastructure diagram (resources inside regions, networks and subnets, and how traffic flows) as an animated HTML page and a draw.io file. Use when the user asks for an AWS, GCP or Azure style diagram or a network layout.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Cloud diagram

You write a short **spec**: the frames, the parts in them and the links. A script places the parts on a grid, sizes each frame around what it holds, routes the lines, checks the trust levels and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the frames (edge, region, VPC, zones, subnets, sites), the parts in the smallest frame that holds each, and the traffic between them.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "cloud",
  "title": "Basic cloud diagram: a web app in one VPC",
  "frames": [
    {"id": "edge", "kind": "edge"},
    {"id": "region", "kind": "region", "label": "Region eu-west"},
    {"id": "vpc", "kind": "vpc", "range": "10.0.0.0/16", "parent": "region"},
    {"id": "pub", "kind": "public", "parent": "vpc"},
    {"id": "priv", "kind": "private", "parent": "vpc"},
    {"id": "data", "kind": "data", "parent": "vpc"}
  ],
  "parts": [
    {"id": "users", "label": "Customers", "detail": "browsers", "icon": "browser"},
    {"id": "cdn", "label": "CDN", "detail": "caches static files", "icon": "cdn", "frame": "edge"},
    {"id": "lb", "label": "Load balancer", "detail": "spreads traffic", "icon": "load-balancer", "frame": "pub"},
    {"id": "app", "label": "App server", "detail": "container", "icon": "container", "frame": "priv"},
    {"id": "db", "label": "Database", "detail": "PostgreSQL", "icon": "sql-database", "frame": "data"},
    {"id": "files", "label": "Object storage", "detail": "images, uploads", "icon": "object-storage", "frame": "region"}
  ],
  "links": [
    {"from": "users", "to": "cdn", "label": "HTTPS", "main": true},
    {"from": "cdn", "to": "lb", "label": "HTTPS, on a miss", "main": true},
    {"from": "lb", "to": "app", "label": "HTTP", "main": true},
    {"from": "app", "to": "db", "label": "SQL", "main": true},
    {"from": "app", "to": "files", "label": "files, HTTPS"}
  ]
}
```

- **Frame**: `id`, `kind`, optional `label` (the name of the kind by default), `range` (the address range of a `vpc`, put into its label) and `parent` (the frame it sits in). The kind fixes the colour and the line: `region` blue solid, `vpc` violet dashed, `zone` grey dashed, `public` subnet green dashed, `private` subnet amber dashed, `data` subnet teal dashed, `onprem` (an office or data centre) slate solid, `dmz` red dashed, `edge` violet dashed. Frames nest: edge or region, then VPC, then zone, then subnet. Each has a coloured pill with its name on the top edge, at the left; lines never enter there. The frame is drawn around its parts and inner frames (30 px between a frame and the next one inside it, 40 px between a subnet and its parts).
- **Part**: `id`, `label` (by role: *Primary database*), `detail` (the technology or the zone: *PostgreSQL*, *zone a*), `icon`, `tone`, `frame` (the smallest frame that holds it; none for a user or a remote admin outside the cloud), `at: [row, column]`. Parts are 196 x 68. Icons of the Cloud services set: `load-balancer kubernetes sql-database nosql-database message-queue firewall-waf firewall virtual-network private-network cdn object-storage block-storage in-memory-cache container virtual-machine serverless-function dns api-gateway identity-iam secrets monitoring logging`, plus `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`.
- **Link**: `from` and `to` (parts: a link between sites runs from device to device, never frame to frame), `label` (a protocol or what travels: *HTTPS*, *IPsec VPN*, *replication*; required), `kind` (`call` ink, `main` blue, `event` or `copy` violet) or `main: true`. One blue route: one request from user to data. Violet is the event stream or the database copy, or a second site tunnel.
- **Trust levels**, top to bottom: the internet and the edge (0), a public subnet or a DMZ (1), a private subnet (2), a data subnet (3). The build refuses a database (`database`, `sql-database`, `nosql-database` icon) in a public subnet or a DMZ, a link that skips two levels (internet to data), and zones of one VPC that do not hold the same subnets. Parts that sit in no subnet (a managed queue or storage in the region frame, a part in the VPC frame) are not checked.
- **Layout**: the row follows the trust level (users above, edge, then public, private and data subnets; 255 px between rows); each zone takes as many columns as its fullest subnet and the same subnets sit on the same rows in every zone; a managed service in the region frame goes right of the VPC; on-premises sites go left of the region, remote users above. Two parts that would share a cell are moved apart. Give `at` to a part to override.
- `theme` (optional): `pastel` (default), `technical` or `midnight`. Cloud diagrams are plain only; `style: illustrated` is refused.
- More than about 16 parts: split by region or by network.

## Limits to tell the user

- There are no provider icons (AWS, GCP, Azure logos); the parts use the generic Cloud services icons. Say so if the user expects official ones.
- Frames are not snapped to a 40 px grid, and route tables, security-group rules, CIDR planning and multi-region failover are not drawn.
- A line may cross a frame border where it must; a label never sits on one.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout can give long lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
