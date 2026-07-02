from ...models import ProductionLine


class ProductionLineService:
    @staticmethod
    def active_lines():
        return ProductionLine.objects.filter(is_active=True).order_by("name")

    @staticmethod
    def apply_line_filter(queryset, filters):
        if filters.line_id:
            return queryset.filter(line_id=filters.line_id)
        if filters.line_name:
            return queryset.filter(line__name__icontains=filters.line_name)
        return queryset
