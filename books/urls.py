from django.urls import path
from .views import BookSearchView, BookDetailView

app_name = 'books'

urlpatterns = [
    path("search/", BookSearchView.as_view(), name="book-search"),
    path("detail/<str:googleid>", BookDetailView.as_view(), name="book-detail"),
]
