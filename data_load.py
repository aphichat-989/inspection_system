import json
import os
import re
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


def strip_json_comments(text):
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r",(\s*[}\]])", r"\1", text)


def load_tson(path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(strip_json_comments(text))


def normalize_items(payload, key):
    items = payload.get(key, [])
    if not isinstance(items, list):
        raise ValueError(f"{key} must be a list")
    return items


def upsert_master_data(payload):
    total_created = 0
    total_updated = 0

    for key, model in MODEL_MAP.items():
        created_count = 0
        updated_count = 0
        for item in normalize_items(payload, key):
            name = str(item.get("name", "")).strip()
            if not name:
                raise ValueError(f"{key} has an item without name")

            defaults = {
                "description": str(item.get("description", "") or ""),
                "is_active": bool(item.get("is_active", True)),
            }
            _, created = model.objects.update_or_create(name=name, defaults=defaults)
            if created:
                created_count += 1
            else:
                updated_count += 1

        total_created += created_count
        total_updated += updated_count
        print(f"{key}: created={created_count}, updated={updated_count}")

    print(f"Done. created={total_created}, updated={total_updated}")


def main():
    fixture_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_FIXTURE
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    payload = load_tson(fixture_path)
    upsert_master_data(payload)


if __name__ == "__main__":
    main()
