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