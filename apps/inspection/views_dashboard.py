from datetime import date

from django.views.generic.base import TemplateView

from .models import InspectionSession, InspectionTest


class DashboardView(TemplateView):
    template_name = "inspection/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = InspectionSession.objects.select_related("line", "test_condition", "inspector")
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
