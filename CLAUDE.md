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
```

## Environment Setup

Requires a `.env` file with:
- `DJANGO_SECRET_KEY`
- `GOOGLE_BOOKS_API_KEY`
- `ALLOWED_HOSTS`

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
Shelf → ShelfItem (1:many)
ShelfItem → UserBook (1:1)
UserBook → Book (many:1, shared catalog entry)
Book → external_id + source (e.g., Google Books volume ID)
```

### Template System

Two base templates:
- `templates/base_app.html` — for authenticated users (Halfmoon CSS elegant theme)
- `templates/base_public.html` — for guests

Frontend uses Halfmoon CSS + Bootstrap. No build step — static assets are committed directly to `static/`.
