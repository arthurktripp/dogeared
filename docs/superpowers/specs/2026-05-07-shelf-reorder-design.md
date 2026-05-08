# Shelf Reorder — Design

## Goal

Let a user reorder books on a shelf by dragging the grip-vertical handle on each row of the shelf detail page. The new order persists immediately on drop. On failure, the page reloads to show the canonical (server) order and a Django messages-framework error banner.

This change also introduces htmx and SortableJS as standard front-end dependencies, intended to serve future features (inline remove, toggle finished/favorite, book-club discussions).

## Architecture

- **Drag interaction:** SortableJS, scoped to the grip handle.
- **Persistence trigger:** htmx posts a form on SortableJS's `end` event.
- **Server:** new `ShelfReorderView` validates the payload and rewrites positions inside one transaction.
- **Failure UX:** server queues a Django messages-framework error and returns 400; client JS reloads the page so the message banner renders and the DOM resets to the DB state.

No new Python dependencies. Three new static assets in `static/scripts/`: `htmx.min.js`, `Sortable.min.js`, `shelf-reorder.js`.

## Data model

`ShelfItem.position` already exists as `PositiveIntegerField(null=True, blank=True)`. No schema redesign needed; two migrations bring the field into a usable state.

### Migration A — backfill positions

`RunPython` migration:
- For each `Shelf`, fetch its items ordered by `(added_at, id)`.
- Assign `position = 0, 1, 2, …` and `bulk_update`.
- Idempotent: safe to re-run on shelves that already have positions.
- Reverse op: no-op.

### Migration B — tighten field

After backfill, alter `ShelfItem.position` to drop `null=True, blank=True`. Future code can rely on the field being non-null.

### No unique constraint on (shelf, position)

Reorders rewrite all positions for a shelf inside `transaction.atomic()`, so transient duplicates can't be observed by other transactions. A unique constraint would force a temporary-offset trick during updates without adding meaningful safety.

## Server: `ShelfReorderView`

- **URL:** `POST /shelves/my-shelves/<slug>/reorder/`, named `shelves:shelf-reorder`.
- **Class:** `ShelfReorderView(LoginRequiredMixin, View)` with `http_method_names = ["post"]`.
- **Request body:** form-encoded, repeated `item` fields:
  ```
  item=42&item=17&item=88
  ```
  This is exactly what htmx serializes from the hidden inputs on each list-group item.

### Logic

1. `shelf = get_object_or_404(Shelf, slug=slug, user=request.user)` — enforces ownership; foreign shelves return 404.
2. `ids = request.POST.getlist("item")`, coerced to ints. Empty list, duplicates, or any non-integer → error path.
3. Fetch `shelf_item_ids = set(ShelfItem.objects.filter(shelf=shelf).values_list("id", flat=True))`. If `set(ids) != shelf_item_ids`, the payload is missing items, includes an unknown ID, or includes items from another shelf → error path. (This also catches duplicates within the payload, since `set(ids)` would have a smaller length than `ids`.)
4. Inside `transaction.atomic()`, fetch `items = list(ShelfItem.objects.filter(shelf=shelf))`, build a dict `{id: index}` from the ordered request list, set `item.position` accordingly on each, then `ShelfItem.objects.bulk_update(items, ["position"])`.
5. Return `HttpResponse(status=204)`.

### Error path

Any of the above failures:
- `messages.error(request, "Couldn't save the new order. Please try again.")`
- Return `HttpResponse(status=400)`.

The 400 triggers `htmx:responseError` on the client, which reloads the page and renders the queued message in the existing banner (`templates/base_app.html` lines 37–45).

### Tests

In `shelves/tests.py`:
- Foreign user's shelf → 404.
- Unknown `item` ID → 400.
- `item` ID belonging to another shelf of the same user → 400.
- Payload missing one of the shelf's items → 400.
- Duplicate IDs in payload → 400.
- Malformed payload (non-integer, empty) → 400.
- Happy path: positions updated to match request order.

## Front end

### Static assets

Committed to `static/scripts/`:
- `htmx.min.js` (htmx 2.x)
- `Sortable.min.js` (SortableJS 1.15.x)
- `shelf-reorder.js` (init glue)

### `templates/base_app.html`

Add `<script>` tags for `htmx.min.js` and `Sortable.min.js` before `bootstrap.bundle.js`. They load on every authenticated page; future features can use htmx without re-plumbing.

### `shelves/templates/shelves/shelf_detail.html`

The list-group container:

```django
<div class="list-group col-md-8{% if current_sort == 'custom' %} sortable{% endif %}"
     {% if current_sort == 'custom' %}
     hx-post="{% url 'shelves:shelf-reorder' shelf.slug %}"
     hx-trigger="end"
     hx-swap="none"
     hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
     {% endif %}>
```

Sortable behavior is gated on `current_sort == "custom"`. Dragging while items are sorted by title would silently re-stamp positions in title order — surprising and irreversible without server-side history. Disabling drag in non-custom sorts is the safe default.

Each `list-group-item` gains a hidden input as its first child:

```django
<input type="hidden" name="item" value="{{ item.id }}">
```

The grip SVG gets `class="drag-handle"` and `style="cursor: grab;"`.

### `static/scripts/shelf-reorder.js`

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

Loaded via a `<script>` tag in `base_app.html` after htmx and SortableJS.

### CSRF

The `hx-headers` attribute on the list container injects `X-CSRFToken` per request, which Django's CSRF middleware accepts on POSTs. No global config needed.

## Edge cases

| Case | Behavior |
|------|----------|
| User reorders in two tabs | Last write wins. Acceptable for v1. |
| Item deleted between page render and drop | Server returns 400, page reloads, item is gone, user sees current state. |
| Foreign-shelf item in payload | Server returns 400 (count mismatch). |
| Touch / mobile | SortableJS handles touch natively. |
| Sort = title/author/date_added | List is not draggable; sortable class and htmx attrs are not rendered. |

## Out of scope

- Keyboard accessibility for reordering (move-up/down buttons, ARIA live regions). SortableJS does not provide this natively.
- Undo for reorders.
- Real-time cross-tab sync.
- Surfacing a sort selector in the shelf detail UI (the view already accepts `?sort=`, but no toolbar exposes it yet — pre-existing gap, separate work).

## Files touched

- `shelves/views.py` — add `ShelfReorderView`.
- `shelves/urls.py` — add reorder route.
- `shelves/migrations/<next>_backfill_shelfitem_position.py` — new (sequence number determined at implementation time).
- `shelves/migrations/<next+1>_alter_shelfitem_position.py` — new.
- `shelves/tests.py` — add reorder view tests.
- `shelves/templates/shelves/shelf_detail.html` — sortable container, hidden inputs, drag-handle class.
- `templates/base_app.html` — htmx + Sortable + shelf-reorder script tags.
- `static/scripts/htmx.min.js` — new vendor file.
- `static/scripts/Sortable.min.js` — new vendor file.
- `static/scripts/shelf-reorder.js` — new init script.
