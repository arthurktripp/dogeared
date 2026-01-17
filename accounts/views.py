from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView

from django.urls import reverse_lazy

from django.views.generic.edit import CreateView

from .forms import RegisterNewUser, StyledLoginForm


# Create your views here.

class RegisterPageView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RegisterNewUser
    success_url = reverse_lazy('home-page')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        submitted_username = form.cleaned_data.get('username')
        username = form.cleaned_data.get('username').lower()
        messages.success(
            self.request, f'Welcome, {submitted_username}. Your account has been created.')

        return response


class LoginPageView(LoginView):
    template_name = 'accounts/login.html'
    form_class = StyledLoginForm
