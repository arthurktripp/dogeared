# shelves/views.py
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView


from .forms import ShelfCreateForm
from .models import Shelf, ShelfItem

from books.models import Book
from books.services.googlebooks import create_book_object, retrieve_volume

from shelves.models import UserBook


class AllBookshelvesPageView(LoginRequiredMixin, ListView):
    model = Shelf
    template_name = "shelves/bookshelves.html"
    context_object_name = "shelves"

    def get_queryset(self):
        return (
            Shelf.objects
            .filter(user=self.request.user)
            .annotate(book_count=Count("items"))
            .order_by("-updated_at")
        )


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

        # Save safely (handles race + unique constraient nicely)
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # Most likely the (user, name) uniqueness constraint
            form.add_error("name", "You already have a shelf with that name.")
            return self.form_invalid(form)

        messages.success(self.request, f'Created shelf: "{form.instance.name}".')
        return response


class AddBookToShelfView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        shelf_id = request.POST.get("shelf_id")
        external_id = request.POST.get("external_id")
        

        if not shelf_id or not external_id:
            return HttpResponseBadRequest("Missing shelf_id or external_id")

        shelf = get_object_or_404(Shelf, id=shelf_id, user=request.user)

        
        volume = retrieve_volume(external_id)
        if not volume:
            return HttpResponseBadRequest("Unable to find volume")


        book, created = Book.objects.get_or_create(
            source="google",
            external_id=external_id,
            title=volume.title,
            authors=volume.authors
        )
        
        user_book, created = UserBook.objects.get_or_create(
            user=request.user,
            book=book            
        )
        

        shelf_item, shelf_item_created = ShelfItem.objects.get_or_create(
            shelf=shelf,
            user_book=user_book,
        )

        if shelf_item_created:
            messages.success(
                request,
                f"Added {book.title} to {shelf.name}."
            )
        else:
            messages.info(
                request,
                f"{book.title} is already on {shelf.name}."
            )
        
        return HttpResponseRedirect(
            reverse_lazy("books:book-detail", kwargs={"googleid": external_id})
        )

