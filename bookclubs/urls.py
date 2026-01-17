from django.urls import path
from . import views

app_name = 'bookclubs'

urlpatterns = [
    path('', views.AllBookclubsPageView.as_view(), name='all-bookclubs-page'),
]
