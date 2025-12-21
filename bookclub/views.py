from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

from django.shortcuts import render

from django.urls import reverse_lazy

from django.views import View
from django.views.generic.edit import CreateView, FormView

from .forms import RegisterNewUser

# Create your views here.


class HomePageView(View):
    def get(self, request):
        context = {}
        if request.user.is_authenticated:
            return render(request, 'bookclub/home_app.html')
        else:
            return render(request, 'bookclub/home_public.html')


class RegisterPageView(CreateView):
    template_name = 'bookclub/register.html'
    form_class = RegisterNewUser
    success_url = None

    template_name = "bookclub/register.html"
    success_url = reverse_lazy("home-page")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Welcome, {username}. <br>Your account has been created.')
        
        return response


class LoginPageView(FormView):
    def get(self, request):
        context = {}
        return render(request, 'bookclub/login.html')
