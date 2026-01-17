from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

# Create your views here.


class SearchPageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'books/search.html')
    
    def post(self, request):
        return render(request, 'books/search.html')
    
