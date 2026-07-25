# django-oscar-paypal-store

A [Django Oscar](https://github.com/django-oscar/django-oscar) (4.1) e-commerce
sandbox integrated with **PayPal Express Checkout**, **Simplified-Chinese (zh-CN)
localization**, and a **demo storefront UI**.

> ⚠️ **This is a technical demo / portfolio, not a production store.**
> PayPal runs in **sandbox mode only** (`PAYPAL_MODE=sandbox`). Do **not** switch it
> to live or use it to accept real payments. See [Security notes](#security-notes).

---

## What's inside

- **Django Oscar 4.1** storefront (catalogue, basket, checkout, dashboard) on Django 5.2 + Bootstrap 4.
- **PayPal Express Checkout** integration (OAuth → create order → approve → capture → refund) running against the PayPal sandbox API.
- **Idempotent payments** — `create_order` uses a unique idempotency key per click; `capture_order` is retry-safe (GET reconcile + stable `PayPal-Request-Id` + treats `ORDER_ALREADY_CAPTURED` as success).
- **Dashboard refund wired to PayPal** — the Oscar dashboard "refund" action performs a *real* PayPal refund via the facade instead of only local bookkeeping.
- **zh-CN localization** — a project-level `django.po` supplies ~83 high-frequency UI translations; the language switcher is an **EN | 中文** toggle.
- **Demo UI** — modern e-commerce theme + a fixed **"演示站点 · DEMO"** badge so the site is clearly marked as a non-commercial demo.
- **One-command Docker** — `docker compose up` brings up the web (uWSGI) + PostgreSQL services with auto-migrate and auto-seed.

## Tech stack

| Layer        | Choice |
|--------------|--------|
| Language     | Python 3.12 |
| Framework    | Django Oscar 4.1 / Django 5.2 |
| Web server   | uWSGI (port 8080) |
| Database     | PostgreSQL 15 (Alpine) |
| Search       | Haystack + Whoosh |
| Build assets | Node.js 20 (npm) |
| Orchestration| Docker Compose |

> The internal Compose **project name is pinned** to `django-oscar-research`
> (`name:` in `docker-compose.yml`). Renaming the directory therefore **does not**
> break running containers, volumes, or baked-in customizations.

## Prerequisites

- Docker 20.10+ and Docker Compose v2
- A PayPal developer account for **sandbox** credentials (see [PayPal setup](#paypal-sandbox-setup))
- `git` (to clone)

## Quick start

```bash
# 1. Clone
git clone git@github.com:erishen/django-oscar-paypal-store.git
cd django-oscar-paypal-store

# 2. Create your environment file (REQUIRED — see note below)
cp .env.example .env
#    then edit .env and fill in SECRET_KEY, DATABASE_PASSWORD,
#    and your PayPal sandbox CLIENT_ID / CLIENT_SECRET.

# 3. Build & start (rebuilds the image so all customizations are baked in)
docker compose up -d --build

# 4. Open the storefront
#    Chinese : http://localhost:8080/zh-cn/
#    English : http://localhost:8080/en-gb/
#    (If 8080 is taken on the host, set WEB_PORT in .env, e.g. 8092, and use
#     http://localhost:8092/ instead.)
```

> 🔴 **`.env` is required and is NOT in the repo** (gitignored).
> `docker-compose.yml` reads `DATABASE_PASSWORD` with `${DATABASE_PASSWORD:?...}`,
> so starting without a `.env` fails immediately. Always `cp .env.example .env`
> first and fill in at least `SECRET_KEY` and `DATABASE_PASSWORD`.

### Create an admin / superuser

```bash
make quick-admin          # creates admin / admin123456
# or
make createsuperuser      # interactive
```

Then visit the dashboard under the language prefix, e.g.
`http://localhost:8080/zh-cn/dashboard/` (or `/en-gb/dashboard/`).
The Django admin is at `/zh-cn/admin/` (or `/en-gb/admin/`).

## Environment variables

All variables live in `.env` (copy from `.env.example`). Key entries:

| Variable             | Required | Notes |
|----------------------|----------|-------|
| `DEBUG`              | no       | `True` in this sandbox. Set `False` for production. |
| `SECRET_KEY`         | **yes**  | Use a strong random value. |
| `DATABASE_ENGINE`    | no       | `django.db.backends.postgresql_psycopg2` (default). |
| `DATABASE_NAME`      | no       | `oscar_db` (default). |
| `DATABASE_USER`      | no       | `oscar_user` (default). |
| `DATABASE_PASSWORD`  | **yes**  | Read by Compose; the DB user is updated to match on first init. |
| `PAYPAL_CLIENT_ID`   | **yes\***| Sandbox client id. `*` only needed for checkout. |
| `PAYPAL_CLIENT_SECRET`| **yes\***| Sandbox client secret. |
| `PAYPAL_MODE`        | no       | `sandbox` (default). Keep it sandbox. |
| `WEB_PORT`          | no       | Host port published (container listens on 8080 internally). Default `8080`. Set to e.g. `8092` if `8080` is already taken on the host. |

PayPal credentials are **never committed** (`.env` is gitignored) and have never
been in the git history.

## PayPal sandbox setup

1. Create an app at <https://developer.paypal.com/dashboard/applications/sandbox>.
2. Copy the **Client ID** and **Secret** into `.env` as `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET`.
3. Keep `PAYPAL_MODE=sandbox`.
4. In the storefront, add a product to the basket → checkout → *Pay with PayPal* →
   log in with a PayPal **sandbox buyer** account → approve → you are returned and
   the Oscar order is placed. Refunds can be issued from the Oscar dashboard.

The payment flow implementation lives in
`django-oscar/sandbox/apps/paypal_express/` (a forked Oscar sandbox app), with the
HTTP facade in `facade.py`.

## Internationalization (en-gb / zh-cn)

The active languages are registered in `settings.LANGUAGES` as **`en-gb`** and
**`zh-cn`** only.

- Storefront URLs are language-prefixed: `/zh-cn/...` and `/en-gb/...`.
- 👉 **There is no `/en-us/` prefix** — requesting `/en-us/` returns 404 by design
  (the English locale is `en-gb`). Use `/en-gb/` for English.
- zh-CN UI strings are provided by `django-oscar/sandbox/locale/zh_CN/LC_MESSAGES/django.po`
  (project `LOCALE_PATHS` takes priority over the library translations).
- The header switcher is an **EN | 中文** toggle that posts to Django's
  `set_language` with a language-neutral `next` (so switching languages never gets
  "stuck" on the old prefix).

## Project structure

```
django-oscar-paypal-store/
├── django-oscar/                 # Vendored Django Oscar source + sandbox (customized)
│   └── sandbox/
│       ├── apps/
│       │   ├── paypal_express/   # PayPal facade + views (idempotent capture/refund)
│       │   └── dashboard/        # Forked dashboard with real-PayPal refunds
│       ├── locale/zh_CN/         # zh-CN translations
│       ├── templates/oscar/      # Base / nav / product template overrides
│       └── static/oscar/css/     # Demo theme (custom.css) + DEMO badge
├── docker-compose.yml            # Pinned project name: django-oscar-research
├── Dockerfile                   # python:3.12 + Node 20 + uWSGI
├── init-db.sh                   # migrate + seed (skips if data exists) + index
├── scripts/                     # Helper management commands
├── .env.example                 # Template for required env vars
├── UPSTREAM.md                  # Upstream baseline + customization list
├── README.md / README.zh.md     # Docs
└── PRODUCT-DATA-GUIDE.md        # Product data guide
```

## Data & seeding

On first start, `init-db.sh` runs migrations, loads fixtures (users, catalogue,
images, countries, pages, ranges, offers, orders), builds the search index, and
collects static files. **If data already exists it is skipped**, so restarts never
duplicate seed data.

Current seeded state: **≈140 products** (products without images were removed) and
**4 sample orders**. Data persists in the `postgres_data` volume.

## Rebuilding after code changes

The Docker image is built from the local `django-oscar/` source, so any change to
the vendored Oscar sandbox (PayPal facade, templates, CSS, translations, …) must be
**baked into the image** to survive a container recreate:

```bash
docker compose build web
docker compose up -d
```

`make build` / `make up` do the same. Hot-patching via `docker cp` works while a
container is running but is lost on recreate — prefer a rebuild for durable changes.

## Makefile cheat-sheet

| Command | Purpose |
|---------|---------|
| `make up` / `make down` | Start / stop (PostgreSQL) |
| `make up-sqlite` | Start with SQLite instead of PostgreSQL |
| `make build` | Build the web image |
| `make restart` | Restart services |
| `make logs` / `make logs-web` | Tail logs |
| `make shell` | Bash into the web container |
| `make db-shell` | PSQL into PostgreSQL |
| `make quick-admin` | Create `admin`/`admin123456` |
| `make migrate` | Run migrations |
| `make rebuild-index` | Rebuild the search index |
| `make check-data` | Show product / order counts |
| `make clean` | Stop **and delete** containers + volumes |

## Known caveats / FAQ

- **`/en-us/` returns 404** — expected. The English locale is `en-gb`; use `/en-gb/`.
- **Must create `.env` before `docker compose up`** — `DATABASE_PASSWORD` is required.
- **Sandbox only** — PayPal is wired to the sandbox API; this is a demo, not a store.
- **`settings.py` has a hardcoded fallback `SECRET_KEY`** for the demo (low risk);
  the real value comes from `.env`. Override it for any real deployment.
- The seed catalogue is the upstream Oscar sample data; products without images
  were removed so the storefront looks clean.

## Security notes

- `.env` (containing `SECRET_KEY`, `DATABASE_PASSWORD`, PayPal credentials) is
  **gitignored** and has never been committed.
- `DATABASE_PASSWORD` is supplied to the container from `.env`
  (`POSTGRES_PASSWORD: ${DATABASE_PASSWORD:?...}`); it is **not** hardcoded in
  `docker-compose.yml`.
- PayPal runs in **sandbox** mode. Accepting real payments would require a payment
  license / compliant on-boarding (e.g. EDI in China) and a different payment
  backbone — out of scope for this demo.
- For production you would additionally set `DEBUG=False`, configure
  `ALLOWED_HOSTS`, terminate TLS at a reverse proxy, and back up the DB volume.

## License

Django Oscar is distributed under the **BSD-3-Clause** license. This sandbox and
its customizations are provided as-is for demonstration purposes.
