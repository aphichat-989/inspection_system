from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms_users import UserAdminForm


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        messages.error(self.request, "คุณไม่มีสิทธิ์เข้าหน้าจัดการผู้ใช้")
        return redirect("inspection:dashboard")


class UserListView(StaffRequiredMixin, ListView):
    model = get_user_model()
    template_name = "inspection/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return self.model.objects.order_by("username")


class UserCreateView(StaffRequiredMixin, CreateView):
    model = get_user_model()
    form_class = UserAdminForm
    template_name = "inspection/user_form.html"
    success_url = reverse_lazy("inspection:user_list")

    def form_valid(self, form):
        messages.success(self.request, "เพิ่มผู้ใช้เรียบร้อยแล้ว")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "เพิ่มผู้ใช้"
        context["is_update"] = False
        return context


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserAdminForm
    template_name = "inspection/user_form.html"
    success_url = reverse_lazy("inspection:user_list")

    def form_valid(self, form):
        messages.success(self.request, "บันทึกผู้ใช้เรียบร้อยแล้ว")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "แก้ไขผู้ใช้"
        context["is_update"] = True
        return context


class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = get_user_model()
    template_name = "inspection/user_confirm_delete.html"
    success_url = reverse_lazy("inspection:user_list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.pk == request.user.pk:
            messages.error(request, "ไม่สามารถลบบัญชีที่กำลังใช้งานอยู่ได้")
            return redirect("inspection:user_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "ลบผู้ใช้เรียบร้อยแล้ว")
        return super().form_valid(form)