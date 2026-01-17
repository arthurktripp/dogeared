from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.AllBookshelvesPageView.as_view(), name='all-shelves-page'),
]
