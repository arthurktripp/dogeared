from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.AllBookshelvesPageView.as_view(), name='all-shelves-page'),
    path('new/', views.ShelfCreateView.as_view(), name='create'),
    path('add/', views.AddBookToShelfView.as_view(), name='add-book'),
    path('remove/<slug:shelf_slug>/<int:item_id>', views.RemoveBookFromShelfView.as_view(), name='remove-book'),
    path('my-shelves/<slug:slug>/', views.ShelfDetailView.as_view(), name='shelf-detail'),
]
