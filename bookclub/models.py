from django.db import models


class Book(models.Model):
    author = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20)

    def __str__(self):
        return self.title


class Member(models.Model):
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.username


class Shelf(models.Model):
    # A shelf is a collection of books that belongs to a specific member.
    name = models.CharField(max_length=255)
    books = models.ManyToManyField(Book, related_name='shelves')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
