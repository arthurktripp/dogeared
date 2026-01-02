from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django.shortcuts import render, redirect, get_object_or_404

from django.urls import reverse_lazy

from django.views import View
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView

from .forms import RegisterNewUser, StyledLoginForm, UserEditForm, ProfileEditForm

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
    
class EditUserProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = 'bookclub/profile-edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.request.user.profile
        return context
    
    def get(self, request, *args, **kwargs):
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return self.render_to_response(self.get_context_data(
            user_form=user_form,
            profile_form=profile_form,
        ))
        
    def post(self, request, *args, **kwargs):
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile-page")

        return self.render_to_response(self.get_context_data(
            user_form=user_form,
            profile_form=profile_form,
        ))


class PublicProfilePageView(LoginRequiredMixin, DetailView):
    template_name = 'bookclub/profile-public.html'
    model = Profile
    

    def get_object(self, queryset=None):
        username = self.kwargs["username"]
        return get_object_or_404(Profile, user__username=username, is_public=True)




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
    

