from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterPageView.as_view(), name='registration-page'),
    path('login/', views.LoginPageView.as_view(), name='login-page'),
    path('logout/', LogoutView.as_view(), name='logout-page'),
]
