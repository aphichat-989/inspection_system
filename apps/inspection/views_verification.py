from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import VerificationRecordForm
from .models import VerificationRecord


class VerificationListView(ListView):
    model = VerificationRecord
    template_name = "inspection/verification_list.html"
    context_object_name = "records"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "This module now uses Test Sessions only.")
        return HttpResponseRedirect(reverse("inspection:list"))


class VerificationCreateView(CreateView):
    model = VerificationRecord
    form_class = VerificationRecordForm
    template_name = "inspection/verification_form.html"
    success_url = reverse_lazy("inspection:verification_list")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "This module now uses Test Sessions only.")
        return HttpResponseRedirect(reverse("inspection:list"))


class VerificationUpdateView(UpdateView):
    model = VerificationRecord
    form_class = VerificationRecordForm
    template_name = "inspection/verification_form.html"
    success_url = reverse_lazy("inspection:verification_list")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "This module now uses Test Sessions only.")
        return HttpResponseRedirect(reverse("inspection:list"))


class VerificationDeleteView(DeleteView):
    model = VerificationRecord
    template_name = "inspection/verification_confirm_delete.html"
    success_url = reverse_lazy("inspection:verification_list")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "This module now uses Test Sessions only.")
        return HttpResponseRedirect(reverse("inspection:list"))
