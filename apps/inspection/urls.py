from django.urls import path

from . import views

urlpatterns = [
    path("language/<str:language>/", views.set_language, name="set_language"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("list/", views.InspectionListView.as_view(), name="list"),
    path("new/", views.InspectionCreateView.as_view(), name="create"),
    path("<int:pk>/", views.InspectionDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.InspectionUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.InspectionDeleteView.as_view(), name="delete"),
    path("verification/", views.VerificationListView.as_view(), name="verification_list"),
    path("verification/new/", views.VerificationCreateView.as_view(), name="verification_create"),
    path("verification/<int:pk>/edit/", views.VerificationUpdateView.as_view(), name="verification_update"),
    path("verification/<int:pk>/delete/", views.VerificationDeleteView.as_view(), name="verification_delete"),
    path("master-data/production-lines/", views.ProductionLineListView.as_view(), name="production_line_list"),
    path("master-data/production-lines/new/", views.ProductionLineCreateView.as_view(), name="production_line_create"),
    path("master-data/production-lines/<int:pk>/edit/", views.ProductionLineUpdateView.as_view(), name="production_line_update"),
    path("master-data/production-lines/<int:pk>/delete/", views.ProductionLineDeleteView.as_view(), name="production_line_delete"),
    path("master-data/inspectors/", views.InspectorListView.as_view(), name="inspector_list"),
    path("master-data/inspectors/new/", views.InspectorCreateView.as_view(), name="inspector_create"),
    path("master-data/inspectors/<int:pk>/edit/", views.InspectorUpdateView.as_view(), name="inspector_update"),
    path("master-data/inspectors/<int:pk>/delete/", views.InspectorDeleteView.as_view(), name="inspector_delete"),
    path("master-data/defect-types/", views.DefectTypeListView.as_view(), name="defect_type_list"),
    path("master-data/defect-types/new/", views.DefectTypeCreateView.as_view(), name="defect_type_create"),
    path("master-data/defect-types/<int:pk>/edit/", views.DefectTypeUpdateView.as_view(), name="defect_type_update"),
    path("master-data/defect-types/<int:pk>/delete/", views.DefectTypeDeleteView.as_view(), name="defect_type_delete"),
    path("master-data/test-conditions/", views.TestConditionListView.as_view(), name="test_condition_list"),
    path("master-data/test-conditions/new/", views.TestConditionCreateView.as_view(), name="test_condition_create"),
    path("master-data/test-conditions/<int:pk>/edit/", views.TestConditionUpdateView.as_view(), name="test_condition_update"),
    path("master-data/test-conditions/<int:pk>/delete/", views.TestConditionDeleteView.as_view(), name="test_condition_delete"),
]

