from django.shortcuts import render
from django.views import View

# Create your views here.

class HomePageView(View):
    def get(self, request):
        context = {}
        if request.user.is_authenticated:
            return render(request, 'core/home_app.html')
        else:
            return render(request, 'core/home_public.html')
        
class PrivacyPolicyView(View):
    def get(self, request):
        context = 'temp'
        return render(request, context)