from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home-page'),
    path('privacy-policy', views.PrivacyPolicyView.as_view(), name='privacy-policy-page'),
]
