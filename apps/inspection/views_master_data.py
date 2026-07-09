from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import DefectTypeForm, InspectorForm, ProductionLineForm, TestConditionForm
from .models import DefectType, Inspector, ProductionLine, TestCondition
from .services import DashboardService
from .views_permissions import StaffRequiredMixin


class MasterDataListView(StaffRequiredMixin, ListView):
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


class MasterDataCreateView(StaffRequiredMixin, CreateView):
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


class MasterDataUpdateView(StaffRequiredMixin, UpdateView):
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


class MasterDataDeleteView(StaffRequiredMixin, DeleteView):
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
    name_help = "กรอกประเภทการทดสอบ เช่น Normal Light, Low Light, Oil Condition"
    description_help = "อธิบายประเภทการทดสอบ เช่น Test under normal factory lighting"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:test_condition_list"


class TestConditionUpdateView(MasterDataUpdateView):
    model = TestCondition
    form_class = TestConditionForm
    page_title = "แก้ไขประเภทการทดสอบ"
    name_help = "กรอกประเภทการทดสอบ เช่น Normal Light, Low Light, Oil Condition"
    description_help = "อธิบายประเภทการทดสอบ เช่น Test under normal factory lighting"
    active_help = "เปิดใช้งานเพื่อให้เลือกได้ในหน้า Create New Test Session"
    success_url_name = "inspection:test_condition_list"


class TestConditionDeleteView(MasterDataDeleteView):
    model = TestCondition
    page_title = "ลบประเภทการทดสอบ"
    success_url_name = "inspection:test_condition_list"


