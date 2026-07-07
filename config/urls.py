"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
from apps.inspection.forms_auth import BootstrapAuthenticationForm
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path
from apps.inspection.forms_auth import BootstrapAuthenticationForm


def home_redirect(request):
    return redirect("inspection:dashboard")


def healthz(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("accounts/login/", LoginView.as_view(template_name="registration/login.html", authentication_form=BootstrapAuthenticationForm, redirect_authenticated_user=True), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("", home_redirect, name="home"),
    path("admin/", admin.site.urls),
    path("inspection/", include(("apps.inspection.urls", "inspection"), namespace="inspection")),
]


