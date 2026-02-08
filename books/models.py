from django.db import models


class Book(models.Model):
    source = models.CharField(max_length=20,
                              choices=[
                                  ("google", "Google"),
                                  ("isbndb", "ISBNdb")
                                  ],
                              )
    external_id = models.CharField(max_length=64, blank=False)
    title = models.CharField(max_length=512, blank=True)
    authors = models.CharField(max_length=512, blank=True)
    thumbnail_url = models.URLField(blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="uniq_book_source_external"
                )
        ]
