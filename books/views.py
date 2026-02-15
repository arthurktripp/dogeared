from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.views import View

from django.views.generic import FormView, TemplateView
from .forms import OmniSearchForm, AdvancedSearchForm
from .services.googlebooks import gb_search, retrieve_volume

from shelves.models import Shelf
from shelves.forms import ShelfCreateForm

# Create your views here.


class SearchPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'books/search.html')

    def post(self, request):
        return render(request, 'books/search.html')


class BookSearchView(FormView):
    template_name = "books/search.html"
    form_class = AdvancedSearchForm
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())

        # If no query string, just show the empty search page
        if "q" not in request.GET:
            return self.render_to_response(self.get_context_data(form=form))

        # Bind the form to GET data and validate
        form = self.form_class(request.GET)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        q = form.cleaned_data["q"]
        title = form.cleaned_data['title']
        author = form.cleaned_data['author']
        language = form.cleaned_data['language']
        page = form.cleaned_data.get("page") or 1

        limit = self.paginate_by
        offset = (page - 1) * limit

        resp = gb_search(limit=limit, offset=offset, q=q,
                         title=title, author=author, language=language)

        context = self.get_context_data(
            form=form,
            q=q,
            results=resp.results,
            num_found=resp.num_found,
            page=page,
            offset=offset,
            title=title,
            author=author,
            language=language,
            has_prev=page > 1,
            has_next=(offset + limit) < resp.num_found,
        )
        return self.render_to_response(context)


SHELF_MODAL_LIMIT = 5
MAX_SHELVES_PER_USER = 100

class BookDetailView(TemplateView):
    template_name = 'books/book_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        google_id = self.kwargs["googleid"]

        detail = retrieve_volume(google_id)
        if detail is None:
            raise Http404("Book not found")

        context["book"] = detail
        context["object"] = detail
        context["google_id"] = google_id

        if self.request.user.is_authenticated:
            qs = Shelf.objects.filter(user=self.request.user).order_by('-updated_at')
            context['shelf_choices'] = list(qs)
            context['shelf_total'] = qs.count()
            context['can_create_new_shelf'] = context['shelf_total'] < MAX_SHELVES_PER_USER
            new_shelf_form = ShelfCreateForm()
            context['new_shelf_form'] = new_shelf_form
        else:
            context['shelf_choices'] = []
            context['shelf_total'] = 0
            context['can_create_new_shelf'] = False
        
        return context

