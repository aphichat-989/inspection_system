from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


class AppPermissionRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_denied_message = "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        messages.error(self.request, self.get_permission_denied_message())
        return redirect("inspection:dashboard")


class ModelPermissionRequiredMixin(AppPermissionRequiredMixin):
    permission_action = "view"

    def get_permission_required(self):
        opts = self.model._meta
        return (f"{opts.app_label}.{self.permission_action}_{opts.model_name}",)
