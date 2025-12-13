from django.contrib import admin

# Register your models here.

from .models import Book, Member, Shelf


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("author", "title")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name")


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name",)
