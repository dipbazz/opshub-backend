# Architecture

## What OpsHub is

OpsHub is a multi-tenant booking platform: each **tenant** is an organization
(a company or team) that manages a pool of shared **resources** — meeting
rooms, equipment, vehicles — and lets its members reserve time slots on them.
Every tenant's data is fully isolated from every other tenant's, enforced at
the application's query layer, not just hidden in the UI. Three roles exist
within a tenant: **Admin** (manages users and all bookings), **Manager**
(creates/edits any booking), **Member** (creates and manages only their own
bookings).

## Domain model (4 models)

- `Tenant(id, name, slug, created_at)`
- `User(AbstractUser + tenant FK [nullable, see tenants/models.py], role: ADMIN|MANAGER|MEMBER)`
- `Resource(id, tenant FK, name, description, capacity, created_at)`
- `Booking(id, tenant FK, resource FK, created_by FK→User, start_time, end_time, status, created_at)`

`Booking` carries `tenant` directly rather than only reaching it through
`resource` — a deliberate denormalization so every tenant-scoped queryset
filter is a single indexed FK match (`.filter(tenant=request.user.tenant)`),
not a join through `resource` on every request.

## Request flow (filled in as pieces land — a real diagram replaces this on Day 7)

- **Auth**: JWT (`djangorestframework-simplejwt`) issues access/refresh
  tokens carrying `tenant_id`/`role` claims, so the frontend can drive
  role-aware UI without an extra round trip.
- **Data access**: DRF ViewSets, tenant-scoped at the queryset level *and*
  the serializer level (defense in depth — see `SECURITY.md`).
- **Caching**: Redis caches the resource-availability endpoint, keyed
  per-tenant, invalidated on booking writes rather than relying on TTL alone.
- **Deploy**: React (Vercel) → Nginx → Gunicorn/Django → Postgres/Redis, all
  behind HTTPS on a DigitalOcean droplet.

See `SECURITY.md` (added Day 2 onward) for the tenant-isolation and RBAC
decisions behind this model.
