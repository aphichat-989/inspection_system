from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0009_inspectiontest_completion_state"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="inspectionsession",
            name="session_model_date_idx",
        ),
        migrations.RemoveIndex(
            model_name="inspectionrecord",
            name="insp_model_date_idx",
        ),
        migrations.RemoveField(
            model_name="inspectionsession",
            name="product_model",
        ),
        migrations.RemoveField(
            model_name="inspectionrecord",
            name="product_model",
        ),
        migrations.DeleteModel(
            name="ProductModel",
        ),
    ]
