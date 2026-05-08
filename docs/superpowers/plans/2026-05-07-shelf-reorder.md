# Shelf Reorder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users reorder books on a shelf by dragging the grip handle, persisting on drop, with Django messages-framework error feedback on failure.

**Architecture:** SortableJS handles the drag interaction; htmx posts the new order on the SortableJS `end` event; a new Django view rewrites `ShelfItem.position` values inside one transaction. On failure the page reloads to show the canonical order and a Django error banner.

**Tech Stack:** Django 6, htmx 2, SortableJS 1.15, vanilla JS (no build step). Static assets committed directly to `static/scripts/` matching project convention.

**Spec:** `docs/superpowers/specs/2026-05-07-shelf-reorder-design.md`

---

## File Structure

**Create:**
- `static/scripts/htmx.min.js` (vendored)
- `static/scripts/Sortable.min.js` (vendored)
- `static/scripts/shelf-reorder.js` (init glue)
- `shelves/migrations/0008_backfill_shelfitem_position.py`
- `shelves/migrations/0009_alter_shelfitem_position.py` (auto-generated)

**Modify:**
- `shelves/models.py` — drop `null=True, blank=True` from `ShelfItem.position`
- `shelves/views.py` — add `ShelfReorderView`
- `shelves/urls.py` — add reorder route
- `shelves/tests.py` — add reorder view tests
- `shelves/templates/shelves/shelf_detail.html` — sortable container, hidden inputs, drag-handle class
- `templates/base_app.html` — add htmx, Sortable, and shelf-reorder script tags

---

## Working assumptions for the engineer

- `python3` and `pip` work in the project root with the `.venv` already activated. If not: `source .venv/bin/activate` first.
- All `manage.py` commands run from `/Users/arthurktripp/dogeared`.
- The CustomUser model uses email as `USERNAME_FIELD`. `User.objects.create_user(username=..., email=..., password=...)` works.
- After each task, run the test suite (`python3 manage.py test shelves`) to make sure nothing else broke.
- Commit messages follow the project's existing imperative style (e.g. "remove book from shelf", "background styling").

---

## Task 1: Vendor htmx and SortableJS

**Files:**
- Create: `static/scripts/htmx.min.js`
- Create: `static/scripts/Sortable.min.js`
- Modify: `templates/base_app.html`

- [ ] **Step 1: Download htmx 2.0.4**

```bash
curl -L -o static/scripts/htmx.min.js \
  https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js
```

Verify the file is non-empty:
```bash
ls -la static/scripts/htmx.min.js
```
Expected: file size > 40KB.

- [ ] **Step 2: Download SortableJS 1.15.2**

```bash
curl -L -o static/scripts/Sortable.min.js \
  https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js
```

Verify:
```bash
ls -la static/scripts/Sortable.min.js
```
Expected: file size > 40KB.

- [ ] **Step 3: Add script tags to `templates/base_app.html`**

Find the existing line near the bottom:
```html
    <script src="{% static 'scripts/bootstrap.bundle.js' %}" ></script>
```

Replace with:
```html
    <script src="{% static 'scripts/bootstrap.bundle.js' %}" ></script>
    <script src="{% static 'scripts/htmx.min.js' %}"></script>
    <script src="{% static 'scripts/Sortable.min.js' %}"></script>
```

(We add `shelf-reorder.js` later in Task 6 once it exists.)

- [ ] **Step 4: Smoke-check the page loads**

Run the dev server in a second terminal:
```bash
python3 manage.py runserver 0.0.0.0:8000
```
Open the app in a browser, log in, and check the browser dev tools Network tab to confirm `htmx.min.js` and `Sortable.min.js` return 200. Also open the JS console and type `htmx` and `Sortable` — both should be defined globals.

Stop the server (Ctrl-C) when done.

- [ ] **Step 5: Commit**

```bash
git add static/scripts/htmx.min.js static/scripts/Sortable.min.js templates/base_app.html
git commit -m "vendor htmx and SortableJS"
```

---

## Task 2: Backfill `ShelfItem.position` via data migration

**Files:**
- Create: `shelves/migrations/0008_backfill_shelfitem_position.py`

- [ ] **Step 1: Create the migration**

Create `shelves/migrations/0008_backfill_shelfitem_position.py`:

```python
from django.db import migrations


def backfill_positions(apps, schema_editor):
    Shelf = apps.get_model("shelves", "Shelf")
    ShelfItem = apps.get_model("shelves", "ShelfItem")

    for shelf in Shelf.objects.all():
        items = list(
            ShelfItem.objects.filter(shelf=shelf).order_by("added_at", "id")
        )
        for index, item in enumerate(items):
            item.position = index
        if items:
            ShelfItem.objects.bulk_update(items, ["position"])


class Migration(migrations.Migration):

    dependencies = [
        ("shelves", "0007_alter_userbook_finished_at"),
    ]

    operations = [
        migrations.RunPython(backfill_positions, migrations.RunPython.noop),
    ]
```

- [ ] **Step 2: Run the migration**

```bash
python3 manage.py migrate shelves
```

Expected: `Applying shelves.0008_backfill_shelfitem_position... OK`

- [ ] **Step 3: Verify positions populated**

```bash
python3 manage.py shell -c "from shelves.models import ShelfItem; print([(i.shelf_id, i.id, i.position) for i in ShelfItem.objects.all().order_by('shelf_id', 'position')])"
```

Expected: every row has a non-null integer `position`. Within each `shelf_id`, positions are `0, 1, 2, …` with no gaps and no duplicates.

If your dev DB has no shelf items yet, the output will be `[]` — that's still success.

- [ ] **Step 4: Commit**

```bash
git add shelves/migrations/0008_backfill_shelfitem_position.py
git commit -m "backfill shelf item positions"
```

---

## Task 3: Tighten `ShelfItem.position` to non-null

**Files:**
- Modify: `shelves/models.py`
- Create (auto-generated): `shelves/migrations/0009_alter_shelfitem_position.py`

- [ ] **Step 1: Update the model field**

In `shelves/models.py`, find:

```python
    position = models.PositiveIntegerField(null=True, blank=True)
```

Replace with:

```python
    position = models.PositiveIntegerField()
```

- [ ] **Step 2: Generate the migration**

```bash
python3 manage.py makemigrations shelves
```

Expected output mentions creating `0009_alter_shelfitem_position.py` (filename may vary slightly — Django picks based on field changes).

If Django prompts for a default value, that means Step 1 of Task 2 didn't actually populate every row. Abort, investigate (some `position` is still null), and re-run the data migration before continuing.

- [ ] **Step 3: Apply the migration**

```bash
python3 manage.py migrate shelves
```

Expected: the new migration applies cleanly.

- [ ] **Step 4: Verify**

```bash
python3 manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add shelves/models.py shelves/migrations/0009_*.py
git commit -m "make ShelfItem.position non-null"
```

---

## Task 4: Add `ShelfReorderView` (TDD)

**Files:**
- Modify: `shelves/tests.py`
- Modify: `shelves/views.py`
- Modify: `shelves/urls.py`

- [ ] **Step 1: Write the failing tests**

Replace the contents of `shelves/tests.py` with:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from shelves.models import Shelf, ShelfItem, UserBook


class ShelfReorderViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pw",
        )
        self.other = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="pw",
        )
        self.shelf = Shelf.objects.create(user=self.user, name="My Shelf")
        self.items = []
        for i in range(3):
            book = Book.objects.create(
                source="google",
                external_id=f"ext{i}",
                title=f"Book {i}",
                authors=["Author"],
            )
            user_book = UserBook.objects.create(user=self.user, book=book)
            item = ShelfItem.objects.create(
                shelf=self.shelf, user_book=user_book, position=i
            )
            self.items.append(item)

    def url(self, slug=None):
        return reverse(
            "shelves:shelf-reorder",
            kwargs={"slug": slug or self.shelf.slug},
        )

    def _ids(self, items):
        return [str(i.id) for i in items]

    def test_unauthenticated_redirected(self):
        resp = self.client.post(self.url(), {"item": self._ids(self.items)})
        self.assertEqual(resp.status_code, 302)

    def test_foreign_shelf_returns_404(self):
        other_shelf = Shelf.objects.create(user=self.other, name="Other")
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("shelves:shelf-reorder", kwargs={"slug": other_shelf.slug}),
            {"item": []},
        )
        self.assertEqual(resp.status_code, 404)

    def test_unknown_item_returns_400(self):
        self.client.force_login(self.user)
        ids = self._ids(self.items) + ["999999"]
        resp = self.client.post(self.url(), {"item": ids})
        self.assertEqual(resp.status_code, 400)

    def test_item_from_other_shelf_returns_400(self):
        other_shelf = Shelf.objects.create(user=self.user, name="Other")
        book = Book.objects.create(
            source="google", external_id="x", title="X", authors=["a"]
        )
        ub = UserBook.objects.create(user=self.user, book=book)
        other_item = ShelfItem.objects.create(
            shelf=other_shelf, user_book=ub, position=0
        )
        self.client.force_login(self.user)
        ids = self._ids(self.items[:2]) + [str(other_item.id)]
        resp = self.client.post(self.url(), {"item": ids})
        self.assertEqual(resp.status_code, 400)

    def test_missing_item_returns_400(self):
        self.client.force_login(self.user)
        ids = self._ids(self.items[:2])
        resp = self.client.post(self.url(), {"item": ids})
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_ids_return_400(self):
        self.client.force_login(self.user)
        ids = [
            str(self.items[0].id),
            str(self.items[0].id),
            str(self.items[1].id),
        ]
        resp = self.client.post(self.url(), {"item": ids})
        self.assertEqual(resp.status_code, 400)

    def test_non_integer_returns_400(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url(), {"item": ["abc"]})
        self.assertEqual(resp.status_code, 400)

    def test_empty_payload_returns_400(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url(), {"item": []})
        self.assertEqual(resp.status_code, 400)

    def test_happy_path_reorders(self):
        self.client.force_login(self.user)
        new_order = [self.items[2].id, self.items[0].id, self.items[1].id]
        resp = self.client.post(
            self.url(), {"item": [str(i) for i in new_order]}
        )
        self.assertEqual(resp.status_code, 204)
        for index, item_id in enumerate(new_order):
            self.assertEqual(
                ShelfItem.objects.get(id=item_id).position, index
            )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 manage.py test shelves
```

Expected: all `ShelfReorderViewTests` fail because `shelves:shelf-reorder` is not a registered URL name (`NoReverseMatch`).

- [ ] **Step 3: Add the URL route**

In `shelves/urls.py`, add a new path before the `shelf-update` path:

```python
    path('my-shelves/<slug:slug>/reorder/',
         views.ShelfReorderView.as_view(),
         name='shelf-reorder'),
```

The full updated `urlpatterns` should look like:

```python
urlpatterns = [
    path('', views.AllBookshelvesPageView.as_view(), name='all-shelves-page'),
    path('new/', views.ShelfCreateView.as_view(), name='create'),
    path('add/', views.AddBookToShelfView.as_view(), name='add-book'),
    path('remove/<slug:shelf_slug>/<int:item_id>', views.RemoveBookFromShelfView.as_view(), name='remove-book'),
    path('my-shelves/<slug:slug>/', views.ShelfDetailView.as_view(), name='shelf-detail'),
    path('my-shelves/<slug:slug>/reorder/', views.ShelfReorderView.as_view(), name='shelf-reorder'),
    path('my-shelves/<slug:slug>/edit', views.ShelfUpdateView.as_view(), name='shelf-update'),
]
```

- [ ] **Step 4: Add the view**

In `shelves/views.py`, append to the bottom of the file:

```python
class ShelfReorderView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        slug = kwargs["slug"]
        shelf = get_object_or_404(Shelf, slug=slug, user=request.user)

        raw = request.POST.getlist("item")
        try:
            ids = [int(x) for x in raw]
        except (TypeError, ValueError):
            return self._error(request)

        if not ids:
            return self._error(request)

        shelf_item_ids = set(
            ShelfItem.objects.filter(shelf=shelf).values_list("id", flat=True)
        )
        if len(ids) != len(set(ids)) or set(ids) != shelf_item_ids:
            return self._error(request)

        with transaction.atomic():
            items = list(ShelfItem.objects.filter(shelf=shelf))
            order = {item_id: idx for idx, item_id in enumerate(ids)}
            for item in items:
                item.position = order[item.id]
            ShelfItem.objects.bulk_update(items, ["position"])

        return HttpResponse(status=204)

    def _error(self, request):
        messages.error(
            request,
            "Couldn't save the new order. Please try again.",
        )
        return HttpResponse(status=400)
```

Also confirm the existing imports at the top of `views.py` already include everything we need: `messages`, `LoginRequiredMixin`, `transaction`, `HttpResponse`, `get_object_or_404`, `View`, `Shelf`, `ShelfItem`. They do — no import changes needed. (Note: the file already imports `HttpResponseBadRequest` and `HttpResponseRedirect`; we use `HttpResponse` directly with explicit status codes for clarity.)

If `HttpResponse` is not yet imported, add it to the existing line:
```python
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
```

- [ ] **Step 5: Run tests and verify they pass**

```bash
python3 manage.py test shelves
```

Expected: all 9 `ShelfReorderViewTests` pass.

- [ ] **Step 6: Commit**

```bash
git add shelves/views.py shelves/urls.py shelves/tests.py
git commit -m "add shelf reorder endpoint"
```

---

## Task 5: Wire up `shelf_detail.html`

**Files:**
- Modify: `shelves/templates/shelves/shelf_detail.html`

- [ ] **Step 1: Update the list-group container**

In `shelves/templates/shelves/shelf_detail.html`, find the line:

```html
    <div class="list-group col-md-8">
```

Replace with:

```html
    <div class="list-group col-md-8{% if current_sort == 'custom' %} sortable{% endif %}"
         {% if current_sort == 'custom' %}
         hx-post="{% url 'shelves:shelf-reorder' shelf.slug %}"
         hx-trigger="end"
         hx-swap="none"
         hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
         {% endif %}>
```

- [ ] **Step 2: Add the hidden input inside each item**

Find:

```html
        <div class="list-group-item " data-item-id="{{ item.id }}">
            <div class="d-flex align-items-center justify-content-between">
```

Replace with:

```html
        <div class="list-group-item " data-item-id="{{ item.id }}">
            <input type="hidden" name="item" value="{{ item.id }}">
            <div class="d-flex align-items-center justify-content-between">
```

- [ ] **Step 3: Add the drag-handle class to the grip SVG**

Find the grip SVG:

```html
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-grip-vertical-icon lucide-grip-vertical"><circle cx="9" cy="12" r="1"/><circle cx="9" cy="5" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="19" r="1"/></svg>
```

Replace with:

```html
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-grip-vertical-icon lucide-grip-vertical drag-handle" style="cursor: grab;"><circle cx="9" cy="12" r="1"/><circle cx="9" cy="5" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="19" r="1"/></svg>
```

(Only the `class` and added `style` attributes change.)

- [ ] **Step 4: Sanity-check the page renders**

Start the dev server:
```bash
python3 manage.py runserver 0.0.0.0:8000
```

Open a shelf in the browser. Confirm:
- The list still renders.
- View page source: the list-group `<div>` has `class="list-group col-md-8 sortable"` and the `hx-post` attribute.
- Each `list-group-item` contains `<input type="hidden" name="item" value="...">`.
- The grip SVG has `drag-handle` in its class list.

Drag won't work yet (no init script). That's expected.

Stop the server.

- [ ] **Step 5: Commit**

```bash
git add shelves/templates/shelves/shelf_detail.html
git commit -m "wire shelf detail for sortable reorder"
```

---

## Task 6: Add the `shelf-reorder.js` init script

**Files:**
- Create: `static/scripts/shelf-reorder.js`
- Modify: `templates/base_app.html`

- [ ] **Step 1: Create the init script**

Create `static/scripts/shelf-reorder.js` with:

```js
htmx.onLoad(function(content) {
  content.querySelectorAll(".sortable").forEach(function(el) {
    new Sortable(el, {
      handle: ".drag-handle",
      animation: 150,
      ghostClass: "sortable-ghost",
    });
  });
});

document.body.addEventListener("htmx:responseError", function() {
  window.location.reload();
});
```

- [ ] **Step 2: Add the script tag to `base_app.html`**

In `templates/base_app.html`, find the script tags added in Task 1:

```html
    <script src="{% static 'scripts/bootstrap.bundle.js' %}" ></script>
    <script src="{% static 'scripts/htmx.min.js' %}"></script>
    <script src="{% static 'scripts/Sortable.min.js' %}"></script>
```

Append the new line:

```html
    <script src="{% static 'scripts/bootstrap.bundle.js' %}" ></script>
    <script src="{% static 'scripts/htmx.min.js' %}"></script>
    <script src="{% static 'scripts/Sortable.min.js' %}"></script>
    <script src="{% static 'scripts/shelf-reorder.js' %}"></script>
```

- [ ] **Step 3: Commit**

```bash
git add static/scripts/shelf-reorder.js templates/base_app.html
git commit -m "init sortable on shelf detail"
```

---

## Task 7: End-to-end browser verification

**Files:** none modified — manual test only.

- [ ] **Step 1: Start the server**

```bash
python3 manage.py runserver 0.0.0.0:8000
```

- [ ] **Step 2: Happy path**

In the browser:
1. Log in.
2. Open a shelf with at least 3 books.
3. Drag the second book by its grip handle to the first position.
4. Watch the Network tab — confirm a POST to `/shelves/my-shelves/<slug>/reorder/` returns 204.
5. Refresh the page. The new order persists.

- [ ] **Step 3: Sort gating**

Open the shelf with `?sort=title` in the URL.
1. View page source: the list-group `<div>` should NOT have the `sortable` class or `hx-post`.
2. The grip handles should still render but be inert.

Open the same shelf without query params (defaults to custom). The sortable class and hx attrs should reappear.

- [ ] **Step 4: Failure path**

Force a 400:
1. Open the shelf detail page.
2. Open the browser console and remove a `<input name="item">` from one of the items via dev tools (e.g., `document.querySelector('.list-group-item input[name=item]').remove()`).
3. Drag a book — the POST will be missing one item ID, server returns 400.
4. The page should reload automatically and show the "Couldn't save the new order…" alert.

- [ ] **Step 5: Touch / mobile (optional)**

If you have a touchscreen device or browser device emulation: long-press the grip handle and drag. SortableJS supports touch natively; same flow as desktop.

- [ ] **Step 6: Stop the server (Ctrl-C)**

No commit — this task is verification only.

---

## Self-Review Notes

Done after writing this plan:

- **Spec coverage:** Every spec section has a task. (Architecture → tasks 1, 6; data model → tasks 2, 3; server → task 4; front end → tasks 5, 6; edge cases → task 7.)
- **Type/name consistency:** URL name `shelves:shelf-reorder` used in template (Task 5), tests (Task 4), and view (Task 4). Field name `item` used in hidden input, view's `getlist`, and test payloads. Class `sortable` and `drag-handle` consistent across template (Task 5) and JS (Task 6).
- **No placeholders:** every step shows exact code or commands.
