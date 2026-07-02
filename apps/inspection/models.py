from datetime import date, time

from django.db import models


class BaseMasterModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductionLine(BaseMasterModel):
    pass


class ProductModel(BaseMasterModel):
    pass


class DefectType(BaseMasterModel):
    pass


class TestCondition(BaseMasterModel):
    pass


class Inspector(BaseMasterModel):
    pass


class InspectionResultType(BaseMasterModel):
    pass


class InspectionSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    session_number = models.CharField(max_length=50, unique=True, db_index=True)
    inspection_date = models.DateField(default=date.today, db_index=True)
    line = models.ForeignKey(ProductionLine, on_delete=models.PROTECT, related_name="inspection_sessions")
    product_model = models.ForeignKey(ProductModel, on_delete=models.PROTECT, related_name="inspection_sessions")
    test_condition = models.ForeignKey(TestCondition, on_delete=models.PROTECT, related_name="inspection_sessions")
    inspector = models.ForeignKey(Inspector, on_delete=models.PROTECT, related_name="inspection_sessions")
    overall_comment = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inspection_date", "-created_at"]
        indexes = [
            models.Index(fields=["inspection_date", "line"], name="session_date_line_idx"),
            models.Index(fields=["product_model", "inspection_date"], name="session_model_date_idx"),
            models.Index(fields=["test_condition", "inspection_date"], name="session_cond_date_idx"),
            models.Index(fields=["inspector", "inspection_date"], name="session_insp_date_idx"),
            models.Index(fields=["status", "inspection_date"], name="session_status_date_idx"),
        ]

    def __str__(self):
        return self.session_number


class InspectionTest(models.Model):
    session = models.ForeignKey(InspectionSession, on_delete=models.CASCADE, related_name="tests")
    defect_type = models.ForeignKey(
        DefectType,
        on_delete=models.PROTECT,
        related_name="inspection_tests",
        blank=True,
        null=True,
    )
    test_name = models.CharField(max_length=150, blank=True, default="")
    total_rounds = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["defect_type__name", "test_name", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "defect_type"],
                name="uniq_session_defect_test",
            )
        ]
        indexes = [
            models.Index(fields=["session", "defect_type"], name="test_session_defect_idx"),
            models.Index(fields=["defect_type"], name="test_defect_idx"),
        ]

    def __str__(self):
        return self.test_name or str(self.defect_type or self.pk)


class InspectionRound(models.Model):
    inspection_test = models.ForeignKey(InspectionTest, on_delete=models.CASCADE, related_name="rounds")
    round_number = models.PositiveIntegerField()
    result_type = models.ForeignKey(
        InspectionResultType,
        on_delete=models.PROTECT,
        related_name="inspection_rounds",
        blank=True,
        null=True,
    )
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inspection_test", "round_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["inspection_test", "round_number"],
                name="uniq_test_round_number",
            )
        ]
        indexes = [
            models.Index(fields=["inspection_test", "round_number"], name="round_test_number_idx"),
            models.Index(fields=["result_type"], name="round_result_type_idx"),
        ]

    def __str__(self):
        return f"{self.inspection_test} - Round {self.round_number}"


class InspectionRecord(models.Model):
    RESULT_OK = "ok"
    RESULT_NG = "ng"
    RESULT_PENDING = "pending"
    RESULT_CHOICES = [
        (RESULT_OK, "OK"),
        (RESULT_NG, "NG"),
        (RESULT_PENDING, "Pending"),
    ]

    inspection_date = models.DateField(default=date.today, db_index=True)
    inspection_time = models.TimeField(default=time(8, 0))
    initial_control = models.BooleanField(default=False, db_index=True)
    verify = models.BooleanField(default=False, db_index=True)
    sd_code = models.CharField(max_length=100, blank=True, default="", db_index=True)
    part_name = models.CharField(max_length=200, blank=True, default="")
    line = models.ForeignKey(ProductionLine, on_delete=models.PROTECT, related_name="inspection_records")
    product_model = models.ForeignKey(ProductModel, on_delete=models.PROTECT, related_name="inspection_records")
    test_condition = models.ForeignKey(TestCondition, on_delete=models.PROTECT, related_name="inspection_records")
    total_production = models.PositiveIntegerField(default=0)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default=RESULT_PENDING, db_index=True)
    machine_ng = models.PositiveIntegerField(default=0)
    machine_ok = models.PositiveIntegerField(default=0)
    pqc_ng = models.PositiveIntegerField(default=0)
    pqc_ok = models.PositiveIntegerField(default=0)
    kanban_mismatch_count = models.PositiveIntegerField(default=0)
    bush_vertical_defect_count = models.PositiveIntegerField(default=0)
    spatter_count = models.PositiveIntegerField(default=0)
    forgotten_bush_vertical_count = models.PositiveIntegerField(default=0)
    not_enter_bush_vertical_count = models.PositiveIntegerField(default=0)
    bush_vertical_misaligned_count = models.PositiveIntegerField(default=0)
    stopper_leak_count = models.PositiveIntegerField(default=0)
    round_recline_leak_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inspection_date", "-inspection_time", "-created_at"]
        indexes = [
            models.Index(fields=["inspection_date", "line"], name="insp_date_line_idx"),
            models.Index(fields=["line", "inspection_date", "inspection_time"], name="insp_line_date_time_idx"),
            models.Index(fields=["product_model", "inspection_date"], name="insp_model_date_idx"),
            models.Index(fields=["test_condition", "inspection_date"], name="insp_cond_date_idx"),
            models.Index(fields=["sd_code", "inspection_date"], name="insp_sd_code_date_idx"),
            models.Index(fields=["result", "inspection_date"], name="insp_result_date_idx"),
        ]

    def __str__(self):
        return f"{self.inspection_date} - {self.sd_code or self.product_model}"


class InspectionDefect(models.Model):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="defects")
    test_condition = models.ForeignKey(TestCondition, on_delete=models.PROTECT, related_name="inspection_defects")
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="inspection_defects")
    machine_quantity = models.PositiveIntegerField(default=0)
    pqc_quantity = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["test_condition__name", "defect_type__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["inspection", "test_condition", "defect_type"],
                name="uniq_inspection_defect_condition_type",
            )
        ]
        indexes = [
            models.Index(fields=["inspection", "test_condition"], name="inspdef_inspection_cond_idx"),
            models.Index(fields=["defect_type", "test_condition"], name="inspdef_type_cond_idx"),
            models.Index(fields=["test_condition", "defect_type"], name="inspdef_cond_type_idx"),
        ]

    def __str__(self):
        return f"{self.inspection_id} - {self.test_condition} - {self.defect_type}: {self.quantity}"


class VerificationRecord(models.Model):
    RESULT_FOUND = "found"
    RESULT_NOT_FOUND = "not_found"
    RESULT_PENDING = "pending"
    RESULT_CHOICES = [
        (RESULT_FOUND, "ตรวจเจอ"),
        (RESULT_NOT_FOUND, "ตรวจไม่เจอ"),
        (RESULT_PENDING, "Pending"),
    ]

    inspection_date = models.DateField(default=date.today, db_index=True)
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="verification_records")
    test_condition = models.ForeignKey(TestCondition, on_delete=models.PROTECT, related_name="verification_records")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default=RESULT_PENDING, db_index=True)
    round_no = models.PositiveIntegerField(default=1)
    found_count = models.PositiveIntegerField(default=0)
    not_found_count = models.PositiveIntegerField(default=0)
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inspection_date", "-round_no", "-created_at"]
        indexes = [
            models.Index(fields=["inspection_date", "defect_type"], name="verify_date_defect_idx"),
            models.Index(fields=["test_condition", "inspection_date"], name="verify_cond_date_idx"),
            models.Index(fields=["result", "inspection_date"], name="verify_result_date_idx"),
        ]

    def __str__(self):
        return f"{self.inspection_date} - {self.defect_type} - รอบ {self.round_no}"
