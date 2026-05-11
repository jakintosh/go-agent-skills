# Style Guide System Plan

This document turns the current style guides into a proposed system of smaller, task-oriented guides.

The goal is to make it easy to answer questions like:

- "How should a CLI command tree be structured?"
- "How do we build a clean API router with subrouters and middleware?"
- "What does a good service/store boundary look like?"
- "How should API tests be laid out?"
- "How do we structure a server-rendered HTMX UI?"

Instead of one large project-style document carrying everything, the system should separate:

- global principles that apply everywhere
- subsystem guides for specific architectural needs
- examples and checklists that help apply the style consistently

## What exists today

Current source documents:

- `POLLINATOR_STYLE.md`
- `FRONT_END_STYLE.md`
- `API_TEST_STYLE.md`

Current example sources:

- `examples/coalition`
- `examples/coffer`
- `examples/compass`
- `examples/consent`
- `examples/cosign`
- `examples/courier`

The examples are symlinks to sibling repositories and can be mined as reference implementations.

## Main observation

Right now the docs are split by broad area, but not yet by "job to be done."

`POLLINATOR_STYLE.md` in particular contains several distinct guides mixed together:

- repository layout
- CLI structure
- config and credential loading
- service construction
- store contracts
- router composition
- database adapter style
- API design
- testing
- build and automation

That is good source material, but not the ideal shape for adoption. A person usually needs one narrow answer at a time.

## Target document architecture

Use a three-layer system.

### 1. Foundations

These documents define rules that apply across many subsystems.

Candidate docs:

- `foundations/philosophy.md`
  - standard library bias
  - shallow architecture
  - explicit dependencies
  - clarity over cleverness
  - naming and error-string conventions
- `foundations/repository-layout.md`
  - when to use `cmd/`, `internal/`, `pkg/`, `testdata/`, `scripts/`
  - domain-oriented file naming
  - when to split files
- `foundations/testing-philosophy.md`
  - fast default suite
  - in-process over external network
  - deterministic setup
  - layering of unit/service/api/integration tests

These should be short and referenced by subsystem guides, not copied into them.

### 2. Subsystem guides

These are the core of the system. Each one should answer:

- when to use this pattern
- what files exist
- what responsibilities live where
- what handler/flow shape to follow
- what tests should exist
- what anti-patterns to avoid

Candidate first-class guides:

- `subsystems/cli-command-trees.md`
  - root command shape
  - global `args.Command` vars
  - command file layout
  - nested subcommand trees
  - handler phase ordering
  - config/env/client resolution

- `subsystems/config-and-credentials.md`
  - config dir defaults
  - env precedence
  - credential file loading
  - validation rules
  - what belongs in serve-time validation vs command defaults

- `subsystems/service-construction.md`
  - `Service` and `Options`
  - required dependency validation
  - `Start()` / `Stop()`
  - composition roots
  - explicit dependency injection

- `subsystems/store-contracts.md`
  - where interfaces live
  - how domain types and store methods relate
  - storage-representation naming
  - translation boundaries
  - compile-time conformance checks

- `subsystems/http-router-composition.md`
  - root mux vs domain routers
  - subrouter mounting
  - base-path mounting
  - middleware bundles
  - auth/cors/rate-limit placement
  - method+path registrations

- `subsystems/http-resource-handlers.md`
  - request/response struct placement
  - decode -> validate -> service -> encode flow
  - status mapping
  - error helpers
  - resource-path design

- `subsystems/database-adapters.md`
  - database package responsibilities
  - migration shape
  - SQLite defaults
  - SQL style
  - row scanning and domain conversion

- `subsystems/api/testing.md`
  - file naming
  - chunk comments
  - `internal/testutil`
  - request helper style
  - side-effect assertions
  - when to table-drive

- `subsystems/server-rendered-htmx-ui.md`
  - renderer setup
  - view model modules
  - full-page vs fragment paths
  - HTMX request context parsing
  - OOB strategy
  - progressive enhancement contract

- `subsystems/app-view-models.md`
  - per-concern `view_*.go`
  - pure mapping functions
  - presentation utilities
  - detail-panel and list-region patterns

- `subsystems/public-packages.md`
  - when `pkg/` is appropriate
  - `doc.go`
  - public API surface expectations

### 3. Reference material

These help application, not policy.

Candidate docs:

- `reference/checklists/cli.md`
- `reference/checklists/router.md`
- `reference/checklists/api-tests.md`
- `reference/checklists/frontend-htmx.md`
- `reference/examples.md`
  - map each example repo to the patterns it demonstrates well
  - also note where an example is partial or less ideal

## Recommended guide template

Every subsystem guide should use the same shape so readers know where to look.

Suggested template:

1. Purpose
2. When to use this guide
3. Non-goals
4. Canonical file/package shape
5. Core rules
6. Canonical flow
7. Testing expectations
8. Anti-patterns
9. Example repos/files
10. Related guides

This structure keeps documents self-contained without making them duplicate the whole style system.

## How to decide guide boundaries

A topic deserves its own guide if most of these are true:

- it solves a distinct architectural job
- it has a recognizable file/package shape
- it has repeatable flow rules
- it has specific test expectations
- someone could reasonably search for it directly

Examples:

- "CLI command trees" deserves a guide
- "router/subrouter composition" deserves a guide
- "API tests" deserves a guide
- "lowercase error strings" does not deserve a full guide; it belongs in foundations

## Proposed extraction map from the current docs

### From `POLLINATOR_STYLE.md`

Extract into:

- foundations/philosophy
- foundations/repository-layout
- subsystems/cli-command-trees
- subsystems/config-and-credentials
- subsystems/service-construction
- subsystems/store-contracts
- subsystems/http-router-composition
- subsystems/http-resource-handlers
- subsystems/database-adapters
- foundations/testing-philosophy
- subsystems/public-packages

Leave behind only a short "project blueprint" overview, or retire this document once the extracted guides exist.

### From `API_TEST_STYLE.md`

Keep as the seed for:

- subsystems/api/testing

Potentially split out:

- foundations/testing-philosophy
- reference/checklists/api-tests

### From `FRONT_END_STYLE.md`

Extract into:

- subsystems/server-rendered-htmx-ui
- subsystems/app-view-models

Potentially split out:

- reference/checklists/frontend-htmx

## Example repo mapping

This should eventually become a reference doc, but the early mapping is already useful.

- `coalition`
  - good CLI root and service/router split
  - good example of additive API router building
- `coffer`
  - strong command-tree example
  - good API test inventory
  - strong service/database/test layering
- `compass`
  - strong server-rendered HTMX example
  - clear renderer/view/template split
- `consent`
  - strong public `pkg/` example
  - good service/store boundary example
- `cosign`
  - strong app/view-model rendering example
  - good route registration by concern
- `courier`
  - strong middleware and subrouter composition example
  - good example of app-specific inner packages beyond service/database

## What needs to happen next

### Phase 1: Inventory and tagging

Read the current guides and convert each rule into a tagged inventory:

- foundation
- cli
- config
- service
- store
- router
- api-handler
- database
- frontend
- app-view
- testing
- public-pkg
- build

This is the key normalization step. It prevents accidental overlap and makes duplication visible.

### Phase 2: Define the minimum viable guide set

Start with a small set of high-value subsystem guides:

- CLI command trees
- HTTP router composition
- service construction
- store contracts
- API tests
- server-rendered HTMX UI

That is probably enough to prove the system without over-fragmenting it.

### Phase 3: Extract and rewrite

For each guide:

- pull only the rules relevant to that job
- rewrite for task-specific clarity
- add canonical file layout
- add a small end-to-end flow example
- link to related guides instead of repeating shared philosophy

### Phase 4: Add reference checklists

Create short implementation checklists after the subsystem docs stabilize.

These should be intentionally operational:

- "before merging a new CLI command"
- "before merging a new router subtree"
- "before merging API tests for a new endpoint"

### Phase 5: Curate examples

Build an examples index that says:

- which repo demonstrates which guide
- which files are best to read
- where each repo diverges from the desired style

This matters because some examples are "roughly in style" rather than canonical.

## Important guardrail

Do not let every subsystem guide re-explain the whole architecture.

Each targeted guide should:

- include only the cross-cutting rules needed to use it correctly
- link outward for shared philosophy
- stay narrow enough that someone can read it before implementing one feature

If a document starts teaching the whole project style again, it is too broad.

## Suggested first pass output

A good first milestone would be:

1. `foundations/philosophy.md`
2. `subsystems/cli-command-trees.md`
3. `subsystems/http-router-composition.md`
4. `subsystems/api/testing.md`
5. `subsystems/server-rendered-htmx-ui.md`
6. `reference/examples.md`

That set covers the clearest repeated patterns in the current material and examples.

## Open decisions to make together

These choices will shape the whole system:

1. Should there still be one short "project blueprint" document, or should the system be only small guides plus an index?
2. Do you want guides optimized around subsystems ("router composition") or around tasks ("adding a new protected API resource")?
3. Should example snippets live inside each guide, or should guides stay policy-only and point to example files?
4. Do you want this to read like strict standards, or like opinionated defaults with explicit escape hatches?

My current recommendation:

- keep one short blueprint/index
- make subsystem guides the primary unit
- include small inline examples, then link to real repos for larger ones
- write as strong defaults, with a short "when to deviate" section where needed
