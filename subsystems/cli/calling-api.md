# Calling an API from a CLI

**Pre-requisite:** `./README.md`
**Package:** `git.sr.ht/~jakintosh/command-go@v0.5.0`

Use this guide when a CLI command calls a JSON HTTP API with `command-go/pkg/wire`.

API-calling commands should still look like normal CLI commands: parse inputs, build a client, call one API operation, and print the result. Keep request construction and output formatting visible at the command boundary.

## Required

- Put API-calling commands under an obvious branch such as `api`.
- Put `wire.ClientOptions` on the API-calling branch.
- Use `envs.ResolveClient(...)` when the project uses named environments.
- Use `wire.Client` methods instead of hand-writing request, auth, envelope, and error handling.
- Marshal request DTOs explicitly in the handler or a narrow helper.
- Branch on `wire.HTTPError` helpers when status codes are part of the command behavior.
- Print API responses in one consistent format, usually JSON.
- Keep command handlers free of service or database construction.

## Local Shape

The default shape is:

1. root command owns environment selection with `envs.ConfigOptions`.
2. API branch owns `wire.ClientOptions`.
3. leaf handlers extract CLI input and build request DTOs.
4. handlers resolve a `wire.Client`.
5. handlers call `Get`, `Post`, `Put`, `Patch`, or `Delete`.
6. handlers format the response.

```go
var apiCommand = &args.Command{
	Name: "api",
	Help: "call the HTTP API",
	Options: wire.ClientOptions,
	Subcommands: []*args.Command{
		apiUserCommand,
	},
}
```

## Client Resolution

Use one small helper when several commands call the same API.

```go
func apiClient(
	i *args.Input,
) (
	wire.Client,
	error,
) {
	return envs.ResolveClient(i, DEFAULT_CFG, "/api/v1")
}
```

`envs.ResolveClient(...)` loads `environments.json`, applies `--env`, `CLI_ENV`, `--base-url`, and `--api-key`, then appends the API path prefix to the base URL.

If a project does not use `envs`, construct `wire.Client` from the project's config subsystem instead.

## Focused Example

```go
type CreateUserRequest struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

type UserDTO struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

var apiUserCreateCommand = &args.Command{
	Name: "create",
	Help: "create user",
	Operands: []args.Operand{
		{
			Name: "name",
			Help: "user name",
		},
		{
			Name: "email",
			Help: "user email",
		},
	},
	Handler: func(i *args.Input) error {
		req := CreateUserRequest{
			Name:  i.GetOperand("name"),
			Email: i.GetOperand("email"),
		}

		body, err := json.Marshal(req)
		if err != nil {
			return err
		}

		client, err := apiClient(i)
		if err != nil {
			return err
		}

		var user UserDTO
		if err := client.Post("/users", body, &user); err != nil {
			return err
		}

		return writeJSON(user)
	},
}
```

## Client Methods

Use the method-specific helpers for ordinary calls:

```go
err := client.Get("/users", &users)
err := client.Post("/users", body, &created)
err := client.Put("/users/"+id, body, nil)
err := client.Patch("/users/"+id, body, &updated)
err := client.Delete("/users/"+id, nil)
```

Use `client.Do(...)` only when the method-specific helper would make the handler less clear.

`wire.Client` automatically joins the base URL and path, sends bearer auth when `APIKey` is set, and decodes the standard wire envelope.

## HTTP Error Handling

For non-2xx responses, `wire.Client` returns a `wire.HTTPError`.

The error preserves:

- request URL
- status string and status code
- raw response body
- decoded wire API error, when the response used `wire.WriteError`
- decode error, when the response was not a valid wire envelope

Use the helper functions when command behavior depends on status:

```go
if err := client.Get("/documents/"+id, &doc); err != nil {
	if wire.IsStatus(err, http.StatusNotFound) {
		return fmt.Errorf("document %q not found", id)
	}
	return err
}
```

Use `AsHTTPError(...)` when the command needs details for diagnostics:

```go
if err := client.Post("/documents", body, &created); err != nil {
	httpErr, ok := wire.AsHTTPError(err)
	if ok && httpErr.APIError != nil {
		return fmt.Errorf("create document: %s", httpErr.APIError.Message)
	}
	return err
}
```

Available helpers:

```go
wire.AsHTTPError(err)
wire.IsHTTPError(err)
wire.IsStatus(err, http.StatusConflict)
wire.IsStatusClass(err, 500)
wire.StatusCode(err)
```

When the server returns envelope data with a non-2xx status, `wire.Client` decodes that data into the response value before returning the `HTTPError`. Use this only for intentional API contracts; ordinary failures should use the error envelope.
