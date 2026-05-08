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
