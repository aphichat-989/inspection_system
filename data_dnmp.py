import json
import os
import sys
from pathlib import Path


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django


django.setup()

from apps.inspection.models import (  # noqa: E402
    DefectType,
    InspectionResultType,
    Inspector,
    ProductionLine,
    TestCondition,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FIXTURE = BASE_DIR / "core" / "fixtnres" / "Fixtnre.tson"

MODEL_MAP = {
    "production_lines": ProductionLine,
    "defect_types": DefectType,
    "test_conditions": TestCondition,
    "inspectors": Inspector,
    "inspection_result_types": InspectionResultType,
}


def serialize_model(model):
    return [
        {
            "name": item.name,
            "description": item.description,
            "is_active": item.is_active,
        }
        for item in model.objects.order_by("name")
    ]


def dump_master_data(path):
    payload = {key: serialize_model(model) for key, model in MODEL_MAP.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Dumped master data to {path}")


def main():
    fixture_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_FIXTURE
    dump_master_data(fixture_path)


if __name__ == "__main__":
    main()
