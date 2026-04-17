# Writing Subsystem Guides

This document defines how subsystem guides should be written in this style system.

Subsystem guides live as families under:

```
subsystems/<name>/
  README.md
  <leaf>.md
```

`README.md` is always the spine doc and the default starting point.

The goal is to produce modular execution context that helps a human or an agent implement the default shape of a subsystem reliably.

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

## Core rules

- Write for execution, not completeness theater.
- Define one default path before documenting variants.
- Prefer one canonical shape over several equivalent patterns.
- Use positive instructions by default.
- Use examples to compress explanation.
- Split optional material out when it weakens the main guide.

## Family structure

Every subsystem is a directory family.

Use this shape:

```
subsystems/
  service/
    README.md
    bootstrap-initialization.md
    lifecycle-hooks.md
    with-config.md
```

In this structure:

- the directory name is the subsystem name
- `README.md` is the spine doc
- sibling `.md` files are leaf docs

## Spine doc

`README.md` is the default retrieval target.

The spine doc should:

- define the subsystem's default shape
- contain the highest-priority instructions
- include the main canonical example
- link to leaf docs at the decision point
- make adjacent subsystem touchpoints obvious

Most spine docs should use roughly this structure:

1. title and purpose
2. use this when
3. owns
4. required instructions
5. canonical shape
6. canonical flow
7. canonical example
8. leaf docs
9. common touchpoints

## Leaf docs

Leaf docs own branches of the subsystem.

They should:

- own one branch each
- stay narrow and task-shaped
- assume the spine doc already defined the subsystem
- include only the local rules and example material needed for that branch

Use leaf docs for:

- optional integrations
- cross-subsystem integration points

Most leaf docs should use roughly this structure:

1. title and purpose
2. use this when
3. required instructions
4. local shape or flow
5. focused example

## Leaf naming

Use descriptive names for internal branches, such as:

- `bootstrap-initialization.md`
- `lifecycle-hooks.md`
- `serving.md`

Use `with-<other-subsystem>.md` for cross-subsystem docs, such as:

- `with-config.md`
- `with-service.md`
- `with-http-router.md`

## Branch reduction

Good subsystem docs reduce the number of plausible implementation paths.

That means:

- define one default path strongly
- isolate variants into separate docs
- avoid presenting many options in the same context unless the distinction matters

If a guide shows several roughly equal ways to do the same thing, it needs revision.

## Instruction budgeting

Instruction count matters, not just token count.

When writing a guide:

- state the most important rules plainly
- remove low-value repetition
- cut obvious inverses of the preferred pattern
- move optional material into leaf docs
- let examples carry part of the teaching load

When in doubt, ask:

- does this improve default execution?
- does this belong in the main path or only in a leaf doc?

## Positive and negative guidance

Do not include an `Anti-patterns` section by default.

Prefer positive rules.

Include negative guidance only when it prevents a mistake that is:

- easy to make
- costly to recover from
- not already prevented by the default path

## Non-goals

Do not include a `Non-goals` section by default.

Use it only when there is a real scope confusion that would otherwise cause bad retrieval or bad implementation.

## Examples

Examples are core teaching material.

Every spine doc should usually include at least one strong example that:

- shows the default shape clearly
- is realistic enough to imitate
- is short enough to scan quickly
- avoids unnecessary domain detail

Leaf docs should include only the example needed for that branch.

Use neutral names like `documents`, `projects`, `settings`, or `themes` unless a concrete package dependency is itself part of the rule.

## Cross-subsystem docs

When two subsystems touch, the detailed integration doc should usually live with the consuming subsystem.

Use this rule:

- if subsystem A consumes subsystem B, put the integration doc in A

That means the consumer owns the integration pattern by default.

The provider subsystem should usually mention the touchpoint briefly in its `README.md`, not duplicate the full integration guidance.

Use a separate subsystem family only when the crossover is a stable shared contract reused across multiple subsystems.

## Inline branch links

Do not rely on bottom-of-page related-guide lists.

When a branch matters, link to the relevant leaf doc where the reader would naturally need it.

Good:

- If startup must initialize durable mutable state explicitly, read `./bootstrap-initialization.md`.
- If this subsystem is being wired from config resolution, read `./with-config.md`.

## Source extraction

When extracting from old docs or example repos, preserve:

- the actual rules
- the ownership model
- the recurring flow shape
- the default path
- the meaningful branches
- the important subsystem touchpoints

Do not preserve:

- migration framing
- historical cleanup notes
- project-specific naming
- edge-case accumulation that does not belong in the default path

Write from the extracted rules, not from the old docs directly.

## Signs a guide is working

- the default path is obvious
- `README.md` is a clear starting point
- optional branches are isolated cleanly
- subsystem touchpoints are easy to discover
- examples are easy to imitate structurally
- a reader could implement a first pass from the spine doc alone

## Working rules

When in doubt:

- make the default path clearer
- reduce the number of instructions in `README.md`
- move optional material into a leaf doc
- prefer positive rules over negative lists
- add one stronger example instead of several weaker ones
- link outward at the decision point
- make subsystem touchpoints more obvious
