from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import redirect, get_object_or_404

from django.views.generic import DetailView, TemplateView

from .forms import UserEditForm, ProfileEditForm
from users.models import Profile

# Create your views here.


class UserProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.request.user.profile
        return context


class EditUserProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile-edit.html'

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
        profile_form = ProfileEditForm(
            request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("users:profile-page")

        return self.render_to_response(self.get_context_data(
            user_form=user_form,
            profile_form=profile_form,
        ))


class PublicProfilePageView(LoginRequiredMixin, DetailView):
    template_name = 'users/profile-public.html'
    model = Profile

    def get_object(self, queryset=None):
        username = self.kwargs["username"]
        return get_object_or_404(Profile, user__username__iexact=username, is_public=True)
