# Style System

This repository is the working home for an opinionated software style system.

The goal is to turn a set of broad style documents and reference projects into a clearer, more maintainable documentation system made up of:

- short foundation documents for cross-cutting principles
- targeted subsystem guides for specific architectural jobs
- reference material such as checklists and examples indexes

The intended outcome is a set of documents that make it easy to answer questions like:

- how should a CLI command tree be structured?
- how should a router and subrouter tree be composed?
- what should a config system look like?
- how should database adapter code be written?
- how should API tests be laid out?

## Why this exists

The original material in this repository captures a strong style, but much of it is currently organized as broad guides.

That is useful as source material, but not ideal for day-to-day use.

In practice, engineers usually need focused guidance for one subsystem at a time. This project exists to break the broader material into smaller, task-oriented guides that preserve the core style while making it easier to apply consistently.

## Current source material

The repository began with broad guides such as:

- `POLLINATOR_STYLE.md`
- `API_TEST_STYLE.md`
- `FRONT_END_STYLE.md`

There are also temporary reference inputs, including:

- `examples/`
- `CONFIG-SYSTEM-DESIGN.md`
- `COMMAND-GO-v040-MIGRATION.md`

These are source inputs for extraction and synthesis. They are not the desired final shape of the style system.

In particular:

- `examples/` is temporary and should not be treated as permanent documentation
- real project examples should be rewritten into concise generic examples before the temporary source material is removed
- migration framing should inform the rules, but should not become part of the final documentation voice

## Target documentation structure

The documentation system is being organized into three main areas:

### `foundations/`

Short cross-cutting guides for shared principles, such as:

- philosophy
- repository layout
- testing philosophy

### `subsystems/`

Focused guides for one architectural job at a time, such as:

- router composition
- config systems
- database adapters
- user accounts with Consent
- API tests
- server-rendered UI structure

These are the main working documents of the system.

### `reference/`

Supporting material such as:

- checklists
- examples indexes
- implementation notes

## Working documents

A few files act as internal control documents while the system is being built:

- `GUIDE_SYSTEM_PLAN.md`
  - outlines the overall document architecture
- `RULE_INVENTORY_MATRIX.md`
  - tracks the extracted rules, their future owners, and whether they are required, default, or optional patterns
- `meta/WRITING_SUBSYSTEM_GUIDES.md`
  - captures the writing standard for future subsystem guides
- `subsystems/TODO.md`
  - tracks which subsystem guides are drafted and which are still queued

## Project goal

The goal is not just to write nicer docs.

The goal is to codify the style in a form that is:

- easier to navigate
- easier to extend
- easier to apply consistently across projects
- less dependent on memory or oral tradition
- less dependent on reading real production repositories to infer intent

## Current state

This repository is still in the process of extraction and restructuring.

Some documents are legacy source material.
Some are new subsystem guides.
Some are planning and control documents used to drive the transition.

Over time, the center of gravity should move away from the legacy broad guides and toward the new foundation, subsystem, and reference structure.
