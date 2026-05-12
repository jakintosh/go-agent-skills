# Writing Makefiles

This guide defines the default Makefile style for local project workflows.

Use this when creating or reviewing a `Makefile`. The goal is to make build, test, setup, run, install, and cleanup workflows discoverable in one conventional place.

## Required Instructions

- Use the `Makefile` as the primary local action surface by default.
- Put repeated paths, binary names, tool names, ports, URLs, and local inputs in variables at the top.
- Use `:=` for internal constants and `?=` for values a local user may override.
- Set `.DEFAULT_GOAL := help`.
- Declare phony targets explicitly.
- Make recipe commands visible by default.
- Provide `help`, `build`, `test`, and `clean`.
- Provide `install` when the project has a CLI binary.
- Provide `run` when the project has a long-running local service.
- Provide `init` when the project needs local config, data, secrets, or environment records.
- Use `reset` or another clearly destructive name for removing local runtime state.
- Keep `clean` limited to build and test artifacts.
- Prefer public CLI commands over private setup scripts.
- Run `go generate ./...` from `build` when generated code may affect the build.

## Canonical Shape

For a Go service project with a CLI binary, use a shape like:

```make
GO := go
BIN_DIR := ./bin
APP := documents
BIN := $(BIN_DIR)/$(APP)
CONFIG_DIR := ./config
DATA_DIR := ./data
PORT ?= 8080
BASE_URL ?= http://localhost:$(PORT)

.DEFAULT_GOAL := help

.PHONY: help build generate test fmt vet lint install init run clean reset

help:
	printf "Targets:\n"
	printf "  build    Build $(BIN)\n"
	printf "  test     Run tests\n"
	printf "  install  Install the CLI binary\n"
	printf "  init     Create local config and data\n"
	printf "  run      Run the local service\n"
	printf "  clean    Remove build and test artifacts\n"
	printf "  reset    Remove local runtime state\n"

build: generate
	mkdir -p $(BIN_DIR)
	$(GO) build -o $(BIN) ./cmd/$(APP)

generate:
	$(GO) generate ./...

test:
	$(GO) test ./...

fmt:
	$(GO) fmt ./...

vet:
	$(GO) vet ./...

lint: fmt vet

install:
	$(GO) install ./cmd/$(APP)

init: build
	mkdir -p $(CONFIG_DIR) $(DATA_DIR)
	$(BIN) config init \
		--config-dir $(CONFIG_DIR) \
		--data-dir $(DATA_DIR) \
		--base-url $(BASE_URL) \
		--port $(PORT)
	$(BIN) init \
		--config-dir $(CONFIG_DIR) \
		--data-dir $(DATA_DIR)

run: init
	$(BIN) serve \
		--config-dir $(CONFIG_DIR) \
		--data-dir $(DATA_DIR)

clean:
	rm -rf $(BIN_DIR) coverage.out

reset:
	rm -rf $(CONFIG_DIR) $(DATA_DIR)
```

The example is intentionally complete. Smaller projects should keep the same shape and include only the targets their workflows actually use. Start with at least `help`, build`, `test`, and `lint`, and add from there as needed.

## Target Names

Use stable names for common workflows:

- `help`: list available targets
- `build`: build the project or default binary
- `generate`: refresh generated source or assets
- `test`: run the default test suite
- `fmt`: format source
- `vet`: run static analysis
- `lint`: run formatting and static checks when the project uses that name
- `install`: install the CLI binary
- `init`: create a runnable local instance
- `run`: run the built local service
- `serve`: run development infrastructure when that is the established local verb
- `clean`: remove build and test artifacts
- `reset`: remove local runtime state

For multiple binaries, keep the vanilla targets pointed at the obvious default binary and add namespaced targets for the rest:

```make
build: api-build

api-build:
	go build -o $(API_BIN) ./cmd/api

worker-build:
	go build -o $(WORKER_BIN) ./cmd/worker
```

## Variables

Variables should make repeated values easy to scan and override. Use `:=` for project constants such as `BIN_DIR`, `APP`, `BIN`, `CONFIG_DIR`, and `DATA_DIR`. Use `?=` for local knobs such as ports, URLs, tool paths, database paths, and optional inputs.

## Help

Every Makefile should make `help` the default target. Keep help text short enough to scan and specific enough that someone can choose the right target without opening another document.

## Build and Generate

For Go projects with generated code, make `build` depend on `generate`. Make can track generated files when the inputs and outputs are explicit and stable. Most Go generation workflows are simpler to keep correct by running generation before building when generated code participates in the build.

## Test and Checks

Keep `test` focused on the default test suite. In Go projects, `go test ./...` already compiles tested packages, so a separate `build` target remains available for checking the final binary artifact.

## Install

If the project exposes a CLI binary, provide `install`. For Go CLI projects, the default install recipe is `go install ./cmd/$(APP)`.

## Init and Run

Use `init` for making a local instance runnable. It should compose the same public commands an engineer could run by hand: create config, initialize mutable state, and register local environment or credential records.

Use the built binary for `run`. `run` should bring the project to a runnable local state in one command.

If the project depends on Docker Compose for development infrastructure, keep the same target names and let the recipes call Docker:

```make
build:
	docker compose run --rm build

run:
	docker compose up web

test:
	docker compose run --rm test
```

## Clean and Reset

Use `clean` for build and test artifacts. Use `reset`, `reset-local`, or another clearly destructive name for local runtime state such as config, data, var directories, mock deployments, local databases, or secrets.

## Long Recipes

Keep ordinary targets direct. Long shell recipes are acceptable when the workflow is genuinely orchestration-heavy, such as a mock deployment, multi-process demo environment, readiness loop, or log-managed local stack.

When extracting a long recipe improves readability, reuse, or testing, move the detailed orchestration into a script and keep the Makefile as the entry point:

```make
demo: build
	./scripts/demo
```
