from django.contrib import admin

from .models import (
    DefectType,
    InspectionDefect,
    InspectionRecord,
    Inspector,
    ProductionLine,
    TestCondition,
    VerificationRecord,
)


@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name", "description")


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name", "description")


@admin.register(TestCondition)
class TestConditionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name", "description")


@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name", "description")


class InspectionDefectInline(admin.TabularInline):
    model = InspectionDefect
    extra = 0
    fields = ("test_condition", "defect_type", "machine_quantity", "pqc_quantity", "quantity")
    autocomplete_fields = ("test_condition", "defect_type")


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "inspection_date",
        "sd_code",
        "part_name",
        "line",
        "test_condition",
        "total_production",
        "result",
        "initial_control",
        "verify",
        "created_at",
    )
    list_filter = ("result", "initial_control", "verify", "test_condition", "inspection_date", "line")
    search_fields = ("sd_code", "part_name", "line__name", "test_condition__name", "notes")
    inlines = (InspectionDefectInline,)


@admin.register(InspectionDefect)
class InspectionDefectAdmin(admin.ModelAdmin):
    list_display = ("inspection", "test_condition", "defect_type", "machine_quantity", "pqc_quantity", "quantity")
    list_filter = ("test_condition", "defect_type")
    search_fields = ("inspection__sd_code", "inspection__part_name", "inspection__line__name", "defect_type__name")
    autocomplete_fields = ("inspection", "test_condition", "defect_type")


@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ("inspection_date", "defect_type", "test_condition", "result", "round_no", "found_count", "not_found_count", "created_at")
    list_filter = ("result", "test_condition", "defect_type", "inspection_date")
    search_fields = ("defect_type__name", "test_condition__name", "comment")
    autocomplete_fields = ("defect_type", "test_condition")

