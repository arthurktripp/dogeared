from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from django.shortcuts import render

from django.urls import reverse_lazy

from django.views import View
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView

from .forms import RegisterNewUser, StyledLoginForm

from .models import Profile

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
    success_url = reverse_lazy('home-page')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        
        username = form.cleaned_data.get('username').lower()
        messages.success(self.request, f'Welcome, {username}. Your account has been created.')
        
        return response


class UserProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = "bookclub/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.request.user.profile
        return context


class LoginPageView(LoginView):
    template_name = 'bookclub/login.html'
    form_class = StyledLoginForm


class AllBookclubsPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'bookclub/bookclubs.html')


class AllBookshelvesPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'bookclub/bookshelves.html')




class SearchPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'bookclub/search.html')
    
    def post(self, request):
        return render(request, 'bookclub/search.html')