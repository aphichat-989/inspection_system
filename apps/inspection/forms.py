from datetime import datetime

from django import forms

from .models import (
    DefectType,
    InspectionSession,
    Inspector,
    ProductionLine,
    TestCondition,
    VerificationRecord,
)


class TestSessionForm(forms.ModelForm):
    session_number = forms.CharField(
        label="Session Number",
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "readonly": "readonly"}),
    )

    def __init__(self, *args, **kwargs):
        session_number = kwargs.pop("session_number", "")
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial.setdefault("inspection_date", datetime.now().date().strftime("%Y-%m-%d"))
        self.initial.setdefault("session_number", self.instance.session_number or session_number)
        self.fields["line"].queryset = ProductionLine.objects.filter(is_active=True).order_by("name")
        self.fields["test_condition"].queryset = TestCondition.objects.filter(is_active=True).order_by("name")
        self.fields["inspector"].queryset = Inspector.objects.filter(is_active=True).order_by("name")
        self.fields["line"].empty_label = "Select production line"
        self.fields["test_condition"].empty_label = "Select test condition"
        self.fields["inspector"].empty_label = "Select inspector"

    class Meta:
        model = InspectionSession
        fields = [
            "session_number",
            "inspection_date",
            "line",
            "test_condition",
            "inspector",
            "overall_comment",
        ]
        labels = {
            "inspection_date": "Inspection Date",
            "line": "Production Line",
            "test_condition": "Test Condition",
            "inspector": "Inspector",
            "overall_comment": "Overall Comment",
        }
        widgets = {
            "inspection_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-lg"}),
            "line": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "test_condition": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "inspector": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "overall_comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Example: Camera exposure adjusted to 65 before testing. Jig V2 used under normal factory lighting.",
                }
            ),
        }


class VerificationRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial.setdefault("inspection_date", datetime.now().date().strftime("%Y-%m-%d"))
        self.fields["defect_type"].queryset = DefectType.objects.filter(is_active=True).order_by("name")
        self.fields["test_condition"].queryset = TestCondition.objects.filter(is_active=True).order_by("name")

    class Meta:
        model = VerificationRecord
        fields = [
            "inspection_date",
            "defect_type",
            "test_condition",
            "result",
            "round_no",
            "found_count",
            "not_found_count",
            "comment",
        ]
        labels = {
            "inspection_date": "วันที่",
            "defect_type": "Defect model",
            "test_condition": "Condition",
            "result": "Result",
            "round_no": "ครั้งที่",
            "found_count": "ตรวจเจอ",
            "not_found_count": "ตรวจไม่เจอ",
            "comment": "Comment",
        }
        widgets = {
            "inspection_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "defect_type": forms.Select(attrs={"class": "form-select"}),
            "test_condition": forms.Select(attrs={"class": "form-select"}),
            "result": forms.Select(attrs={"class": "form-select"}),
            "round_no": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "found_count": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "not_found_count": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class InspectorForm(forms.ModelForm):
    class Meta:
        model = Inspector
        fields = ["name", "description", "is_active"]
        labels = {"name": "ชื่อ Inspector", "description": "คำอธิบาย", "is_active": "ใช้งาน"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Somchai / Inspector A"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Example: Day-shift inspector for Line A"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProductionLineForm(forms.ModelForm):
    class Meta:
        model = ProductionLine
        fields = ["name", "description", "is_active"]
        labels = {"name": "ชื่อไลน์ผลิต", "description": "คำอธิบาย", "is_active": "ใช้งาน"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Line A / Final Assembly"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Example: Main production line for Model X"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class DefectTypeForm(forms.ModelForm):
    class Meta:
        model = DefectType
        fields = ["name", "description", "is_active"]
        labels = {"name": "ชื่อรายการของเสีย", "description": "คำอธิบาย", "is_active": "ใช้งาน"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Spatter / Leak / Scratch"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Example: Surface scratch visible near the welding point"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TestConditionForm(forms.ModelForm):
    class Meta:
        model = TestCondition
        fields = ["name", "description", "is_active"]
        labels = {"name": "ชื่อประเภทการทดสอบ", "description": "คำอธิบาย", "is_active": "ใช้งาน"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Example: Normal Light / Low Light / Oil Condition"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Example: Test under normal factory lighting at standard camera exposure"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

