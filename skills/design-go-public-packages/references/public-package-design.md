# Public Packages

This guide defines when a package belongs in `pkg/` and what standards apply once a package is intentionally public.

It focuses on packages that are meant to be reused outside the application itself, not internal convenience packages that happen to be importable.

The goal is to make public packages:

- deliberate
- small and understandable
- documented enough to use correctly
- clearly separated from application internals

## Contents

- [When to use this guide](#when-to-use-this-guide)
- [Non-goals](#non-goals)
- [Core rules](#core-rules)
- [The decision test](#the-decision-test)
- [What good public packages look like](#what-good-public-packages-look-like)
- [Documentation expectations](#documentation-expectations)
- [API design expectations](#api-design-expectations)
- [Canonical shape](#canonical-shape)
- [Generic example](#generic-example)
- [Testing expectations](#testing-expectations)
- [Anti-patterns](#anti-patterns)
- [Related guides](#related-guides)

## When to use this guide

Use this guide when you are:

- deciding whether code belongs in `internal/` or `pkg/`
- designing a reusable client, token, or helper library
- reviewing whether an existing package is truly part of the public API surface

## Non-goals

This guide does not define:

- the internal repository layout for application code
- how service or database packages should be structured
- whether every project must expose a public package

Many projects should have no `pkg/` directory at all.

## Core rules

- Use `pkg/` only for deliberately reusable external APIs.
- Keep public packages small and purpose-built.
- Include `doc.go` with package-level documentation and usage guidance.
- Keep exported interfaces and types narrow and documented.
- Keep application-specific internals in `internal/`, even if reuse feels possible.

## The decision test

Code belongs in `pkg/` only when all of these are true:

- external consumers are a real intended audience
- the API can remain stable enough to support reuse
- the package can be understood without importing the whole application
- the exported surface is worth documenting as a product, not just as an implementation detail

If the answer is uncertain, keep the code in `internal/`.

`pkg/` should represent an intentional compatibility boundary, not a staging area for code that might be reusable someday.

## What good public packages look like

A good public package usually has:

- one clear responsibility
- a small exported surface
- package documentation that explains when to use it
- examples or usage guidance that show the happy path
- minimal assumptions about the containing application

Common candidates include:

- API clients
- token or signing helpers
- well-bounded protocol utilities

Poor candidates include:

- service-layer helpers tied to one app's domain model
- packages that depend on many internal repository details
- partially generalized code extracted only to "clean up" `internal/`

## Documentation expectations

Every public package should include a `doc.go` file.

That documentation should explain:

- what the package is for
- the main entry points
- important expectations or constraints
- a short usage sketch when helpful

The point is not volume. The point is that a new reader should not need to open several source files just to learn how to start.

## API design expectations

Public APIs should be narrower and more stable than internal ones.

Prefer:

- small exported interfaces
- explicit constructors
- obvious option types
- stable data contracts
- documented error behavior where it matters

Be more conservative about exporting names from `pkg/` than from `internal/`.

If an exported type or interface would be hard to support over time, it probably should not be public.

## Canonical shape

A typical public package might look like:

```text
pkg/client/
  doc.go
  client.go
  options.go
  types.go
```

This shape keeps:

- documentation at the package boundary
- constructors and core behavior easy to find
- option and type contracts explicit

The exact filenames may vary, but the package should read like a small library, not like a slice of application internals copied into `pkg/`.

## Generic example

```go
// Package client provides a small HTTP client for the theme service API.
//
// It is intended for command-line tools and other Go services that need to
// list, fetch, and publish themes through the public API.
package client

type Options struct {
	BaseURL string
	Token   string
}

type Client struct {
	baseURL string
	token   string
}

func New(opts Options) (*Client, error) {
	if opts.BaseURL == "" {
		return nil, errors.New("base url is required")
	}
	return &Client{
		baseURL: opts.BaseURL,
		token:   opts.Token,
	}, nil
}
```

This is a good `pkg/` candidate because:

- the audience is external callers
- the responsibility is narrow
- the constructor contract is explicit
- the package can stand on its own

## Testing expectations

Public packages should have focused tests for:

- documented constructors and option validation
- core exported behavior
- the small public contracts other code will rely on

Tests should reinforce that the exported API is intentional and supportable.

## Anti-patterns

- moving code to `pkg/` only because it is large
- exporting broad interfaces that mirror internal application structure
- omitting package docs and expecting readers to infer usage from tests
- leaking internal repository assumptions through public types
- treating `pkg/` as the default home for non-main code

## Related guides

- [Go service guidance](../../work-with-go-services/SKILL.md)
- [Go HTTP API guidance](../../work-with-go-http-apis/SKILL.md)
