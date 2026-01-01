from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home-page'),
    path('register/', views.RegisterPageView.as_view(), name='registration-page'),
    path('login/', views.LoginPageView.as_view(), name='login-page'),
    path('logout/', LogoutView.as_view(), name='logout-page'),
    
    path('bookclubs/', views.AllBookclubsPageView.as_view(), name='all-bookclubs-page'),
    path('bookshelves/', views.AllBookshelvesPageView.as_view(), name='all-shelves-page'),
    path('profile/', views.UserProfilePageView.as_view(), name='profile-page'),
    path('edit-profile/', views.EditUserProfilePageView.as_view(), name='edit-profile-page'),
    path('profile/<str:username>', views.PublicProfilePageView.as_view(), name='public-profile-page'),
    # path('search/', views.UserProfilePageView.as_view(), name='search-page'),
]
