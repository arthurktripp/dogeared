from django.contrib.auth.models import User
from django.db import models


class Book(models.Model):
    author = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20)

    def __str__(self):
        return self.title


class Shelf(models.Model):
    # A shelf is a collection of books that belongs to a specific member.
    name = models.CharField(max_length=255)
    books = models.ManyToManyField(Book, related_name='shelves')
    member = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(default='default-profile.jpg', upload_to='profile_pics')
    favorite_genre = models.CharField(max_length=100)
    
    def __str__(self):
        return f'{self.user.username} Profile' 
    
