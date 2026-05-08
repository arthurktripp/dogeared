# shelves/views.py
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin


from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, DeleteView, UpdateView


from .forms import ShelfCreateForm, ShelfUpdateForm
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


class ShelfUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Shelf
    form_class = ShelfUpdateForm
    template_name = "shelves/shelf_update.html"
    success_message = f'%(name)s updated successfully.'
    
    def get_queryset(self):
        return Shelf.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse("shelves:shelf-detail", kwargs={"slug": self.object.slug})
    

class AddBookToShelfView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        shelf_id = request.POST.get("shelf_id")
        external_id = request.POST.get("external_id")
        new_shelf_name = request.POST.get("name")
        new_shelf_description = request.POST.get("description")

        if not external_id:
            return HttpResponseBadRequest("Missing external_id")

        if shelf_id:
            shelf = get_object_or_404(Shelf, id=shelf_id, user=request.user)
        else:
            shelf = Shelf(
                user=request.user,
                name=new_shelf_name,
                description=new_shelf_description
            )
            shelf.save()

        
        volume = retrieve_volume(external_id)
        if not volume:
            return HttpResponseBadRequest("Unable to find volume")


        book, book_created = Book.objects.get_or_create(
            source="google",
            external_id=external_id,
            title=volume.title,
            authors=volume.authors
        )
        
        user_book, user_book_created = UserBook.objects.get_or_create(
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


class ShelfDetailView(LoginRequiredMixin, DetailView):
    model = Shelf
    template_name = "shelves/shelf_detail.html"
    context_object_name = "shelf"
    
    # enforces ownership
    def get_queryset(self):
        return Shelf.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        sort = self.request.GET.get("sort", "custom")
        direction = self.request.GET.get("dir", "asc")  # optional

        items = (
            ShelfItem.objects
            .filter(shelf=self.object)
            .select_related("user_book", "user_book__book")
        )

        if sort == "title":
            order = "user_book__book__title"
        elif sort == "author":
            order = "user_book__book__authors"  # or author_sort if you have it
        elif sort == "date_added":
            order = "added_at"                  # your field name may differ
        else:  # custom
            order = "position"

        if direction == "desc":
            order = "-" + order

        ctx["items"] = items.order_by(order, "id")  # stable tie-breaker
        ctx["current_sort"] = sort
        ctx["current_dir"] = direction
        return ctx

class RemoveBookFromShelfView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        shelf_slug = kwargs.get("shelf_slug")
        item_id = kwargs.get("item_id")

        shelf = get_object_or_404(Shelf, slug=shelf_slug, user=request.user)
        shelf_item = get_object_or_404(ShelfItem, id=item_id, shelf=shelf)

        book_title = shelf_item.user_book.book.title
        shelf_item.delete()

        messages.success(
            request,
            f'Removed "{book_title}" from {shelf.name}.'
        )

        return HttpResponseRedirect(
            reverse("shelves:shelf-detail", kwargs={"slug": shelf.slug})
        )