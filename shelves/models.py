from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from dogeared import settings

from books.models import Book


class UserBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    notes = models.TextField(blank=True)
    have_read = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    progress = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "book"],
                                    name="uniq_user_book",)
        ]


class Shelf(models.Model):
    # A shelf is a collection of books that belongs to a specific member.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90)
    description = models.CharField(max_length=280, blank=True)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"],
                                    name="uniq_shelf_name_per_user"),
            models.UniqueConstraint(fields=["user", "slug"],
                                    name="uniq_shelf_user_slug"),
        ]
    
    def _generate_unique_slug(self) -> str:
        base = slugify(self.name) or "shelf"
        slug = base
        i = 2

        qs = Shelf.objects.filter(user=self.user)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1

        return slug

    def save(self, *args, **kwargs):
        self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ShelfItem(models.Model):
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name='items')
    user_book = models.ForeignKey(UserBook, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["shelf", "user_book"],
                                    name="uniq_book_per_shelf")
        ]
