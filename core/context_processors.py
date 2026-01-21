from django.utils.safestring import mark_safe
from books.forms import OpenLibrarySearchForm


def nav_search_form(request):
    # Bind to GET so the query stays in the input after searching
    return {
        "nav_search_form": OpenLibrarySearchForm(request.GET or None)
    }


def brand(request):
    return {
        "brand": mark_safe("<em>dog&#8209;eared</em>"),
    }
