# Project Actions

This guide defines the standard shape for a project's local action surface.

It focuses on how common build and setup tasks are exposed to engineers, and how automation should compose the public CLI rather than bypass it with private scripts.

The goal is to make project actions:

- easy to discover
- thin and predictable
- aligned with the real runtime interfaces of the application
- convenient without hiding important behavior

## When to use this guide

Use this guide when you are:

- deciding what belongs in the `Makefile`
- adding a one-command local setup flow
- reviewing whether automation is bypassing the application's public CLI

## Non-goals

This guide does not define:

- CI pipeline design
- deployment automation
- command-tree internals
- repository layout beyond the local action surface

This topic may eventually move into foundations, but the rules are still worth documenting.

## Core rules

- Use the `Makefile` as the primary local action surface by default.
- Provide `build`, `test`, and `install` targets at minimum.
- Prefer thin automation that composes public CLI commands over private setup scripts.
- Keep setup flows understandable as a sequence of normal application commands.

## What this subsystem is for

A good local action surface helps an engineer answer:

- how do I build the binary?
- how do I run the default test suite?
- how do I install the tool locally?
- how do I bootstrap a runnable local instance?

If the answers live in a mix of hidden scripts, undocumented shell snippets, and tribal knowledge, the project action surface is too weak.

## Canonical shape

A good default `Makefile` includes:

- `build`
- `test`
- `install`
- optional setup flows such as `init`

For example:

```make
build:
	go build ./cmd/docsvc

test:
	go test ./...

install:
	go install ./cmd/docsvc

init:
	docsvc config init
	docsvc init
```

The important idea is not the exact target names. The important idea is that the `Makefile` exposes the common local actions in one obvious place.

## Thin automation

Prefer automation that composes the public CLI.

For local setup, that often means:

1. build or install the binary
2. generate config through `config init`
3. initialize mutable runtime state through `init`
4. optionally register local environment state through another public command

This keeps:

- documentation honest
- debugging easier
- operational flows reproducible without `make`

If a workflow only works through a private script, it is harder to understand and harder to trust.

## Relationship to the CLI

The `Makefile` should be a convenience layer over the real command surface, not a replacement for it.

That means:

- engineers should be able to run the underlying commands directly
- make targets should not hide important side effects
- setup automation should call stable public commands rather than internal helper scripts when possible

This is especially important for initialization flows, where the CLI should remain the authoritative operational interface.

## Testing expectations

Project actions should be easy to verify informally and, when needed, through focused checks for:

- presence of core targets
- correctness of the composed public commands
- local setup flows remaining aligned with current CLI behavior

The value here is not elaborate test coverage. The value is keeping the action surface simple enough that drift is easy to notice.

## Anti-patterns

- relying on undocumented shell snippets instead of a visible action surface
- hiding primary setup behavior in private scripts when the CLI could expose it directly
- `make` targets that perform surprising side effects without clear names
- local automation that diverges from the public operational commands

## Related guides

- `cli-command-trees.md`
- `config/README.md`
- `service-construction.md`
