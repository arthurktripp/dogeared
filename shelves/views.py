# shelves/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView


from .forms import ShelfCreateForm
from .models import Shelf

# Create your views here.

class AllBookshelvesPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'shelves/bookshelves.html')



MAX_SHELVES_PER_USER = 100

class ShelfCreateView(LoginRequiredMixin, CreateView):
    model = Shelf
    form_class = ShelfCreateForm
    template_name = "shelves/shelf_form.html"
    success_url = reverse_lazy("shelves:all-shelves-page")

    def form_valid(self, form):
        # Enforce per-user shelf cap
        existing_count = Shelf.objects.filter(user=self.request.user).count()
        if existing_count >= MAX_SHELVES_PER_USER:
            form.add_error(None, f"You’ve reached the limit of {MAX_SHELVES_PER_USER} shelves.")
            return self.form_invalid(form)

        form.instance.user = self.request.user

        # Save safely (handles race + unique constraint nicely)
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # Most likely the (user, name) uniqueness constraint
            form.add_error("name", "You already have a shelf with that name.")
            return self.form_invalid(form)

        messages.success(self.request, f'Created shelf: "{form.instance.name}".')
        return response
