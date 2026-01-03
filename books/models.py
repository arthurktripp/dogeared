from django.db import models

# Create your models here.


class work(models.Model):
    author = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    open_lib_work_key = models.CharField(max_length=20)

    def __str__(self):
        return self.title
