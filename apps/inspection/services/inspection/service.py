from dataclasses import dataclass

from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Q

from ...models import DefectType, InspectionDefect, InspectionRecord, ProductModel, TestCondition
from ..analytics.defect_service import DefectAnalyticsService
from ..production.line_service import ProductionLineService


DASHBOARD_CACHE_VERSION_KEY = "inspection:dashboard:version"


@dataclass(frozen=True)
class InspectionFilters:
    line_id: str = ""
    line_name: str = ""
    product_model: str = ""
    test_condition_id: str = ""
    start_date: str = ""
    end_date: str = ""

    @classmethod
    def from_request(cls, request):
        return cls(
            line_id=request.GET.get("line_id", "").strip(),
            line_name=request.GET.get("line_name", "").strip(),
            product_model=request.GET.get("product_model", "").strip(),
            test_condition_id=request.GET.get("test_condition_id", "").strip(),
            start_date=request.GET.get("start_date", "").strip(),
            end_date=request.GET.get("end_date", "").strip(),
        )

    def cache_parts(self):
        return (
            self.line_id or "all-lines",
            self.line_name or "no-line-name",
            self.product_model or "all-models",
            self.test_condition_id or "all-conditions",
            self.start_date or "open-start",
            self.end_date or "open-end",
        )


class InspectionReadService:
    @staticmethod
    def base_queryset():
        return InspectionRecord.objects.select_related("line", "product_model", "test_condition")

    @staticmethod
    def filtered_queryset(filters):
        queryset = InspectionReadService.base_queryset()
        queryset = ProductionLineService.apply_line_filter(queryset, filters)

        if filters.product_model:
            queryset = queryset.filter(Q(product_model__name__icontains=filters.product_model) | Q(part_name__icontains=filters.product_model) | Q(sd_code__icontains=filters.product_model))
        if filters.test_condition_id:
            queryset = queryset.filter(test_condition_id=filters.test_condition_id)
        if filters.start_date:
            queryset = queryset.filter(inspection_date__gte=filters.start_date)
        if filters.end_date:
            queryset = queryset.filter(inspection_date__lte=filters.end_date)

        return queryset.order_by("-inspection_date", "-inspection_time", "-created_at")

    @staticmethod
    def detail_queryset():
        return InspectionReadService.base_queryset().prefetch_related(
            Prefetch(
                "defects",
                queryset=InspectionDefect.objects.select_related("test_condition", "defect_type"),
            )
        )

    @staticmethod
    def get_form_context(record=None):
        defect_types = DefectType.objects.filter(is_active=True).order_by("name")
        test_conditions = TestCondition.objects.filter(is_active=True).order_by("name")
        defect_values = DefectAnalyticsService.defect_value_map(record)

        dynamic_defect_groups = []
        for test_condition in test_conditions:
            defects = []
            for defect_type in defect_types:
                key = f"{test_condition.pk}_{defect_type.pk}"
                defects.append(
                    {
                        "defect_type": defect_type,
                        "name": f"defect_{test_condition.pk}_{defect_type.pk}",
                        "machine_value": defect_values.get(key, {}).get("machine_quantity", ""),
                        "pqc_value": defect_values.get(key, {}).get("pqc_quantity", ""),
                    }
                )
            dynamic_defect_groups.append({"test_condition": test_condition, "defects": defects})

        return {
            "defect_types": defect_types,
            "test_conditions": test_conditions,
            "product_models": ProductModel.objects.filter(is_active=True).order_by("name"),
            "production_lines": ProductionLineService.active_lines(),
            "dynamic_defect_groups": dynamic_defect_groups,
        }


class InspectionWriteService:
    @staticmethod
    @transaction.atomic
    def save_inspection_with_defects(form, post_data):
        inspection = form.save(commit=False)
        inspection.save()
        form.save_m2m()
        InspectionWriteService.replace_defects(inspection, post_data)
        InspectionWriteService.invalidate_dashboard_cache()
        return inspection

    @staticmethod
    def replace_defects(inspection, post_data):
        defect_values = [
            item
            for item in DefectAnalyticsService.collect_dynamic_defect_values(post_data)
            if item["test_condition_id"] == inspection.test_condition_id
        ]
        inspection.defects.all().delete()
        InspectionDefect.objects.bulk_create(
            [
                InspectionDefect(
                    inspection=inspection,
                    test_condition_id=item["test_condition_id"],
                    defect_type_id=item["defect_type_id"],
                    machine_quantity=item["machine_quantity"],
                    pqc_quantity=item["pqc_quantity"],
                    quantity=item["quantity"],
                )
                for item in defect_values
            ],
            batch_size=500,
        )

    @staticmethod
    def invalidate_dashboard_cache():
        try:
            cache.incr(DASHBOARD_CACHE_VERSION_KEY)
        except ValueError:
            cache.set(DASHBOARD_CACHE_VERSION_KEY, 2, None)

