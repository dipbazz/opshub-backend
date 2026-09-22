# Security

This is a portfolio project, not a production SaaS handling real customer
data — but the security decisions below are made the way they would be for
one, since defending them is the point of the exercise. Written
incrementally as each piece lands (see `docs/architecture.md` for how this
fits the overall request flow); this is not a Day 7 reconstruction.

## Tenant isolation

Every tenant's data must be unreachable by every other tenant, enforced at
the application layer, not just hidden in the UI.

- **Queryset-level**: `tenants.mixins.TenantScopedQuerySetMixin` overrides
  `get_queryset()` on any view that uses it, filtering to
  `tenant=request.user.tenant_id` before any other lookup runs. A user can
  never even discover another tenant's object exists (404, not 403, on a
  cross-tenant ID guess) — see `tenants/tests/test_mixins.py`.
- **Object-level**: `tenants.permissions._TenantRolePermission.has_object_permission`
  independently re-checks `obj.tenant_id == request.user.tenant_id` on any
  detail/update/delete action, so a bug in one view's `get_queryset()`
  wiring doesn't silently become a cross-tenant leak.
- **Serializer-level** (defense in depth, third layer): planned for Day 3,
  once `ResourceSerializer`/`BookingSerializer` exist to enforce it on
  nested writes. Tracked in `docs/execution-plan.md`, not yet implemented.
- **`Booking.tenant`** is denormalized directly onto the model rather than
  reached only through `resource.tenant`, so every tenant filter above is a
  single indexed FK match, not a join — see `docs/architecture.md`.

## RBAC

Three roles, ranked `MEMBER < MANAGER < ADMIN`
(`tenants.permissions._ROLE_RANK`). `IsTenantMember` / `IsTenantManagerOrAbove`
/ `IsTenantAdmin` each require the requesting user's role to rank at or
above their minimum, *and* (via `has_permission`) that the user has a
tenant at all — a user with `tenant_id = None` is rejected outright, not
treated as a global admin. Fully TDD'd, 13/13 tests passing
(`tenants/tests/test_permissions.py`).

## Authentication

JWT via `djangorestframework-simplejwt`. In progress (Day 2, branch
`feat/jwt-tenant-claims`): a custom `TokenObtainPairSerializer` embeds
`tenant_id` and `role` as token claims, so the frontend can drive
role-aware UI (e.g. hide admin-only actions) without an extra identity
round trip after login. This is a UX optimization, not a trust boundary —
the backend re-derives tenant/role from `request.user` on every request via
the permission/mixin layers above; a tampered claim in a client-held token
cannot grant access the backend wouldn't independently check, since
`SIMPLE_JWT` tokens are signed (`SECRET_KEY`-backed HMAC) and any edited
claim invalidates the signature.

- Access token lifetime: 15 minutes. Refresh token: 7 days, rotated on use
  (`ROTATE_REFRESH_TOKENS = True`) — see `config/settings/base.py`.
- Frontend token storage decision (access in memory, refresh in an
  httpOnly cookie if time allows) is tracked in `docs/execution-plan.md`
  Day 4; documented here once implemented, since where the refresh token
  lives is itself a security decision (XSS exposure if `localStorage`).

## CORS

`CORS_ALLOW_ALL_ORIGINS` is never set to `True`, in any environment,
including local dev — an explicit allowlist costs nothing and removes a
habit that would otherwise need unlearning before prod
(`config/settings/base.py`). Each settings module sets its own
`CORS_ALLOWED_ORIGINS` explicitly:

- `dev.py`: `http://localhost:5173` (Vite's actual default dev port).
- `prod.py`: read from the `CORS_ALLOWED_ORIGINS` env var (comma-separated),
  empty until the real domain exists (Day 6).
- `CORS_ALLOW_CREDENTIALS = True` throughout, since the frontend sends the
  JWT cross-origin.

## Transport & cookies (production only, `config/settings/prod.py`)

- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` all
  `True`.
- `SECURE_PROXY_SSL_HEADER` set to trust Nginx's `X-Forwarded-Proto`,
  since Gunicorn itself only ever sees plain HTTP from the reverse proxy.
- HSTS enabled, 30-day `max-age` to start (raised once HTTPS is confirmed
  stable in practice), `includeSubDomains` + `preload` both on.

## Not yet done (tracked in `docs/execution-plan.md`)

- Serializer-level tenant enforcement (Day 3).
- Rate limiting on the auth endpoints (evaluate `django-ratelimit` or
  DRF's built-in throttling — not yet decided; will be documented here
  when it lands, likely Day 5 alongside the rest of the performance pass).
- Dependency/secret scanning in CI (Day 6, alongside the GitHub Actions
  pipeline).
