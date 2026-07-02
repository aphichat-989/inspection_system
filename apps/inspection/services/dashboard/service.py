from datetime import date

from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from ...models import TestCondition
from ..analytics.defect_service import DefectAnalyticsService
from ..inspection.service import InspectionReadService
from ..production.line_service import ProductionLineService


class DashboardService:
    CACHE_TIMEOUT_SECONDS = 30
    VERSION_KEY = "inspection:dashboard:version"

    @classmethod
    def get_context(cls, filters):
        cache_key = cls.cache_key(filters)
        cached_context = cache.get(cache_key)
        if cached_context is not None:
            return cached_context

        queryset = InspectionReadService.filtered_queryset(filters)
        today = date.today()
        totals = queryset.aggregate(
            total_records=Count("id"),
            total_tests=Coalesce(Sum("total_production"), 0),
            today_records=Count("id", filter=Q(inspection_date=today)),
        )
        total_tests = totals["total_tests"] or 0
        total_defects = DefectAnalyticsService.total_defects(filters)
        fail_rate = min(round((total_defects / total_tests) * 100, 2), 100) if total_tests else 0
        pass_rate = round(100 - fail_rate, 2) if total_tests else 0
        defect_distribution = DefectAnalyticsService.distribution(filters, limit=8)

        context = {
            "filters": filters,
            "production_lines": list(ProductionLineService.active_lines()),
            "test_conditions": list(TestCondition.objects.filter(is_active=True).order_by("name")),
            "total_records": totals["total_records"],
            "total_tests": total_tests,
            "today_records": totals["today_records"],
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
            "total_defects": total_defects,
            "condition_summary": list(cls.condition_summary(queryset)),
            "defect_distribution": defect_distribution,
            "most_common_defect": defect_distribution[0] if defect_distribution else None,
            "latest_records": list(queryset[:8]),
        }
        cache.set(cache_key, context, cls.CACHE_TIMEOUT_SECONDS)
        return context

    @staticmethod
    def condition_summary(queryset):
        return (
            queryset.values("test_condition_id", "test_condition__name")
            .annotate(total_records=Count("id"), total_tests=Coalesce(Sum("total_production"), 0))
            .order_by("test_condition__name")
        )

    @staticmethod
    def cache_key(filters):
        version = cache.get(DashboardService.VERSION_KEY, 1)
        return f"inspection:dashboard:v{version}:" + ":".join(filters.cache_parts())

    @staticmethod
    def invalidate_cache():
        try:
            cache.incr(DashboardService.VERSION_KEY)
        except ValueError:
            cache.set(DashboardService.VERSION_KEY, 2, None)
