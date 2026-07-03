from django.db import migrations, models


NOT_FOUND_STOP_REASON = "NOT_FOUND reached 4 occurrences"


def backfill_test_completion_state(apps, schema_editor):
    InspectionTest = apps.get_model("inspection", "InspectionTest")
    InspectionRound = apps.get_model("inspection", "InspectionRound")

    for test in InspectionTest.objects.all().iterator():
        completed_rounds = 0
        not_found_count = 0
        for round_item in InspectionRound.objects.filter(inspection_test_id=test.pk, result_type__isnull=False).select_related("result_type"):
            completed_rounds = max(completed_rounds, round_item.round_number)
            if round_item.result_type and round_item.result_type.name == "Not Found":
                not_found_count += 1

        status = "in_progress"
        stop_reason = ""
        if not_found_count >= 4:
            status = "finished"
            stop_reason = NOT_FOUND_STOP_REASON
        elif completed_rounds and completed_rounds >= test.total_rounds:
            status = "finished"

        InspectionTest.objects.filter(pk=test.pk).update(
            completed_rounds=completed_rounds,
            status=status,
            stop_reason=stop_reason,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0008_inspectionresulttype_inspector_inspectionsession_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspectiontest",
            name="completed_rounds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="inspectiontest",
            name="status",
            field=models.CharField(
                choices=[("in_progress", "In Progress"), ("finished", "Finished")],
                db_index=True,
                default="in_progress",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="inspectiontest",
            name="stop_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddIndex(
            model_name="inspectiontest",
            index=models.Index(fields=["status"], name="test_status_idx"),
        ),
        migrations.RunPython(backfill_test_completion_state, migrations.RunPython.noop),
    ]
