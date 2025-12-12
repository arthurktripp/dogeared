from django.db import models

# Create your models here.


class Book(models.Model):
    author = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20)
    
    def __str__(self):
        return self.title


class Library(models.Model):
    name = models.CharField(max_length=255)
    books = models.ManyToManyField(Book, related_name='libraries')
    
    def __str__(self):
        return self.name


class User(models.Model):
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    libraries = models.OnetoMany(Library, on_delete=models.CASCADE)
