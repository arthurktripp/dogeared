from django.contrib.auth.models import User
from django.db import models


class Shelf(models.Model):
    # A shelf is a collection of books that belongs to a specific member.
    name = models.CharField(max_length=255)
    # books = models.ManyToManyField(Book, related_name='shelves')

    def __str__(self):
        return self.name


