from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import TestSessionForm
from .models import DefectType, InspectionRound, InspectionSession, InspectionTest, Inspector
from .views_helpers import (
    AUTO_COMPLETED_MESSAGE,
    build_next_session_number,
    get_round_result_types,
    record_inspection_round,
    test_summary,
)


class InspectionListView(ListView):
    model = InspectionSession
    template_name = "inspection/list.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        queryset = InspectionSession.objects.select_related("line", "test_condition", "inspector")
        line_name = self.request.GET.get("line_name", "").strip()
        start_date = self.request.GET.get("start_date", "").strip()
        end_date = self.request.GET.get("end_date", "").strip()
        if line_name:
            queryset = queryset.filter(line__name__icontains=line_name)
        if start_date:
            queryset = queryset.filter(inspection_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(inspection_date__lte=end_date)
        return queryset.order_by("-inspection_date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["line_name"] = self.request.GET.get("line_name", "")
        context["start_date"] = self.request.GET.get("start_date", "")
        context["end_date"] = self.request.GET.get("end_date", "")
        return context


class TestSessionContextMixin:
    def get_defect_context(self, form=None):
        active_defects = DefectType.objects.filter(is_active=True).order_by("name")
        selected_ids = set(self.request.POST.getlist("defects"))
        round_values = {}
        if getattr(self, "object", None) and self.object.pk and not selected_ids:
            tests = self.object.tests.select_related("defect_type")
            selected_ids = {str(test.defect_type_id) for test in tests if test.defect_type_id}
            round_values = {str(test.defect_type_id): test.total_rounds for test in tests if test.defect_type_id}
        else:
            for defect in active_defects:
                round_values[str(defect.pk)] = self.request.POST.get(f"rounds_{defect.pk}", 1)
        defect_cards = []
        for defect in active_defects:
            defect_id = str(defect.pk)
            defect_cards.append(
                {
                    "defect": defect,
                    "selected": defect_id in selected_ids,
                    "rounds": round_values.get(defect_id, self.request.POST.get(f"rounds_{defect.pk}", 1)),
                }
            )
        return {
            "defect_cards": defect_cards,
            "has_active_inspectors": Inspector.objects.filter(is_active=True).exists(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_defect_context(context.get("form")))
        return context


class InspectionCreateView(TestSessionContextMixin, CreateView):
    model = InspectionSession
    form_class = TestSessionForm
    template_name = "inspection/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["session_number"] = build_next_session_number()
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        selected_defects = DefectType.objects.filter(pk__in=self.request.POST.getlist("defects"), is_active=True)
        if not selected_defects.exists():
            form.add_error(None, "Please select at least one defect to test.")
            return self.form_invalid(form)

        self.object = form.save(commit=False)
        self.object.session_number = build_next_session_number()
        self.object.status = InspectionSession.STATUS_IN_PROGRESS
        self.object.save()
        for defect in selected_defects:
            total_rounds = max(1, int(self.request.POST.get(f"rounds_{defect.pk}") or 1))
            InspectionTest.objects.create(
                session=self.object,
                defect_type=defect,
                test_name=str(defect.pk),
                total_rounds=total_rounds,
            )
        messages.success(self.request, "Test Session created. Start testing now.")
        return HttpResponseRedirect(reverse("inspection:detail", kwargs={"pk": self.object.pk}))


class InspectionUpdateView(TestSessionContextMixin, UpdateView):
    model = InspectionSession
    form_class = TestSessionForm
    template_name = "inspection/form.html"
    success_url = reverse_lazy("inspection:list")

    def get_queryset(self):
        return InspectionSession.objects.prefetch_related("tests__rounds")

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        selected_defects = DefectType.objects.filter(pk__in=self.request.POST.getlist("defects"), is_active=True)
        existing_tests = {test.defect_type_id: test for test in self.object.tests.select_related("defect_type") if test.defect_type_id}
        for defect in selected_defects:
            total_rounds = max(1, int(self.request.POST.get(f"rounds_{defect.pk}") or 1))
            test = existing_tests.get(defect.pk)
            if not test:
                test = InspectionTest.objects.create(session=self.object, defect_type=defect, test_name=str(defect.pk), total_rounds=total_rounds)
            else:
                test.total_rounds = total_rounds
                test.save(update_fields=["total_rounds"])

        messages.success(self.request, "Test Session updated.")
        return HttpResponseRedirect(reverse("inspection:detail", kwargs={"pk": self.object.pk}))


class InspectionDetailView(DetailView):
    model = InspectionSession
    template_name = "inspection/detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return InspectionSession.objects.select_related("line", "test_condition", "inspector").prefetch_related(
            Prefetch(
                "tests",
                queryset=InspectionTest.objects.select_related("defect_type").prefetch_related(
                    Prefetch("rounds", queryset=InspectionRound.objects.select_related("result_type").order_by("round_number"))
                ),
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action", "save")
        current_index = int(request.POST.get("current_index") or 0)
        current_test_id = request.POST.get("current_test_id")
        result_value = request.POST.get("result", "")
        show_finished_summary = False

        if result_value:
            if not current_test_id:
                return HttpResponseBadRequest("No inspection test was selected.")
            result, error = record_inspection_round(
                self.object,
                current_test_id,
                result_value,
                request.POST.get("comment", ""),
            )
            if error:
                return HttpResponseBadRequest(error)
            if result["auto_completed"]:
                messages.info(request, AUTO_COMPLETED_MESSAGE)
                show_finished_summary = True
            else:
                messages.success(request, "Inspection round recorded.")
                show_finished_summary = result["test"].status == InspectionTest.STATUS_FINISHED
        elif action == "save":
            return HttpResponseBadRequest("Please select FOUND or NOT_FOUND before submitting.")

        tests_count = self.object.tests.count()
        if action == "finish":
            self.object.status = InspectionSession.STATUS_COMPLETED
            self.object.save(update_fields=["status"])
            messages.success(request, "Test Session finished.")
            return HttpResponseRedirect(f"{reverse('inspection:detail', kwargs={'pk': self.object.pk})}?summary=1")
        if show_finished_summary:
            return HttpResponseRedirect(
                f"{reverse('inspection:detail', kwargs={'pk': self.object.pk})}?defect={current_index}&summary=1"
            )
        if action == "previous":
            current_index = max(0, current_index - 1)
        elif action == "next":
            current_index = min(max(tests_count - 1, 0), current_index + 1)
        return HttpResponseRedirect(f"{reverse('inspection:detail', kwargs={'pk': self.object.pk})}?defect={current_index}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        found_result, not_found_result = get_round_result_types()
        tests = list(self.object.tests.all())
        current_index = int(self.request.GET.get("defect") or 0)
        current_index = min(max(current_index, 0), max(len(tests) - 1, 0)) if tests else 0
        summaries = [test_summary(test) for test in tests]
        current_summary = summaries[current_index] if summaries else None
        current_test = tests[current_index] if tests else None
        current_round_number = current_summary["next_round_number"] if current_summary else 0
        round_progress_percent = (
            round((current_summary["completed"] / current_summary["total_rounds"]) * 100)
            if current_summary and current_summary["total_rounds"]
            else 0
        )
        show_summary = self.request.GET.get("summary") == "1" or (
            current_summary and current_summary["is_finished"]
        )
        context.update(
            {
                "tests": tests,
                "current_test": current_test,
                "current_index": current_index,
                "display_index": current_index + 1,
                "total_tests": len(tests),
                "progress_percent": round(((current_index + 1) / len(tests)) * 100) if tests else 0,
                "round_progress_percent": round_progress_percent,
                "summaries": summaries,
                "current_summary": current_summary,
                "found_result": found_result,
                "not_found_result": not_found_result,
                "current_round_number": current_round_number,
                "show_summary": show_summary,
            }
        )
        return context


class InspectionBulkDeleteView(View):
    success_url = reverse_lazy("inspection:list")

    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist("selected_sessions")
        if not selected_ids:
            messages.warning(request, "Please select at least one Test Session to delete.")
            return HttpResponseRedirect(self.success_url)

        queryset = InspectionSession.objects.filter(pk__in=selected_ids)
        deleted_count = queryset.count()
        if not deleted_count:
            messages.warning(request, "Selected Test Sessions were not found.")
            return HttpResponseRedirect(self.success_url)

        queryset.delete()
        messages.success(request, f"Deleted {deleted_count} Test Session(s).")
        return HttpResponseRedirect(self.success_url)


class InspectionDeleteView(DeleteView):
    model = InspectionSession
    template_name = "inspection/confirm_delete.html"
    success_url = reverse_lazy("inspection:list")

    def form_valid(self, form):
        messages.success(self.request, "Test Session deleted.")
        return super().form_valid(form)
