from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from django.views.generic import FormView
from .forms import OpenLibrarySearchForm
from .services.openlibrary import ol_search_basic
from .services.googlebooks import gb_search_basic

# Create your views here.


class SearchPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'books/search.html')

    def post(self, request):
        return render(request, 'books/search.html')


class BookSearchView(FormView):
    template_name = "books/search.html"
    form_class = OpenLibrarySearchForm
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
        page = form.cleaned_data.get("page") or 1

        limit = self.paginate_by
        offset = (page - 1) * limit

        resp = gb_search_basic(q=q, limit=limit, offset=offset)

        context = self.get_context_data(
            form=form,
            q=q,
            results=resp.results,
            num_found=resp.num_found,
            page=page,
            has_prev=page > 1,
            has_next=(offset + limit) < resp.num_found,
        )
        return self.render_to_response(context)
