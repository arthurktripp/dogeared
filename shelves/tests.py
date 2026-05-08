from types import SimpleNamespace
from unittest.mock import patch

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


class AddBookToShelfPositionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pw",
        )
        self.shelf = Shelf.objects.create(user=self.user, name="My Shelf")

    def _add(self, external_id, title):
        with patch(
            "shelves.views.retrieve_volume",
            return_value=SimpleNamespace(title=title, authors=["Author"]),
        ):
            return self.client.post(
                reverse("shelves:add-book"),
                {"shelf_id": self.shelf.id, "external_id": external_id},
            )

    def test_first_book_gets_position_zero(self):
        self.client.force_login(self.user)
        self._add("ext0", "Book 0")
        item = ShelfItem.objects.get(shelf=self.shelf)
        self.assertEqual(item.position, 0)

    def test_subsequent_books_append_to_bottom(self):
        self.client.force_login(self.user)
        self._add("ext0", "Book 0")
        self._add("ext1", "Book 1")
        self._add("ext2", "Book 2")
        positions = list(
            ShelfItem.objects.filter(shelf=self.shelf)
            .order_by("position")
            .values_list("position", flat=True)
        )
        self.assertEqual(positions, [0, 1, 2])

    def test_appends_after_manually_set_high_position(self):
        # If existing items have non-contiguous positions (e.g., after a
        # reorder), a newly added book lands strictly after the highest.
        book = Book.objects.create(
            source="google", external_id="seed", title="Seed", authors=["a"]
        )
        ub = UserBook.objects.create(user=self.user, book=book)
        ShelfItem.objects.create(shelf=self.shelf, user_book=ub, position=42)

        self.client.force_login(self.user)
        self._add("ext_new", "New")

        new_item = ShelfItem.objects.get(
            shelf=self.shelf, user_book__book__external_id="ext_new"
        )
        self.assertEqual(new_item.position, 43)
