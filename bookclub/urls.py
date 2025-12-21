from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home-page'),
    path('register/', views.RegisterPageView.as_view(), name='registration-page'),
    path('login/', views.LoginPageView.as_view(), name='login-page'),
    path('logout/', views.LogoutPageView.as_view(), name='logout-page'),
]
