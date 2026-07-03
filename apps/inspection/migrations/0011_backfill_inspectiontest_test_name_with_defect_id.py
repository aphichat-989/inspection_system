from django.db import migrations


def use_defect_id_as_test_name(apps, schema_editor):
    InspectionTest = apps.get_model("inspection", "InspectionTest")
    for test in InspectionTest.objects.all().iterator():
        value = str(test.defect_type_id or test.pk)
        InspectionTest.objects.filter(pk=test.pk).update(test_name=value)


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0010_remove_product_model"),
    ]

    operations = [
        migrations.RunPython(use_defect_id_as_test_name, migrations.RunPython.noop),
    ]