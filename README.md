# Smart Electricity Utility Management System

A FastAPI backend for managing electricity customers, service connections, smart
meters, meter readings, tariffs, billing, payments, complaints, field technicians,
service requests, analytics and reporting — built with role-based authentication,
a clean layered architecture, and slab-based billing logic.

Built and tested end-to-end in a live sandbox: every business rule below was
exercised against a running instance (not just written and hoped for), and the
included pytest suite passes (`18 passed`).

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · SQLite (default) /
PostgreSQL · JWT (python-jose) · Alembic · Uvicorn · Pytest

## Project structure

```
app/
├── main.py            # FastAPI app, middleware, exception handlers, router wiring
├── config.py          # Settings (env-driven)
├── database.py         # Engine/session/Base
├── dependencies.py     # get_current_user, require_roles(...) RBAC
├── models/             # SQLAlchemy ORM models (one file per entity)
├── schemas/             # Pydantic request/response models
├── repositories/        # Data-access layer (generic BaseRepository + per-entity repos)
├── services/            # Business logic (billing, tariffs, auth, notifications, reports)
├── routes/               # One FastAPI router per resource, mounted under /api/v1
└── utils/                # security (JWT/hashing), pagination, exceptions, rate limiting
scripts/
└── seed_superadmin.py   # One-time bootstrap for the first admin account
alembic/                  # Migrations (autogenerate-ready, wired to app models)
tests/                    # Pytest suite (18 tests) with an isolated in-memory DB
```

## Getting started

### Option A — local Python

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Bootstrap the first Super Admin (interactive prompt for email/password)
python -m scripts.seed_superadmin

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive Swagger UI.

### Option B — Docker Compose (API + Postgres)

```bash
docker compose up --build
# in another terminal, once it's up:
docker compose exec api python -m scripts.seed_superadmin
```

### Why a seed script?

`POST /auth/register` deliberately **refuses** to create any role other than
`customer` unless the caller is already an authenticated Super Admin — that's
the correct rule once the system is running, but something has to create the
very first admin. `scripts/seed_superadmin.py` does that directly against the
database, once, idempotently.

### Running tests

```bash
pytest -v
```

### Database migrations (Alembic)

The schema is also created automatically on app startup for local/dev
convenience (`Base.metadata.create_all`), but Alembic is fully wired for
real deployments:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## What's implemented

Every level in the spec has working code behind it, not just a route stub:

| Level | Status | Notes |
|---|---|---|
| 1. Auth & Users | ✅ Full | JWT access+refresh, bcrypt, RBAC for 5 roles, activate/deactivate |
| 2. Customers | ✅ Full | Unique customer_number/email, suspended-customer rule enforced downstream |
| 3. Connections | ✅ Full | Disconnect blocks new bills, one customer → many connections |
| 4. Meters | ✅ Full | One active meter per connection, replace flow, faulty/removed states |
| 5. Meter Readings | ✅ Full | Auto units calc, no-decrease rule, duplicate-period rule |
| 6. Billing | ✅ Full | Auto energy/tax/total calc, duplicate-bill prevention |
| 7. Tariffs | ✅ Full | True slab-based (progressive) pricing across unlimited slabs |
| 8. Payments | ✅ Full | Mock gateway, overpayment blocked, duplicate transaction_id blocked, auto bill status |
| 9. Complaints | ✅ Full | Emergency-first sorting, technician availability lock/unlock, full history log |
| 10. Technicians | ✅ Full | Availability tracking feeds directly into complaint assignment |
| 11. Service Requests | ✅ Full | Suspended-customer block, approve/reject/complete state machine |
| 12. Analytics | ✅ Full | Monthly/yearly/connection-wise/customer-wise/highest-consuming/average |
| 13. Search/Filter/Pagination | ✅ Full | Generic `page/limit/sort_by/sort_order` + per-resource filters |
| 14. Dashboard & Reports | ✅ Full | All 7 listed reports + summary dashboard |
| 15. Notifications & Background Tasks | ✅ Functional, simplified | See below |
| 16. Security & Integrity | ✅ Full | JWT, RBAC, FK/unique constraints, audit log, soft delete, CORS, rate limiting, global exception handlers |
| 17. Clean Architecture | ✅ Full | Strict routes → services → repositories → models separation |
| 18. DB & Performance | ✅ Full | Indexes on all spec'd columns, Alembic, joinedload used, no N+1 in list/report queries |

## Bonus features

| Feature | Status |
|---|---|
| API versioning `/api/v1/` | ✅ Done |
| Docker & Docker Compose | ✅ Done |
| Pytest unit & integration tests | ✅ Done (18 tests) |
| Online payment gateway mock | ✅ Done (see Payments below) |
| Automated overdue bill processing | ✅ Done as an admin-triggered endpoint (`POST /bills/process-overdue`); wire it to a cron/Celery-beat schedule in production |
| Redis caching | ⛔ Not built | Rate limiting uses a simple in-memory sliding window instead (`app/utils/rate_limit.py`) — fine for one process, not for multiple workers. Swapping to Redis (or `slowapi` + Redis) is a small, isolated change. |
| Celery scheduled bill generation | ⛔ Not built | `process_overdue_bills()` in `billing_service.py` is written to be schedule-agnostic — call it from a Celery-beat task instead of the HTTP endpoint and nothing else changes. |
| PDF electricity bill | ⛔ Not built | Would add a `reportlab`/`weasyprint` render step in `billing_service.py` returning a byte stream from a new `GET /bills/{id}/pdf` endpoint. |
| Excel billing report | ⛔ Not built | The report data already exists in `report_service.py`; wrapping it with `openpyxl` is straightforward. |
| QR code on bill | ⛔ Not built | Would encode the bill ID/payment link with `qrcode` and embed it in the PDF above. |
| WebSocket complaint status updates | ⛔ Not built | Would need a connection manager plus a broadcast call from `complaints.py`'s status-update endpoint. |

I prioritized a **fully working, tested core system** over partially wiring in
every bonus integration. The ⛔ items above are genuinely not implemented —
they're not hidden behind partial code that looks done but silently no-ops.

## Design decisions worth knowing about

- **Bill status lifecycle**: a new bill starts as `generated`. `POST /bills/process-overdue`
  (meant to run on a schedule) flips unpaid bills past `due_date` to `overdue`
  and applies a flat late fee. A bill becomes `paid` automatically once
  successful payments cover its `total_amount`.
- **Slab billing**: slabs are billed progressively (like a tax bracket), not
  "whichever slab you land in pays that whole rate." `minimum_units` is treated
  as a cumulative threshold (e.g. 0, 100, 200, 500) rather than requiring a
  +1 gap between slabs — configure tariffs that way for exact math.
- **Payments**: `POST /payments/{bill_id}` acts as a mock gateway — it
  succeeds immediately unless the caller passes `simulate_status` (useful for
  demos/tests of the failure path). Swap in Razorpay/Stripe by replacing the
  body of `payment_service.create_payment`.
- **Soft delete**: applied to `Customer` and `Connection` (the two entities
  the spec calls out with a `DELETE` endpoint); other entities use status
  fields instead, matching the spec.
- **Rate limiting**: a basic in-memory per-IP sliding window
  (`RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`, both configurable).
  Fine for a single-process deployment; use Redis for multi-worker setups.

## Default roles & permission model

| Role | Can do |
|---|---|
| `super_admin` | Everything, including creating other staff accounts and activating/deactivating users |
| `billing_officer` | Tariffs, bill generation/overdue processing, most reads |
| `field_technician` / `customer_service_agent` | Meter readings, complaints, service request review |
| `customer` | Self-registers, views their own data via the same endpoints (add row-level scoping if you need customers to see *only* their own records — currently any authenticated user can read most list/detail endpoints; write actions are role-gated) |

**One thing to harden before production**: read endpoints currently only
check "is authenticated," not "is this the customer's own data." For a real
deployment, add an ownership check (e.g. compare `current_user.customer_id`
against the resource's `customer_id`) to customer-facing GET endpoints.

## Configuration

All settings live in `app/config.py` and can be overridden via a `.env` file
— see `.env.example` for the full list (database URL, JWT secret/expiry,
CORS origins, rate limits, tax %, late fee, bill due days).
