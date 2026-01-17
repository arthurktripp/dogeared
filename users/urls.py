from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Logged-in user's profile
    path('', views.UserProfilePageView.as_view(), name='profile-page'),
    path('edit/', views.EditUserProfilePageView.as_view(),
         name='edit-profile-page'),
    
    # Other users' public profiles
    path('<str:username>/', views.PublicProfilePageView.as_view(),
         name='public-profile-page'),
]
