# Generated manually for relational inspection defects.

import json

import django.db.models.deletion
from django.db import migrations, models


def migrate_defect_json_to_rows(apps, schema_editor):
    InspectionRecord = apps.get_model("inspection", "InspectionRecord")
    InspectionDefect = apps.get_model("inspection", "InspectionDefect")

    rows = []
    for inspection in InspectionRecord.objects.exclude(defect_list="").iterator(chunk_size=1000):
        try:
            payload = json.loads(inspection.defect_list or "{}")
        except (TypeError, ValueError):
            continue

        for raw_key, raw_value in payload.items():
            key = str(raw_key).removeprefix("defect_")
            parts = key.split("_", 1)
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                continue
            try:
                quantity = int(raw_value or 0)
            except (TypeError, ValueError):
                continue
            if quantity <= 0:
                continue
            rows.append(
                InspectionDefect(
                    inspection_id=inspection.pk,
                    test_condition_id=int(parts[0]),
                    defect_type_id=int(parts[1]),
                    quantity=quantity,
                )
            )
            if len(rows) >= 1000:
                InspectionDefect.objects.bulk_create(rows, ignore_conflicts=True)
                rows = []

    if rows:
        InspectionDefect.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0005_alter_defecttype_is_active_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="InspectionDefect",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "defect_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inspection_defects",
                        to="inspection.defecttype",
                    ),
                ),
                (
                    "inspection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="defects",
                        to="inspection.inspectionrecord",
                    ),
                ),
                (
                    "test_condition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inspection_defects",
                        to="inspection.testcondition",
                    ),
                ),
            ],
            options={
                "ordering": ["test_condition__name", "defect_type__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="inspectiondefect",
            constraint=models.UniqueConstraint(
                fields=("inspection", "test_condition", "defect_type"),
                name="uniq_inspection_defect_condition_type",
            ),
        ),
        migrations.AddIndex(
            model_name="inspectiondefect",
            index=models.Index(fields=["inspection", "test_condition"], name="inspdef_inspection_cond_idx"),
        ),
        migrations.AddIndex(
            model_name="inspectiondefect",
            index=models.Index(fields=["defect_type", "test_condition"], name="inspdef_type_cond_idx"),
        ),
        migrations.AddIndex(
            model_name="inspectiondefect",
            index=models.Index(fields=["test_condition", "defect_type"], name="inspdef_cond_type_idx"),
        ),
        migrations.RunPython(migrate_defect_json_to_rows, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="inspectionrecord",
            name="defect_list",
        ),
    ]
