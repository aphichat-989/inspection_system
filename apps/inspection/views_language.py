from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


@login_required
def set_language(request, language):
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    request.session["ui_language"] = language
    response = redirect(request.GET.get("next") or request.META.get("HTTP_REFERER") or "inspection:dashboard")
    response.set_cookie("ui_language", language, max_age=60 * 60 * 24 * 365)
    return response


