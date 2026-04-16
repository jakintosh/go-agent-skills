# Integrating CLI root with `command-go/pkg/version`

**Pre-requisite:** ./building-a-cli.md (how to build a CLI in general)
**Package:** `git.sr.ht/~jakintosh/command-go@v0.4.2`

This guide defines how to use the `command-go` module to show version information on the CLI.

## Integration

The `command-go/pkg/version` extracts version information from git and generates a struct literal `VersionInfo`.

Here's an example of what the generated code looks like:
```go
var VersionInfo = version.Info{
    Version:   "v1.2.3",
    Commit:    "abc1234567890",
    BuildDate: "2024-01-15T10:30:45Z",
}
```

### Marker file

First create a generation marker file in `cmd/<bin>/generate_version.go`:
```go
//go:generate go run git.sr.ht/~jakintosh/command-go/pkg/version/generate

package main
```

## Build process

Update the Makefile/build script to call `go generate ./...` before building

```makefile
BIN_DIR := ./bin
APP := example

.PHONY: build test generate

build: generate
        mkdir -p $(BIN_DIR)
        go build -o $(BIN_DIR)/$(APP) ./cmd/$(APP)

generate:
        go generate ./...

test:
        go test ./...
```
## Root command in main.go

- If using `Config.Version`, update the field to use the generated `VersionInfo.Version` value
- Add the built-in `version.Command()` subcommand to the root-level Subcommands slice, passing in the generated `VersionInfo` as a parameter

```go
import "git.sr.ht/~jakintosh/command-go/pkg/version"

var rootCmd = &args.Command{
	Name: "example",
	Config: &args.Config{
		Version: VersionInfo.Version,
	},
	Options: []*args.Option{
		args.Option{
			Short: 'v',
			Long:  "verbose",
			Type:  args.OptionTypeFlag,
			Help:  "enable verbose output",
		},
	},
	Subcommands: []*args.Command{
		version.Command(VersionInfo),
	},
}
```

Once integrated, you'll be able to call `<bin> version (-v/--verbose)`, which will show either the short version tag (without `-v`), or a full version info with commit hash and build time (with `-v`).
