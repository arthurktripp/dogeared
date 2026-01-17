"""
URL configuration for dogeared project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Site shell / landing pages
    path("", include("core.urls")),

    # Authentication & account management
    path("accounts/", include("accounts.urls")),

    # User profiles (identity, not auth)
    path("profiles/", include("users.urls")),

    # Books: search + book detail pages
    path("books/", include("books.urls")),

    # Shelves: personal + club shelves
    path("shelves/", include("shelves.urls")),

    # Book clubs (membership, governance, settings)
    path("clubs/", include("bookclubs.urls")),

    # Affiliate outbound links / redirects (optional but future-proof)
    path("go/", include("affiliates.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)