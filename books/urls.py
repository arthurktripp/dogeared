from django.urls import path
from .views import BookSearchView

app_name = 'books'

urlpatterns = [
    path("search/", BookSearchView.as_view(), name="book-search"),
]
