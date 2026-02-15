from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.AllBookshelvesPageView.as_view(), name='all-shelves-page'),
    path('new/', views.ShelfCreateView.as_view(), name='create'),
    path('add/', views.AddBookToShelfView.as_view(), name='add-book'),
]
