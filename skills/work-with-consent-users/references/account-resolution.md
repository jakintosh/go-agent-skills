# Resolving Accounts From Consent

This guide defines the default `internal/web` shape for turning Consent-issued cookies into a local account context.

Use it when rendering user-aware pages, creating local accounts on first login, refreshing cached Consent profile data, protecting mutations with CSRF, or passing account IDs into service methods.

Assume [consent-user-shape.md](consent-user-shape.md) already defined the account table, service boundary, and server-side Consent client construction.

## Contents

- [Required Instructions](#required-instructions)
- [Local Shape](#local-shape)
- [Read Context Flow](#read-context-flow)
- [Account Setup](#account-setup)
- [Mutation Flow](#mutation-flow)
- [Logout URLs](#logout-urls)

## Required Instructions

- Keep `internal/web` dependent on `client.Verifier`, not `*client.Client`.
- Resolve a local account after successful token verification.
- Use `accessToken.Subject()` as the lookup key for `accounts.consent_subject`.
- Create the local account lazily on first successful login.
- Fetch Consent profile data only when the app requested and needs the `profile` scope.
- Require a matching `userinfo.sub` before trusting returned profile data.
- Treat profile fetch failure for an existing account as a refresh miss when cached data is still usable.
- Treat profile fetch failure for a new account as account setup failure when profile data is required.
- Use the returned local account ID for all service calls.
- Return unauthenticated context for missing or invalid read cookies, and explicit errors for account setup failures.
- Validate CSRF through `VerifyAuthorizationCheckCSRF` before state-changing service calls.

## Local Shape

Use a narrow auth config and a request-local view context.

```go
type AuthConfig struct {
	Verifier client.Verifier
	ProfileFetcher interface {
		FetchUserInfo(accessToken string) (*client.UserInfo, error)
	}
	ProfileRefreshInterval time.Duration
	LoginURL               string
	LogoutURL              string
}

type AuthContext struct {
	IsAuthenticated bool
	AccountID       string
	Subject         string
	Handle          string
	CSRFToken       string
	LoginURL        string
	LogoutURL       string
}
```

The web constructor should validate `Auth.Verifier` just like it validates the service dependency.

```go
type Options struct {
	Service *service.Service
	Auth    AuthConfig
}

func New(
	opts Options,
) (
	*Web,
	error,
) {
	if opts.Service == nil {
		return nil, errors.New("web: service required")
	}
	if opts.Auth.Verifier == nil {
		return nil, errors.New("web: auth verifier required")
	}

	return &Web{
		service: opts.Service,
		auth:    opts.Auth,
	}, nil
}
```

## Read Context Flow

Use read verification for pages that may render state-changing controls.

```go
func (w *Web) resolveAuthContext(
	rw http.ResponseWriter,
	r *http.Request,
) (
	AuthContext,
	error,
) {
	ctx := AuthContext{
		LoginURL:  w.loginURL(r),
		LogoutURL: w.auth.LogoutURL,
	}

	accessToken, csrf, err := w.auth.Verifier.VerifyAuthorizationGetCSRF(rw, r)
	if err != nil {
		return ctx, nil
	}

	account, err := w.accountForToken(accessToken)
	if err != nil {
		return ctx, err
	}

	ctx.IsAuthenticated = true
	ctx.Subject = accessToken.Subject()
	ctx.AccountID = account.ID
	ctx.Handle = account.Handle
	ctx.CSRFToken = csrf
	ctx.LogoutURL = logoutURL(w.auth.LogoutURL, csrf)
	return ctx, nil
}
```

Use this context for login/logout controls, ownership checks, and hidden CSRF form fields. A page can render logged-out state when token verification fails, but it should render an account setup error when token verification succeeds and local account resolution fails.

## Account Setup

Account setup should use the Consent subject first and scoped profile data second.

```go
func (w *Web) accountForToken(
	accessToken *client.AccessToken,
) (
	*service.Account,
	error,
) {
	subject := accessToken.Subject()

	account, err := w.service.GetAccountBySubject(service.GetAccountBySubjectInput{
		Subject: subject,
	})
	if err == nil && !w.shouldRefreshProfile(account) {
		return account, nil
	}
	if err != nil && !errors.Is(err, service.ErrNotFound) {
		return nil, err
	}

	handle := subject
	refreshedAt := time.Now()
	if w.auth.ProfileFetcher != nil {
		userInfo, err := w.auth.ProfileFetcher.FetchUserInfo(accessToken.Encoded())
		if err != nil {
			if account != nil {
				return account, nil
			}
			return nil, err
		}
		if userInfo == nil || userInfo.Sub != subject || userInfo.Profile == nil {
			return nil, ErrAccountSetup
		}
		handle = strings.TrimSpace(userInfo.Profile.Handle)
		if handle == "" {
			return nil, ErrAccountSetup
		}
	}

	return w.service.UpsertAccount(service.UpsertAccountInput{
		Subject:     subject,
		Handle:      handle,
		RefreshedAt: refreshedAt,
	})
}
```

If profile data is optional, leave `ProfileFetcher` nil and use a non-public display fallback. If profile data is required for user-facing URLs, require the `profile` scope in the authorize URL and surface setup failures clearly.

## Mutation Flow

Use one helper for mutation routes so authorization, CSRF, and account resolution stay consistent.

```go
func (w *Web) requireAuth(
	rw http.ResponseWriter,
	r *http.Request,
) (
	AuthContext,
	bool,
) {
	csrf := r.FormValue("csrf")
	if csrf == "" {
		csrf = r.URL.Query().Get("csrf")
	}

	accessToken, newCSRF, err := w.auth.Verifier.VerifyAuthorizationCheckCSRF(rw, r, csrf)
	if errors.Is(err, client.ErrCSRFInvalid) {
		http.Error(rw, "CSRF validation failed", http.StatusForbidden)
		return AuthContext{}, false
	}
	if err != nil {
		http.Error(rw, "Unauthorized", http.StatusUnauthorized)
		return AuthContext{}, false
	}

	account, err := w.accountForToken(accessToken)
	if err != nil {
		w.renderAccountSetupError(rw, r, err)
		return AuthContext{}, false
	}

	return AuthContext{
		IsAuthenticated: true,
		Subject:         accessToken.Subject(),
		AccountID:       account.ID,
		Handle:          account.Handle,
		CSRFToken:       newCSRF,
		LoginURL:        w.loginURL(r),
		LogoutURL:       logoutURL(w.auth.LogoutURL, newCSRF),
	}, true
}
```

Handlers should call the service with `auth.AccountID`.

```go
func (w *Web) handleCreateDocument(
	rw http.ResponseWriter,
	r *http.Request,
) {
	auth, ok := w.requireAuth(rw, r)
	if !ok {
		return
	}

	input := service.CreateDocumentInput{
		AccountID: auth.AccountID,
		Title:     r.FormValue("title"),
	}
	doc, err := w.service.CreateDocument(input)
	if err != nil {
		w.writeError(rw, err)
		return
	}

	http.Redirect(rw, r, "/documents/"+url.PathEscape(doc.ID), http.StatusSeeOther)
}
```

## Logout URLs

Consent's logout handler validates the submitted CSRF value against the refresh-token secret. Build logout controls from the current auth context.

```go
func logoutURL(
	base string,
	csrf string,
) string {
	if base == "" || csrf == "" {
		return base
	}
	u, err := url.Parse(base)
	if err != nil {
		return base
	}
	q := u.Query()
	q.Set("csrf", csrf)
	u.RawQuery = q.Encode()
	return u.String()
}
```

Use POST logout forms when the UI already has form affordances for account actions. A GET link is acceptable only when it points to Consent's package logout handler with the current CSRF value included.
