# Integrating CLI Root with `command-go/pkg/version`

**Pre-requisite:** `./README.md`
**Package:** `git.sr.ht/~jakintosh/command-go@v0.5.0`

Use this guide when a binary should expose build metadata through a standard `version` subcommand.

The `version` package generates a package-level `VersionInfo` value from git metadata and provides `version.Command(VersionInfo)` for the CLI tree.

## Required

- Add one `generate_version.go` marker file in each main binary package.
- Run `go generate ./...` before building.
- Pass the generated `VersionInfo` to `version.Command(...)`.
- Use `VersionInfo.Version` for `args.Config.Version`.
- Define `--verbose` at the root when the version command should print commit and build date.
- Ignore generated `version_generated.go` files unless the project intentionally commits generated code.

## Marker File

Create `cmd/<bin>/generate_version.go`:

```go
//go:generate go run git.sr.ht/~jakintosh/command-go/pkg/version/generate

package main
```

Running `go generate ./...` creates `version_generated.go` in the same package.

The generated value has this shape:

```go
var VersionInfo = version.Info{
	Version:   "v1.2.3",
	Commit:    "abc1234567890",
	BuildDate: "2024-01-15T10:30:45Z",
}
```

## Root Command

Wire the version value into both root metadata and the command tree.

```go
import (
	"git.sr.ht/~jakintosh/command-go/pkg/args"
	"git.sr.ht/~jakintosh/command-go/pkg/version"
)

var rootCmd = &args.Command{
	Name: "example",
	Config: &args.Config{
		Version: VersionInfo.Version,
		HelpOption: &args.HelpOption{
			Short: 'h',
			Long:  "help",
		},
	},
	Options: []args.Option{
		{
			Short: 'v',
			Long:  "verbose",
			Type:  args.OptionTypeFlag,
			Help:  "enable verbose output",
		},
	},
	Subcommands: []*args.Command{
		version.Command(VersionInfo),
		serveCommand,
	},
}
```

The `version` command responds to a long option named `verbose`, but it does not define that option itself. Define `-v`/`--verbose` at the root so it inherits into the version command.

## Build Process

Run generation before every build:

```makefile
BIN_DIR := ./bin
APP := example

.PHONY: build generate test

build: generate
	mkdir -p $(BIN_DIR)
	go build -o $(BIN_DIR)/$(APP) ./cmd/$(APP)

generate:
	go generate ./...

test:
	go test ./...
```

For multiple binaries, each `cmd/<bin>` package should have its own marker file. A single `go generate ./...` pass will generate one `version_generated.go` beside each marker.

## Command Behavior

```text
$ example version
v1.2.3

$ example version --verbose
version:  v1.2.3
commit:   abc1234567890
built:    2024-01-15T10:30:45Z
```

The generator uses git tags, commit hashes, and build timestamps. Build environments such as CI or Docker must run with enough git metadata available for the desired version string.
