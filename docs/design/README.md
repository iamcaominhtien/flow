# Flow design document

The design of **Flow**: the written specification, with pictures, of every diagram type the plugins will draw in draw.io. Read it before writing a plugin; it is the contract between the design and the code.

Start with the [overview](00-overview.md), then [Foundations](01-foundations.md), which everything else builds on.

## Contents

| Page | Subject |
| --- | --- |
| [00 Overview](00-overview.md) | The problem, how the design was made, the thirteen types and how to choose between them |
| [01 Foundations](01-foundations.md) | Colour, type, shapes, icons, line roles, animation (including the draw.io recipe), the two styles, spacing, naming and quality checks |
| [02 Screen flow](02-screen-flow.md) | Screens and the paths between them, fidelity levels, conditions, navigation patterns |
| [03 Flowchart](03-flowchart.md) | Steps and decisions, patterns, swimlanes, plain and illustrated, complete flows |
| [04 Sequence](04-sequence.md) | Messages in time: message kinds, fragments, a complete order from tap to rating |
| [05 ER diagram](05-er.md) | Tables, keys, cardinality, patterns, splitting a large schema by domain |
| [06 Architecture](06-architecture.md) | Parts and connections, patterns, a web app, the delivery system, a streaming platform |
| [07 Explainer](07-explainer.md) | Teaching one idea: layers, tree, comparison, concept, a complete card-payment explainer |
| [08 Planning](08-planning.md) | Gantt, org chart, mind map, Kanban and roadmap |
| [09 UML](09-uml.md) | State machine, use case and class diagram |
| [10 Wireframe](10-wireframe.md) | One screen: annotated, in four states and at three widths |
| [11 BPMN](11-bpmn.md) | Processes across teams and partners: pools, events, gateways, deadlines |
| [12 C4](12-c4.md) | One system at four levels of zoom |
| [13 Cloud, network, deployment](13-cloud.md) | Regions, networks, subnets, zones and trust levels |
| [14 DFD](14-dfd.md) | How data moves: four symbols, three levels, balancing |
| [15 Open items](15-open-items.md) | What is not designed, not tested, and what the review fixed |
| [16 Board index](16-board-index.md) | Every board on the canvas, with its picture |

## How each type page is built

1. **At a glance**: the question the type answers, when to use it and when not to.
2. **How to read one**, then the **conventions** with their reasons.
3. **The examples**, each with its picture and a walk-through of what to notice.
4. **Connections** to other types.
5. **What a plugin can rely on**.
6. **Reference**: the complete rules board for the type, copied word for word.

## Images

All pictures are in [`images/`](images/), one PNG per board, named after the board (`Sequence_Delivery.png`). They are screenshots of the design canvas at 1×, reduced to 256 colours to keep the repository small. Open one in its own tab to read small text.
