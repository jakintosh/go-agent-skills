# Local Testing With Consent

This guide defines the local and test shapes for Consent-backed apps that should not require a real Consent server.

Use it when wiring authenticated route tests, local browser development, account setup tests, CSRF tests, or a `--dev-auth` mode.

Assume [consent-user-shape.md](consent-user-shape.md) already defined the account model and `internal/web` auth boundary.

## Contents

- [Required Instructions](#required-instructions)
- [Dev Auth Mode](#dev-auth-mode)
- [Route Tests](#route-tests)
- [CSRF Tests](#csrf-tests)
- [Profile Fetch Tests](#profile-fetch-tests)

## Required Instructions

- Use `git.sr.ht/~jakintosh/consent/pkg/testing` for tests and local browser development.
- Inject `client.Verifier` into `internal/web` so tests can pass `*testing.TestVerifier`.
- Keep dev auth opt-in through an explicit flag or config setting.
- Mount dev login/logout handlers only in dev auth mode.
- Keep dev auth out of production route config.
- Use `TestVerifier.AuthenticatedRequest(...)` for read-route tests.
- Use `TestEnv` directly when tests need explicit access tokens, refresh tokens, CSRF secrets, subjects, or scopes.
- Fake `ProfileFetcher` separately when account setup logic needs profile responses.
- Keep tests in-process with `httptest` or the app router; do not start a real listener by default.

## Dev Auth Mode

For local browser development without a Consent server, build a test verifier and mount dev-only handlers.

```go
type DevAuth struct {
	Config AuthConfig
	Routes map[string]http.HandlerFunc
}

func buildDevAuthConfig() DevAuth {
	tv := testing.NewTestVerifier("localhost", "documents-dev")

	return DevAuth{
		Config: AuthConfig{
			Verifier:  tv,
			LoginURL:  "/dev/login",
			LogoutURL: "/dev/logout",
		},
		Routes: map[string]http.HandlerFunc{
			"/dev/login":  tv.HandleDevLogin(),
			"/dev/logout": tv.HandleDevLogout(),
		},
	}
}
```

When local pages require scoped profile data, use a shared test env with the same scopes the production authorize URL requests.

```go
env := testing.NewTestEnv("localhost", "documents-dev")
env.Scopes = []string{"identity", "profile"}
tv := testing.NewTestVerifierWithEnv(env)
```

The testing package always uses insecure cookies. Use it only for local development and tests.

## Route Tests

Construct the app with a `TestVerifier` through the same constructor path used by production tests.

```go
func TestProtectedRoute(
	t *testing.T,
) {
	tv := testing.NewTestVerifier("consent.example.com", "documents.example.com")
	web := NewTestWeb(t, AuthConfig{
		Verifier: tv,
		LoginURL: "/dev/login",
	})

	req, err := tv.AuthenticatedRequest("GET", "/documents", testing.DefaultTestSubject)
	if err != nil {
		t.Fatal(err)
	}
	rr := httptest.NewRecorder()

	web.Router().ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusOK)
	}
}
```

This keeps route tests local: no Consent server, no network token refresh, and no production key material.

## CSRF Tests

Use `TestEnv` directly when a mutation route needs a valid refresh-token secret.

```go
env := testing.NewTestEnv("consent.example.com", "documents.example.com")

accessToken, err := env.IssueAccessToken(testing.DefaultTestSubject, time.Hour)
if err != nil {
	t.Fatal(err)
}
refreshToken, err := env.IssueRefreshToken(testing.DefaultTestSubject, time.Hour)
if err != nil {
	t.Fatal(err)
}

form := url.Values{}
form.Set("csrf", refreshToken.Secret())
form.Set("title", "Launch notes")

req := httptest.NewRequest("POST", "/documents", strings.NewReader(form.Encode()))
req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
env.AddAuthCookies(req, accessToken, refreshToken)
```

Assert CSRF failures with a separate request that uses the same cookies and the wrong submitted `csrf` value.

## Profile Fetch Tests

Profile fetching is a separate app dependency. Use a tiny fake instead of running a Consent API.

```go
type fakeProfileFetcher struct {
	userInfo *client.UserInfo
	err      error
}

func (f fakeProfileFetcher) FetchUserInfo(
	accessToken string,
) (
	*client.UserInfo,
	error,
) {
	return f.userInfo, f.err
}
```

Use profile tests to cover:

- new account created from matching `userinfo.sub` and handle
- mismatched `userinfo.sub` rejected
- missing profile or handle rejected when profile is required
- existing account still usable when profile refresh fails
- handle conflict mapped to an account setup error

Keep those tests at the web/account boundary. Service tests should cover account input validation and store-error mapping without Consent tokens.
