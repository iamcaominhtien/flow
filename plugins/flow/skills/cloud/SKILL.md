---
description: Draw a cloud infrastructure diagram (resources inside regions, networks and subnets, and how traffic flows) as an animated HTML page and a draw.io file. Use when the user asks for an AWS, GCP or Azure style diagram or a network layout.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Cloud diagram

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the resources, the nested zones (region, network, subnet) they sit in, and the traffic between them.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "cloud",
  "title": "Cloud: web app in one VPC",
  "desc": "Traffic enters through a load balancer, reaches two app servers, and the app uses a database and a queue.",
  "zones": [
    {
      "id": "region",
      "label": "Region",
      "tone": "blue"
    },
    {
      "id": "vpc",
      "label": "VPC",
      "tone": "violet",
      "parent": "region"
    }
  ],
  "resources": [
    {
      "id": "users",
      "label": "Users",
      "kind": "client"
    },
    {
      "id": "lb",
      "label": "Load balancer",
      "kind": "balancer",
      "zone": "vpc"
    },
    {
      "id": "app",
      "label": "App servers",
      "detail": "2 instances",
      "zone": "vpc"
    },
    {
      "id": "db",
      "label": "Database",
      "kind": "database",
      "zone": "vpc"
    },
    {
      "id": "jobs",
      "label": "Job queue",
      "kind": "queue",
      "zone": "vpc"
    }
  ],
  "links": [
    {
      "from": "users",
      "to": "lb",
      "label": "HTTPS",
      "main": true
    },
    {
      "from": "lb",
      "to": "app",
      "main": true
    },
    {
      "from": "app",
      "to": "db"
    },
    {
      "from": "app",
      "to": "jobs",
      "style": "async"
    }
  ]
}
```

- **Resource**: `id`, `label`, `kind` (`service` default, `client`, `external`, `balancer`, `database`, `storage`, `queue`), `detail`, `icon`, `tone`, `zone`.
- **Zone**: `id`, `label`, optional `tone` and `parent` to nest it (a VPC inside a region).
- **Link**: `from`, `to`, `label`, `style` (`call` solid, `async` dashed), `main: true`.
- Top level: `type` (`cloud`), `title`, `desc`, optional `direction` (`down` default, or `right`).
- Optional `at: [row, column]` on an item places it on an explicit grid cell. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- There are no provider icons (AWS, GCP, Azure logos). Use the built-in icons or draw one; say so if the user expects official icons.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).
