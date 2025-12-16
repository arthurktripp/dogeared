from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.views import View

# Create your views here.

class HomePageView(View):
    def get(self, request):
        context = {}
        return render(request, 'bookclub/home.html')
    
class RegisterPage(View):
    def get(self, request):
        context = {}
        return render(request, 'bookclub/register.html')
    
class LoginPage(View):
    def get(self, request):
        context = {}
        return render(request, 'bookclub/login.html')
    