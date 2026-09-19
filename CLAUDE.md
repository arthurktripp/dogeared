# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dogeared is a Django-based book management app. Users can search for books (via Google Books API), add them to personal shelves, and manage their reading collections. Book club features are planned but not yet implemented.

## Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python3 manage.py migrate

# Start dev server
python3 manage.py runserver

# Run tests
python3 manage.py test

# Run tests for a specific app
python3 manage.py test shelves

# Run a single test method
python3 manage.py test shelves.tests.ShelfReorderViewTests.test_reorder_success
```

## Environment Setup

Requires a `.env` file (copy `.env.example`) with:
- `DJANGO_SECRET_KEY`
- `GOOGLE_BOOKS_API_KEY`
- `ALLOWED_HOSTS`
- `DATABASE_URL` — optional locally; if unset, settings fall back to `postgres://dogeared_app@localhost/dogeared`

Dev and prod both run on **PostgreSQL 18** (see the Database section). A local Postgres server must be running before `migrate`, `runserver`, or `test`.

## Architecture

Seven Django apps, each with their own models/views/forms/templates:

- **`core/`** — Landing pages, shared context processors (nav search form, brand name)
- **`accounts/`** — Registration and login (uses Turnstile CAPTCHA)
- **`users/`** — `CustomUser` (email-based auth) and `Profile` (auto-created via signal on registration)
- **`books/`** — Book search and detail pages; `books/services/googlebooks.py` handles all Google Books API calls; books are stored locally after first fetch using `external_id` + `source='google'`
- **`shelves/`** — Core domain: `Shelf`, `ShelfItem`, and `UserBook` models; `AddBookToShelfView` creates all three in `transaction.atomic()`
- **`bookclubs/`** — Stub only, in development
- **`affiliates/`** — Stub only, future feature

### Key Data Model Relationships

```
CustomUser → Profile (1:1, auto-created via signal)
CustomUser → Shelf (1:many, user owns shelves)
Shelf → ShelfItem (1:many, position-ordered)
ShelfItem → UserBook (1:1)
UserBook → Book (many:1, shared catalog entry)
Book → external_id + source (e.g., Google Books volume ID)
```

The three-layer `Book → UserBook → ShelfItem` design is intentional: `UserBook` holds per-user reading metadata (rating, notes, have_read, progress), and `ShelfItem` links that to a specific shelf with a position. This means the same book can appear on multiple shelves with shared metadata, and position ordering is shelf-scoped.

### Database

PostgreSQL 18 in both dev and prod (migrated off SQLite; prod target is Neon). `DATABASES` is configured via `dj-database-url` reading `DATABASE_URL`, with a local default of `postgres://dogeared_app@localhost/dogeared`. The driver is `psycopg` 3 (`psycopg[binary]`), which requires Django 4.2+. Connections use `conn_max_age=300` and `conn_health_checks=True` — `conn_max_age` must stay at or below Neon's 5-minute scale-to-zero window.

Local dev uses Postgres.app (port 5432, `trust` auth). The app role `dogeared_app` (LOGIN, CREATEDB, non-superuser) owns the `dogeared` database, mirroring Neon's no-superuser setup; `CREATEDB` is what lets the test runner build `test_dogeared`. For Neon, use the direct connection string for migrations and the `-pooler` string for the app on an elastic host (also set `DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True` there); the prod URL needs `sslmode=require&connect_timeout=15`.

The legacy `db.sqlite3` is gitignored and no longer a supported backend. Note Postgres is case-sensitive for `contains` (unlike SQLite) and does not guarantee row order without an explicit `order_by`/`Meta.ordering`.

### Authentication

`CustomUser` uses `email` as `USERNAME_FIELD` (not `username`). Email is normalized to lowercase in both `CustomUser.save()` and the form `clean` methods, enforced by a `UniqueConstraint` with `Lower("email")`. Always use `email` — not `username` — when looking up or creating users.

### Google Books Service

`books/services/googlebooks.py` returns dataclasses (`GBSearchResult`, `GBSearchResponse`, `BookDetail`) — not model instances. API failures are caught and return empty results with no retry logic. `books/services/openlibrary.py` exists but is unused; the `Book` model's `source` field has an `isbndb` choice reserved for a future second source.

### Shelf Ordering

`ShelfItem.position` is a plain integer. New items are appended at `max(position) + 1`. `ShelfReorderView` (POST-only) validates the submitted ID list against five failure modes before doing a bulk update — see `shelves/views.py:212`.

### Frontend

No build step — all static assets are committed to `static/`. The authenticated layout (`base_app.html`) loads HTMX and Sortable.js. Drag-and-drop shelf reordering is wired in `static/scripts/shelf-reorder.js`; on HTMX error it reloads the page to restore order from the server.

### Template System

Two base templates:
- `templates/base_app.html` — for authenticated users (Halfmoon CSS elegant theme)
- `templates/base_public.html` — for guests
