from django.contrib import admin


# Register your models here.

from .models import Book, Shelf, Profile


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("author", "title")

@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    