from django.db.models import Sum
from django.db.models.functions import Coalesce

from ...models import InspectionDefect


class DefectAnalyticsService:
    @staticmethod
    def collect_dynamic_defect_values(post_data):
        grouped = {}
        for key, values_list in post_data.lists():
            if not (key.startswith("defectmc_") or key.startswith("defectpqc_") or key.startswith("defect_")):
                continue
            parts = key.split("_")
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                continue
            raw_value = values_list[-1].strip()
            if not raw_value:
                continue
            try:
                quantity = int(raw_value)
            except ValueError:
                continue
            if quantity <= 0:
                continue

            item_key = (int(parts[1]), int(parts[2]))
            item = grouped.setdefault(
                item_key,
                {
                    "test_condition_id": item_key[0],
                    "defect_type_id": item_key[1],
                    "machine_quantity": 0,
                    "pqc_quantity": 0,
                },
            )
            if key.startswith("defectmc_"):
                item["machine_quantity"] += quantity
            elif key.startswith("defectpqc_"):
                item["pqc_quantity"] += quantity
            else:
                item["machine_quantity"] += quantity

        return [
            {**item, "quantity": item["machine_quantity"] + item["pqc_quantity"]}
            for item in grouped.values()
            if item["machine_quantity"] + item["pqc_quantity"] > 0
        ]

    @staticmethod
    def defect_value_map(inspection):
        if not inspection or not getattr(inspection, "pk", None):
            return {}
        values = {}
        for row in inspection.defects.all():
            key = f"{row.test_condition_id}_{row.defect_type_id}"
            values[key] = {
                "machine_quantity": row.machine_quantity or row.quantity or 0,
                "pqc_quantity": row.pqc_quantity or 0,
                "quantity": row.quantity or 0,
            }
        return values

    @staticmethod
    def distribution(filters=None, limit=8):
        queryset = InspectionDefect.objects.select_related("defect_type", "test_condition")
        queryset = DefectAnalyticsService._apply_inspection_filters(queryset, filters)
        queryset = (
            queryset.values("defect_type_id", "defect_type__name")
            .annotate(count=Coalesce(Sum("quantity"), 0))
            .order_by("-count", "defect_type__name")
        )
        if limit:
            queryset = queryset[:limit]
        return [
            {"id": row["defect_type_id"], "name": row["defect_type__name"], "count": row["count"]}
            for row in queryset
        ]

    @staticmethod
    def total_defects(filters=None):
        queryset = InspectionDefect.objects.all()
        queryset = DefectAnalyticsService._apply_inspection_filters(queryset, filters)
        totals = queryset.aggregate(
            machine=Coalesce(Sum("machine_quantity"), 0),
            pqc=Coalesce(Sum("pqc_quantity"), 0),
            legacy=Coalesce(Sum("quantity"), 0),
        )
        split_total = (totals["machine"] or 0) + (totals["pqc"] or 0)
        return split_total or (totals["legacy"] or 0)

    @staticmethod
    def record_defect_rows(inspection):
        rows = []
        for defect in inspection.defects.select_related("test_condition", "defect_type").order_by(
            "test_condition__name", "defect_type__name"
        ):
            machine_quantity = defect.machine_quantity or defect.quantity or 0
            pqc_quantity = defect.pqc_quantity or 0
            rows.append(
                {
                    "test_condition": defect.test_condition.name,
                    "defect_type": defect.defect_type.name,
                    "machine_count": machine_quantity,
                    "pqc_count": pqc_quantity,
                    "count": machine_quantity + pqc_quantity,
                }
            )
        return rows

    @staticmethod
    def _apply_inspection_filters(queryset, filters):
        if filters is None:
            return queryset
        if filters.line_id:
            queryset = queryset.filter(inspection__line_id=filters.line_id)
        if filters.line_name:
            queryset = queryset.filter(inspection__line__name__icontains=filters.line_name)
        if filters.test_condition_id:
            queryset = queryset.filter(test_condition_id=filters.test_condition_id)
        if filters.start_date:
            queryset = queryset.filter(inspection__inspection_date__gte=filters.start_date)
        if filters.end_date:
            queryset = queryset.filter(inspection__inspection_date__lte=filters.end_date)
        return queryset




