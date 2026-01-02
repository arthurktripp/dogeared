from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower

from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
        
    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_lower_email"
            )
        ]
        
        
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    is_public = models.BooleanField(default=False)
    
    profile_pic = models.ImageField(
        default='default-profile.png',
        upload_to='profile_pics')
    
    blurb = models.TextField(
        max_length=140,
        blank=True)
    
    about_me = models.TextField(
        max_length=2000,
        blank=True)
    
    location = models.CharField(
        max_length=100,
        blank=True)
    
    pronouns = models.CharField(
        max_length=100,
        blank=True)
    
    website = models.URLField(
        blank=True)
    
    favorite_genre = models.CharField(
        max_length=100,
        blank=True)
    
    favorite_author = models.CharField(
        max_length=100,
        blank=True)
    
    recommend_to_everyone = models.CharField(
        max_length=100,
        blank=True)
    
    currently_reading = models.CharField(
        max_length=100,
        blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'
