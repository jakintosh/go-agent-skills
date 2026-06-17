# Contributing

This document describes how to work on the style system itself — guide structure, writing conventions, and what work remains.

## Structure

The style system has three areas:

- [`foundations/`](foundations/) — short cross-cutting guides for shared principles (philosophy, repository layout, testing philosophy).
- [`subsystems/`](subsystems/) — focused guides for one architectural job at a time (router composition, config, database adapters, etc.). These are the main working documents.
- [`reference/`](reference/) — supporting material such as checklists and examples indexes.

## Writing guides

### Guide families

Every subsystem is a directory family:

```
subsystems/
  service/
    README.md                   # spine doc
    bootstrap-initialization.md # leaf doc
    lifecycle-hooks.md          # leaf doc
    with-config.md              # cross-subsystem leaf doc
```

The directory name is the subsystem name. `README.md` is the spine doc — the default starting point and the highest-priority retrieval target. Sibling `.md` files are leaf docs that own one branch each.

### Spine docs

A spine doc should define the subsystem's default shape, contain the highest-priority instructions, include the main canonical example, link to leaf docs at the decision point, and make adjacent subsystem touchpoints obvious.

Most spine docs use roughly this structure:

1. Title and purpose
2. Use this when
3. Owns
4. Required instructions
5. Canonical shape
6. Canonical flow
7. Canonical example
8. Leaf docs
9. Common touchpoints

### Leaf docs

Leaf docs own branches of the subsystem. They should stay narrow and task-shaped, assume the spine doc already defined the subsystem, and include only the local rules and example material needed for that branch.

Most leaf docs use roughly this structure:

1. Title and purpose
2. Use this when
3. Required instructions
4. Local shape or flow
5. Focused example

### Naming

- Descriptive names for internal branches: `bootstrap-initialization.md`, `lifecycle-hooks.md`
- `with-<other-subsystem>.md` for cross-subsystem docs: `with-config.md`, `with-service.md`, `with-routing.md`

### Authoring principles

Optimize for:

- one strong default path
- progressive disclosure
- low instruction count
- low branching pressure
- examples that are easy to imitate

Do not optimize for:

- exhaustive coverage
- symmetrical section checklists
- large anti-pattern inventories
- long boundary disclaimers

Core rules:

- **Write for execution, not completeness theater.** Define one default path before documenting variants. Prefer one canonical shape over several equivalent patterns.
- **Use positive instructions by default.** Do not include an "Anti-patterns" section by default. Include negative guidance only when it prevents a mistake that is easy to make, costly to recover from, and not already prevented by the default path.
- **Use examples to compress explanation.** Every spine doc should include at least one strong example that shows the default shape clearly, is realistic enough to imitate, and is short enough to scan quickly. Use neutral names (`documents`, `projects`, `settings`, `themes`) unless a concrete dependency is itself part of the rule.
- **Split optional material when it weakens the main guide.** If a guide shows several roughly equal ways to do the same thing, it needs revision.
- **Instruction count matters.** State the most important rules plainly. Remove low-value repetition. Cut obvious inverses of the preferred pattern. Move optional material into leaf docs. Let examples carry part of the teaching load.

### Cross-subsystem docs

When two subsystems touch, the detailed integration doc lives with the consuming subsystem:

- If subsystem A consumes subsystem B, put the integration doc in A.
- The provider should mention the touchpoint briefly in its `README.md`, not duplicate the full integration guidance.
- Use a separate subsystem family only when the crossover is a stable shared contract reused across multiple subsystems.

Link to the relevant leaf doc where the reader would naturally need it, rather than relying on bottom-of-page related-guide lists.

### Review checklist

A guide is working when:

- the default path is obvious
- `README.md` is a clear starting point
- optional branches are isolated cleanly
- subsystem touchpoints are easy to discover
- examples are easy to imitate structurally
- a reader could implement a first pass from the spine doc alone

## Remaining work

### Foundations

The `foundations/` directory is still a placeholder. Three documents still need to be written, drawing from the rules below:

**`foundations/philosophy.md`** — core principles that apply everywhere.

Required rules:
- Prefer the standard library unless an external dependency removes meaningful code or risk.
- Keep architecture shallow and direct.
- Separate composition from behavior.
- Make dependencies explicit via options and constructors, not package globals.
- Favor clarity over cleverness and keep data flow obvious.
- Keep error strings lowercase and unpunctuated.
- JSON tags should use `snake_case`.
- Avoid package-level mutable state for stores and services.
- Avoid deep or overly generic abstractions when direct code is clearer.

Default rules:
- Optimize for author ergonomics and readability over abstraction depth.
- Prefer explicit names over abbreviations.
- Use one operation per statement and avoid dense chaining.

**`foundations/repository-layout.md`** — how to place files and packages.

Required rules:
- Prefer domain-oriented naming so engineers can find behavior quickly.

Default rules:
- Keep related behavior local until size or clarity justifies a split.
- Use `internal/` as the default home for application code.

**`foundations/testing-philosophy.md`** — shared testing principles.

Required rules:
- Use short, deterministic default test setups and avoid external dependencies in default suites.
- Keep the default test suite fast and hermetic; isolate true integrations behind explicit boundaries.

### Reference checklists

The `reference/checklists/` directory is also a placeholder. Candidate checklists to write:

- adding a new CLI command
- mounting a new router subtree
- writing API tests for a new endpoint

An examples index (mapping projects to the patterns they demonstrate) could live in `reference/` as well.

## Future meta instructions

This document is the right place for any additional conventions about working on the style system — for example:

- how to propose a new subsystem guide
- when to deprecate or remove a guide
- review process for guide changes
- tooling or automation expectations
