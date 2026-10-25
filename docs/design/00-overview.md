# Flow design: overview

This folder is the design document for **Flow**, a set of AI plugins that draw diagrams in [draw.io](https://www.drawio.com/). It records every decision made on the design canvas, in words and in pictures, so that the plugins can be written against a written specification instead of against someone's memory of what the canvas looked like.

Nothing here is code. The plugins, the draw.io XML they will write and the plugin interface come after this document.

## 1. What problem the design solves

An AI that is asked for "a diagram of the order flow" has to decide a hundred small things: what shape stands for a decision, which way arrows run, how far apart boxes sit, which colour belongs to the courier, whether a label may touch a border. If it decides them differently each time, every diagram looks like it came from a different tool and none of them is pleasant to edit afterwards.

The design fixes those decisions once, for every diagram type, in a way a person can read and a plugin can follow:

- **One visual family.** A flowchart, an ER diagram and a cloud map share the same palette, icons, line roles and spacing. The same thing keeps the same name, tint and icon wherever it appears: the courier is teal in the flowchart lane, the sequence participant, the ER table header and the architecture box.
- **Written rules per type.** Each type has a rules page that says what a box is, what a line means, how far things sit apart and what the plugin can rely on.
- **Worked examples at three sizes.** A small one that shows one idea, a complete delivery-platform one that shows the type used for real, and, for many types, a large or complex one that shows what happens when the subject is big.
- **Two styles.** *Plain* (shapes and text, the default) and *illustrated* (cards with a large icon, for readers outside the team).

## 2. How the design was made

The work followed one loop, one diagram type at a time:

1. **Rules and notation first**, written as a reference board.
2. **A small example** to test that the rules hold on a simple case.
3. **A complete example** on one shared subject, a food-delivery platform, so the types can be compared with each other.
4. **A complex example** where the type's weak spots show (a large streaming platform, a four-level mind map, a five-participant BPMN collaboration).
5. **Review on the canvas**, then fixes. Overlaps, labels sitting on borders and arrows running backwards were found this way and corrected. An automatic check now looks for the same problems before each publish (see [Quality checks](01-foundations.md#10-quality-checks)).

The shared subject matters. Because every type draws the same business (customers order food from restaurants, couriers deliver it, a payment provider charges the card), you can read the sequence diagram, the ER diagram and the architecture diagram of that business side by side and see the same names, tints and icons in each.

## 3. The diagram types

| # | Type | Question it answers | Page |
| --- | --- | --- | --- |
| 1 | Screen flow | How does a person move between the screens of an app? | [02](02-screen-flow.md) |
| 2 | Flowchart | What are the steps of a process, and what decides between them? | [03](03-flowchart.md) |
| 3 | Sequence | Who says what to whom, in what order? | [04](04-sequence.md) |
| 4 | ER | What data is stored, and how are the tables related? | [05](05-er.md) |
| 5 | Architecture | What parts make up the system, and what talks to what? | [06](06-architecture.md) |
| 6 | Explainer | How do I teach one idea to someone outside the field? | [07](07-explainer.md) |
| 7 | Planning | Who does what by when (Gantt, org chart, mind map, Kanban, roadmap)? | [08](08-planning.md) |
| 8 | UML | What states does a thing pass through, who uses the system, how are classes related? | [09](09-uml.md) |
| 9 | Wireframe | What is on one screen, and where? | [10](10-wireframe.md) |
| 10 | BPMN | How does a business process run across several teams and partners? | [11](11-bpmn.md) |
| 11 | C4 | What is the system, at four levels of zoom? | [12](12-c4.md) |
| 12 | Cloud, network, deployment | Where does it run, and how is it joined together? | [13](13-cloud.md) |
| 13 | DFD | How does data move through the system? | [14](14-dfd.md) |

Not designed yet: **editing** an existing `.drawio` file (changing or restyling a diagram that already exists). See [Open items](15-open-items.md).

### Choosing between look-alike types

Several types overlap, and picking the right one is half the work. The short guide:

| If the subject is... | Use | Not |
| --- | --- | --- |
| A sequence of steps and decisions for one actor or team | Flowchart | BPMN, which is for several participants with messages between them |
| Steps that cross teams or companies, with deadlines, parallel work or partners shown as black boxes | BPMN | A swimlane flowchart, which cannot say "wait for a message" or "repeat for each item" |
| The order of messages between systems over time | Sequence | An architecture diagram, which shows structure but not order |
| The parts of a system and their connections | Architecture | C4, if you need a fixed vocabulary and levels |
| One system seen at several levels of detail for different readers | C4 | A single huge architecture diagram |
| Machines, networks and where things run | Cloud / network | Architecture, which does not show regions, subnets or trust levels |
| What happens to data, and where it rests | DFD | A flowchart, which shows control rather than data |
| Screens and the paths between them | Screen flow | A flowchart of screens, which loses the device frames |
| The contents of one screen | Wireframe | A screen flow, which shows how screens connect |
| An idea for a reader who is not an engineer | Explainer | Any technical type |

## 4. How to read this document

- Start with [Foundations](01-foundations.md). It covers everything the types share, and every type page assumes it.
- Then read the page of the type you need. Every type page has the same shape:
  1. **At a glance**: what the type answers, when to use it, when not to.
  2. **How to read one**: the anatomy of a diagram, in plain words.
  3. **Conventions**: the rules that matter most, explained with their reasons.
  4. **The examples**: each board with a picture and a walk-through of what to notice.
  5. **Connections to other types**.
  6. **What a plugin can rely on**.
  7. **Reference**: the complete rules board, copied word for word.
- Every picture is a screenshot of a board on the design canvas, so lines that are animated on the canvas look static here. The text says which lines are animated and how fast.
- Full-size images are in [`images/`](images/). The pictures on the pages are the same files; open one in its own tab to read small text.

## 5. Status of the document

The design is complete for the thirteen types above and not yet for editing existing files. The known gaps and the things that have not been tested are collected in [Open items](15-open-items.md), so that nobody assumes more than has been checked.
