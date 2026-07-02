from datetime import date

from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import TemplateView

from .forms import (
    DefectTypeForm,
    InspectorForm,
    ProductModelForm,
    ProductionLineForm,
    TestConditionForm,
    TestSessionForm,
    VerificationRecordForm,
)
from .models import (
    DefectType,
    InspectionResultType,
    InspectionRound,
    InspectionSession,
    InspectionTest,
    Inspector,
    ProductModel,
    ProductionLine,
    TestCondition,
    VerificationRecord,
)
from .services import DashboardService
from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES




def set_language(request, language):
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    request.session["ui_language"] = language
    response = redirect(request.GET.get("next") or request.META.get("HTTP_REFERER") or "inspection:dashboard")
    response.set_cookie("ui_language", language, max_age=60 * 60 * 24 * 365)
    return response

FOUND_RESULT_NAME = "Found"
NOT_FOUND_RESULT_NAME = "Not Found"


def get_round_result_types():
    found, _ = InspectionResultType.objects.get_or_create(
        name=FOUND_RESULT_NAME,
        defaults={"description": "Defect was detected during the test round."},
    )
    not_found, _ = InspectionResultType.objects.get_or_create(
        name=NOT_FOUND_RESULT_NAME,
        defaults={"description": "Defect was not detected during the test round."},
    )
    return found, not_found


def build_next_session_number():
    today = date.today()
    prefix = today.strftime("TS%Y%m%d")
    existing_count = InspectionSession.objects.filter(session_number__startswith=prefix).count()
    candidate_number = existing_count + 1
    while True:
        session_number = f"{prefix}-{candidate_number:04d}"
        if not InspectionSession.objects.filter(session_number=session_number).exists():
            return session_number
        candidate_number += 1


def test_summary(test):
    found = 0
    not_found = 0
    completed = 0
    for round_item in test.rounds.all():
        if round_item.result_type_id:
            completed += 1
        result_name = round_item.result_type.name if round_item.result_type else ""
        if result_name == FOUND_RESULT_NAME:
            found += 1
        elif result_name == NOT_FOUND_RESULT_NAME:
            not_found += 1
    decided = found + not_found
    detection_rate = round((found / decided) * 100) if decided else 0
    return {
        "test": test,
        "found": found,
        "not_found": not_found,
        "completed": completed,
        "total_rounds": test.rounds.count(),
        "detection_rate": detection_rate,
    }


class DashboardView(TemplateView):
    template_name = "inspection/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = InspectionSession.objects.select_related("line", "product_model", "test_condition", "inspector")
        today = date.today()
        latest_sessions = sessions.order_by("-inspection_date", "-created_at")[:8]
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status=InspectionSession.STATUS_COMPLETED).count()
        active_sessions = sessions.exclude(status=InspectionSession.STATUS_COMPLETED).count()
        total_tests = InspectionTest.objects.count()
        context.update(
            {
                "latest_sessions": latest_sessions,
                "total_sessions": total_sessions,
                "today_sessions": sessions.filter(inspection_date=today).count(),
                "completed_sessions": completed_sessions,
                "active_sessions": active_sessions,
                "total_tests": total_tests,
                "completion_rate": round((completed_sessions / total_sessions) * 100) if total_sessions else 0,
            }
        )
        return context


class InspectionListView(ListView):
    model = InspectionSession
    template_name = "inspection/list.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        queryset = InspectionSession.objects.select_related("line", "product_model", "test_condition", "inspector")
        line_name = self.request.GET.get("line_name", "").strip()
        product_model = self.request.GET.get("product_model", "").strip()
        start_date = self.request.GET.get("start_date", "").strip()
        end_date = self.request.GET.get("end_date", "").strip()
        if line_name:
            queryset = queryset.filter(line__name__icontains=line_name)
        if product_model:
            queryset = queryset.filter(product_model__name__icontains=product_model)
        if start_date:
            queryset = queryset.filter(inspection_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(inspection_date__lte=end_date)
        return queryset.order_by("-inspection_date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["line_name"] = self.request.GET.get("line_name", "")
        context["product_model"] = self.request.GET.get("product_model", "")
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
            test = InspectionTest.objects.create(
                session=self.object,
                defect_type=defect,
                test_name=defect.name,
                total_rounds=total_rounds,
            )
            InspectionRound.objects.bulk_create(
                [InspectionRound(inspection_test=test, round_number=round_number) for round_number in range(1, total_rounds + 1)]
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
                test = InspectionTest.objects.create(session=self.object, defect_type=defect, test_name=defect.name, total_rounds=total_rounds)
            else:
                test.total_rounds = total_rounds
                test.save(update_fields=["total_rounds"])
            existing_round_numbers = set(test.rounds.values_list("round_number", flat=True))
            InspectionRound.objects.bulk_create(
                [
                    InspectionRound(inspection_test=test, round_number=round_number)
                    for round_number in range(1, total_rounds + 1)
                    if round_number not in existing_round_numbers
                ]
            )
        messages.success(self.request, "Test Session updated.")
        return HttpResponseRedirect(reverse("inspection:detail", kwargs={"pk": self.object.pk}))


class InspectionDetailView(DetailView):
    model = InspectionSession
    template_name = "inspection/detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return InspectionSession.objects.select_related("line", "product_model", "test_condition", "inspector").prefetch_related(
            Prefetch(
                "tests",
                queryset=InspectionTest.objects.select_related("defect_type").prefetch_related(
                    Prefetch("rounds", queryset=InspectionRound.objects.select_related("result_type").order_by("round_number"))
                ),
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        found_result, not_found_result = get_round_result_types()
        action = request.POST.get("action", "save")
        current_index = int(request.POST.get("current_index") or 0)
        current_test_id = request.POST.get("current_test_id")
        if current_test_id:
            rounds = InspectionRound.objects.filter(inspection_test_id=current_test_id, inspection_test__session=self.object)
            for round_item in rounds:
                result_value = request.POST.get(f"result_{round_item.pk}", "")
                comment_value = request.POST.get(f"comment_{round_item.pk}", "")
                if result_value == "found":
                    round_item.result_type = found_result
                elif result_value == "not_found":
                    round_item.result_type = not_found_result
                round_item.comment = comment_value
                round_item.save(update_fields=["result_type", "comment"])
        tests_count = self.object.tests.count()
        if action == "finish":
            self.object.status = InspectionSession.STATUS_COMPLETED
            self.object.save(update_fields=["status"])
            messages.success(request, "Test Session finished.")
            return HttpResponseRedirect(f"{reverse('inspection:detail', kwargs={'pk': self.object.pk})}?summary=1")
        if action == "previous":
            current_index = max(0, current_index - 1)
        elif action == "next":
            current_index = min(max(tests_count - 1, 0), current_index + 1)
        messages.success(request, "Testing progress saved.")
        return HttpResponseRedirect(f"{reverse('inspection:detail', kwargs={'pk': self.object.pk})}?defect={current_index}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        found_result, not_found_result = get_round_result_types()
        tests = list(self.object.tests.all())
        current_index = int(self.request.GET.get("defect") or 0)
        current_index = min(max(current_index, 0), max(len(tests) - 1, 0)) if tests else 0
        summaries = [test_summary(test) for test in tests]
        context.update(
            {
                "tests": tests,
                "current_test": tests[current_index] if tests else None,
                "current_index": current_index,
                "display_index": current_index + 1,
                "total_tests": len(tests),
                "progress_percent": round(((current_index + 1) / len(tests)) * 100) if tests else 0,
                "summaries": summaries,
                "current_summary": summaries[current_index] if summaries else None,
                "found_result": found_result,
                "not_found_result": not_found_result,
                "show_summary": self.request.GET.get("summary") == "1",
            }
        )
        return context


class InspectionDeleteView(DeleteView):
    model = InspectionSession
    template_name = "inspection/confirm_delete.html"
    success_url = reverse_lazy("inspection:list")

    def form_valid(self, form):
        messages.success(self.request, "Test Session deleted.")
        return super().form_valid(form)


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


class MasterDataListView(ListView):
    template_name = "inspection/master_data_list.html"
    context_object_name = "items"
    page_title = ""
    create_url_name = ""
    update_url_name = ""
    delete_url_name = ""

    def get_queryset(self):
        return super().get_queryset().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["create_url_name"] = self.create_url_name
        context["update_url_name"] = self.update_url_name
        context["delete_url_name"] = self.delete_url_name
        return context


class MasterDataCreateView(CreateView):
    template_name = "inspection/master_data_form.html"
    page_title = ""
    success_url_name = ""

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)

    def form_valid(self, form):
        response = super().form_valid(form)
        DashboardService.invalidate_cache()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["is_update"] = False
        context["name_help"] = getattr(self, "name_help", "")
        context["description_help"] = getattr(self, "description_help", "")
        context["active_help"] = getattr(self, "active_help", "")
        return context


class MasterDataUpdateView(UpdateView):
    template_name = "inspection/master_data_form.html"
    page_title = ""
    success_url_name = ""

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)

    def form_valid(self, form):
        response = super().form_valid(form)
        DashboardService.invalidate_cache()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["is_update"] = True
        context["name_help"] = getattr(self, "name_help", "")
        context["description_help"] = getattr(self, "description_help", "")
        context["active_help"] = getattr(self, "active_help", "")
        return context


class MasterDataDeleteView(DeleteView):
    template_name = "inspection/master_data_confirm_delete.html"
    page_title = ""
    success_url_name = ""

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)

    def form_valid(self, form):
        response = super().form_valid(form)
        DashboardService.invalidate_cache()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class ProductionLineListView(MasterDataListView):
    model = ProductionLine
    page_title = "ไลน์ผลิต"
    create_url_name = "inspection:production_line_create"
    update_url_name = "inspection:production_line_update"
    delete_url_name = "inspection:production_line_delete"


class ProductionLineCreateView(MasterDataCreateView):
    model = ProductionLine
    form_class = ProductionLineForm
    page_title = "เพิ่มไลน์ผลิต"
    name_help = "กรอกชื่อไลน์ผลิต เช่น Line A, Line 1, Final Assembly"
    description_help = "อธิบายว่าไลน์นี้ใช้กับงานหรือสินค้ากลุ่มใด เช่น Main line for Model X"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:production_line_list"


class ProductionLineUpdateView(MasterDataUpdateView):
    model = ProductionLine
    form_class = ProductionLineForm
    page_title = "แก้ไขไลน์ผลิต"
    name_help = "กรอกชื่อไลน์ผลิต เช่น Line A, Line 1, Final Assembly"
    description_help = "อธิบายว่าไลน์นี้ใช้กับงานหรือสินค้ากลุ่มใด เช่น Main line for Model X"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:production_line_list"


class ProductionLineDeleteView(MasterDataDeleteView):
    model = ProductionLine
    page_title = "ลบไลน์ผลิต"
    success_url_name = "inspection:production_line_list"


class ProductModelListView(MasterDataListView):
    model = ProductModel
    page_title = "รุ่นสินค้า"
    create_url_name = "inspection:product_model_create"
    update_url_name = "inspection:product_model_update"
    delete_url_name = "inspection:product_model_delete"


class ProductModelCreateView(MasterDataCreateView):
    model = ProductModel
    form_class = ProductModelForm
    page_title = "เพิ่มรุ่นสินค้า"
    name_help = "กรอกรุ่นสินค้า เช่น Model X-100, Bracket LH, Cover RH"
    description_help = "อธิบายชิ้นงานหรือรุ่นที่ใช้ทดสอบ เช่น Camera validation part"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:product_model_list"


class ProductModelUpdateView(MasterDataUpdateView):
    model = ProductModel
    form_class = ProductModelForm
    page_title = "แก้ไขรุ่นสินค้า"
    name_help = "กรอกรุ่นสินค้า เช่น Model X-100, Bracket LH, Cover RH"
    description_help = "อธิบายชิ้นงานหรือรุ่นที่ใช้ทดสอบ เช่น Camera validation part"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:product_model_list"


class ProductModelDeleteView(MasterDataDeleteView):
    model = ProductModel
    page_title = "ลบรุ่นสินค้า"
    success_url_name = "inspection:product_model_list"


class InspectorListView(MasterDataListView):
    model = Inspector
    page_title = "Inspectors"
    create_url_name = "inspection:inspector_create"
    update_url_name = "inspection:inspector_update"
    delete_url_name = "inspection:inspector_delete"


class InspectorCreateView(MasterDataCreateView):
    model = Inspector
    form_class = InspectorForm
    page_title = "เพิ่ม Inspector"
    name_help = "กรอกชื่อผู้ทดสอบ เช่น Somchai, Inspector A, QA Line 1"
    description_help = "ใส่รายละเอียดเพิ่มเติม เช่น Day shift inspector for Line A"
    active_help = "เปิดใช้งานเพื่อให้เลือกชื่อผู้ทดสอบใน Test Session ได้"
    success_url_name = "inspection:inspector_list"


class InspectorUpdateView(MasterDataUpdateView):
    model = Inspector
    form_class = InspectorForm
    page_title = "แก้ไข Inspector"
    name_help = "กรอกชื่อผู้ทดสอบ เช่น Somchai, Inspector A, QA Line 1"
    description_help = "ใส่รายละเอียดเพิ่มเติม เช่น Day shift inspector for Line A"
    active_help = "เปิดใช้งานเพื่อให้เลือกชื่อผู้ทดสอบใน Test Session ได้"
    success_url_name = "inspection:inspector_list"


class InspectorDeleteView(MasterDataDeleteView):
    model = Inspector
    page_title = "ลบ Inspector"
    success_url_name = "inspection:inspector_list"


class DefectTypeListView(MasterDataListView):
    model = DefectType
    page_title = "รายการของเสีย"
    create_url_name = "inspection:defect_type_create"
    update_url_name = "inspection:defect_type_update"
    delete_url_name = "inspection:defect_type_delete"


class DefectTypeCreateView(MasterDataCreateView):
    model = DefectType
    form_class = DefectTypeForm
    page_title = "เพิ่มรายการของเสีย"
    name_help = "กรอกชนิด defect เช่น Spatter, Leak, Scratch, Gap, Dent"
    description_help = "อธิบายลักษณะ defect เช่น Surface scratch near welding point"
    active_help = "เปิดใช้งานเพื่อให้ defect นี้แสดงเป็น checkbox card ใน Test Session"
    success_url_name = "inspection:defect_type_list"


class DefectTypeUpdateView(MasterDataUpdateView):
    model = DefectType
    form_class = DefectTypeForm
    page_title = "แก้ไขรายการของเสีย"
    name_help = "กรอกชนิด defect เช่น Spatter, Leak, Scratch, Gap, Dent"
    description_help = "อธิบายลักษณะ defect เช่น Surface scratch near welding point"
    active_help = "เปิดใช้งานเพื่อให้ defect นี้แสดงเป็น checkbox card ใน Test Session"
    success_url_name = "inspection:defect_type_list"


class DefectTypeDeleteView(MasterDataDeleteView):
    model = DefectType
    page_title = "ลบรายการของเสีย"
    success_url_name = "inspection:defect_type_list"


class TestConditionListView(MasterDataListView):
    model = TestCondition
    page_title = "ประเภทการทดสอบ"
    create_url_name = "inspection:test_condition_create"
    update_url_name = "inspection:test_condition_update"
    delete_url_name = "inspection:test_condition_delete"


class TestConditionCreateView(MasterDataCreateView):
    model = TestCondition
    form_class = TestConditionForm
    page_title = "เพิ่มประเภทการทดสอบ"
    name_help = "กรอกเงื่อนไขทดสอบ เช่น Normal Light, Low Light, Oil Condition"
    description_help = "อธิบายเงื่อนไข เช่น Test under normal factory lighting"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:test_condition_list"


class TestConditionUpdateView(MasterDataUpdateView):
    model = TestCondition
    form_class = TestConditionForm
    page_title = "แก้ไขประเภทการทดสอบ"
    name_help = "กรอกเงื่อนไขทดสอบ เช่น Normal Light, Low Light, Oil Condition"
    description_help = "อธิบายเงื่อนไข เช่น Test under normal factory lighting"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:test_condition_list"


class TestConditionDeleteView(MasterDataDeleteView):
    model = TestCondition
    page_title = "ลบประเภทการทดสอบ"
    success_url_name = "inspection:test_condition_list"