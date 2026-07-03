# inspection_system

ระบบ Django + PostgreSQL สำหรับบันทึกและติดตามงานตรวจสอบคุณภาพในสายการผลิต โดยฐานข้อมูลแบ่งเป็น 2 ส่วนหลัก:

- Master Data: ไลน์ผลิต, ประเภท defect, เงื่อนไขทดสอบ, inspector, result type
- Transaction Data: test session, test round, inspection record, defect record, verification record

## Prompt DB ทั้งหมด

ใช้ prompt นี้เมื่อต้องการให้ AI ช่วยสร้าง, ตรวจ, อธิบาย, หรือปรับปรุงฐานข้อมูลของโปรเจกต์นี้

```text
คุณคือ senior database engineer ช่วยออกแบบฐานข้อมูล PostgreSQL สำหรับระบบ inspection_system ซึ่งเป็นระบบตรวจสอบคุณภาพในสายการผลิต สร้าง schema ให้รองรับ Django 5 และใช้ convention ของ Django table name ตาม app label `inspection`

เป้าหมายของระบบ:
1. เก็บ master data ที่ผู้ใช้จัดการได้ ได้แก่ production line, defect type, test condition, inspector และ inspection result type
2. สร้าง inspection session สำหรับการทดสอบแต่ละครั้ง โดยมีเลข session อัตโนมัติรูปแบบ TSYYYYMMDD-0001
3. ใน 1 session เลือก defect ที่ต้องการทดสอบได้หลายรายการ และแต่ละ defect กำหนดจำนวนรอบทดสอบได้
4. แต่ละรอบทดสอบบันทึกผลเป็น Found หรือ Not Found พร้อม comment ได้
5. ถ้า Not Found ครบ 4 ครั้ง ให้ test นั้นจบอัตโนมัติ
6. ถ้า test ทุกตัวใน session จบแล้ว ให้ session เป็น completed
7. เก็บข้อมูล inspection record แบบ legacy/production record ได้ พร้อมจำนวน defect แยกเป็น machine และ PQC
8. รองรับ dashboard สำหรับ filter ตาม line, condition, date range, result และ defect distribution

ฐานข้อมูลต้องมีตารางดังนี้:

1. inspection_productionline
   - เก็บไลน์ผลิต
   - fields: id, name, description, is_active, created_at
   - name unique
   - is_active มี index

2. inspection_defecttype
   - เก็บประเภทของเสีย/defect
   - fields: id, name, description, is_active, created_at
   - name unique
   - is_active มี index

3. inspection_testcondition
   - เก็บเงื่อนไขหรือประเภทการทดสอบ
   - fields: id, name, description, is_active, created_at
   - name unique
   - is_active มี index

4. inspection_inspector
   - เก็บชื่อผู้ทดสอบ
   - fields: id, name, description, is_active, created_at
   - name unique
   - is_active มี index

5. inspection_inspectionresulttype
   - เก็บผลลัพธ์ของรอบทดสอบ เช่น Found, Not Found
   - fields: id, name, description, is_active, created_at
   - name unique
   - is_active มี index

6. inspection_inspectionsession
   - เก็บหัวรายการทดสอบ
   - fields: id, session_number, inspection_date, line_id, test_condition_id, inspector_id, overall_comment, status, created_at
   - session_number unique และมี index
   - status มีค่า draft, in_progress, completed, cancelled
   - line_id FK ไป inspection_productionline แบบ PROTECT/RESTRICT
   - test_condition_id FK ไป inspection_testcondition แบบ PROTECT/RESTRICT
   - inspector_id FK ไป inspection_inspector แบบ PROTECT/RESTRICT
   - index: inspection_date + line_id, test_condition_id + inspection_date, inspector_id + inspection_date, status + inspection_date

7. inspection_inspectiontest
   - เก็บ defect ที่ถูกเลือกทดสอบภายใต้ session
   - fields: id, session_id, defect_type_id, test_name, total_rounds, completed_rounds, status, stop_reason, created_at
   - session_id FK ไป inspection_inspectionsession แบบ CASCADE
   - defect_type_id FK ไป inspection_defecttype แบบ PROTECT/RESTRICT และ nullable
   - status มีค่า in_progress, finished
   - unique: session_id + defect_type_id
   - index: session_id + defect_type_id, defect_type_id, status

8. inspection_inspectionround
   - เก็บผลแต่ละรอบของ inspection test
   - fields: id, inspection_test_id, round_number, result_type_id, comment, created_at
   - inspection_test_id FK ไป inspection_inspectiontest แบบ CASCADE
   - result_type_id FK ไป inspection_inspectionresulttype แบบ PROTECT/RESTRICT และ nullable
   - unique: inspection_test_id + round_number
   - index: inspection_test_id + round_number, result_type_id

9. inspection_inspectionrecord
   - เก็บข้อมูล inspection record แบบ production/legacy
   - fields: id, inspection_date, inspection_time, initial_control, verify, sd_code, part_name, line_id, test_condition_id, total_production, result, machine_ng, machine_ok, pqc_ng, pqc_ok, kanban_mismatch_count, bush_vertical_defect_count, spatter_count, forgotten_bush_vertical_count, not_enter_bush_vertical_count, bush_vertical_misaligned_count, stopper_leak_count, round_recline_leak_count, notes, created_at
   - result มีค่า ok, ng, pending
   - line_id FK ไป inspection_productionline แบบ PROTECT/RESTRICT
   - test_condition_id FK ไป inspection_testcondition แบบ PROTECT/RESTRICT
   - index: inspection_date + line_id, line_id + inspection_date + inspection_time, test_condition_id + inspection_date, sd_code + inspection_date, result + inspection_date

10. inspection_inspectiondefect
    - เก็บ defect ที่พบใน inspection record
    - fields: id, inspection_id, test_condition_id, defect_type_id, machine_quantity, pqc_quantity, quantity, created_at
    - inspection_id FK ไป inspection_inspectionrecord แบบ CASCADE
    - test_condition_id FK ไป inspection_testcondition แบบ PROTECT/RESTRICT
    - defect_type_id FK ไป inspection_defecttype แบบ PROTECT/RESTRICT
    - unique: inspection_id + test_condition_id + defect_type_id
    - index: inspection_id + test_condition_id, defect_type_id + test_condition_id, test_condition_id + defect_type_id

11. inspection_verificationrecord
    - เก็บผล verification แบบเก่า
    - fields: id, inspection_date, defect_type_id, test_condition_id, result, round_no, found_count, not_found_count, comment, created_at
    - result มีค่า found, not_found, pending
    - defect_type_id FK ไป inspection_defecttype แบบ PROTECT/RESTRICT
    - test_condition_id FK ไป inspection_testcondition แบบ PROTECT/RESTRICT
    - index: inspection_date + defect_type_id, test_condition_id + inspection_date, result + inspection_date

ข้อกำหนดเพิ่มเติม:
- ใช้ BigAutoField เป็น primary key ทุกตาราง
- ใช้ timestamp with time zone สำหรับ created_at
- ใช้ integer ที่ไม่ติดลบสำหรับจำนวน เช่น total_rounds, completed_rounds, quantity ต่าง ๆ
- ใช้ ON DELETE CASCADE เฉพาะข้อมูลลูกที่ควรถูกลบตามแม่ เช่น inspection_test, inspection_round, inspection_defect
- ใช้ ON DELETE RESTRICT/PROTECT กับ master data เพื่อป้องกันการลบข้อมูลอ้างอิงที่ถูกใช้งานแล้ว
- เพิ่ม index ให้ field ที่ใช้ filter บ่อย เช่น date, line, condition, status, result, sd_code
- ออกแบบให้ query dashboard รวม defect distribution และ filter ตาม date/line/condition ได้เร็ว
```

## Database Schema

### Master Data

| Table | Purpose | Important Fields |
| --- | --- | --- |
| `inspection_productionline` | ไลน์ผลิต | `name`, `description`, `is_active`, `created_at` |
| `inspection_defecttype` | ประเภท defect | `name`, `description`, `is_active`, `created_at` |
| `inspection_testcondition` | เงื่อนไข/ประเภทการทดสอบ | `name`, `description`, `is_active`, `created_at` |
| `inspection_inspector` | ผู้ทดสอบ | `name`, `description`, `is_active`, `created_at` |
| `inspection_inspectionresulttype` | ผลของรอบทดสอบ | `name`, `description`, `is_active`, `created_at` |

ทุก master table ใช้ field ชุดเดียวกัน:

- `id`: primary key แบบ BigAutoField
- `name`: ชื่อข้อมูล, unique, ความยาวสูงสุด 100
- `description`: รายละเอียดเพิ่มเติม
- `is_active`: ใช้เปิด/ปิดไม่ให้เลือกในหน้าฟอร์ม
- `created_at`: วันที่สร้างข้อมูล

### Test Session Flow

| Table | Purpose |
| --- | --- |
| `inspection_inspectionsession` | หัว session การทดสอบ |
| `inspection_inspectiontest` | defect แต่ละตัวที่ถูกเลือกใน session |
| `inspection_inspectionround` | ผลแต่ละรอบของ defect นั้น |

Relationship:

```text
ProductionLine 1 ---- N InspectionSession
TestCondition 1 ---- N InspectionSession
Inspector      1 ---- N InspectionSession

InspectionSession 1 ---- N InspectionTest
DefectType        1 ---- N InspectionTest

InspectionTest       1 ---- N InspectionRound
InspectionResultType 1 ---- N InspectionRound
```

Business rules:

- `InspectionSession.session_number` ต้อง unique และใช้รูปแบบ `TSYYYYMMDD-0001`
- `InspectionSession.status` ใช้ค่า `draft`, `in_progress`, `completed`, `cancelled`
- ใน 1 session มี `InspectionTest` ต่อ defect ได้เพียง 1 รายการ ด้วย unique constraint `session + defect_type`
- `InspectionTest.status` ใช้ค่า `in_progress`, `finished`
- `InspectionRound.round_number` ห้ามซ้ำใน test เดียวกัน
- ถ้า `Not Found` ครบ 4 ครั้ง ให้ `InspectionTest.status = finished` และบันทึก `stop_reason`
- ถ้าทุก test ใน session เป็น `finished` ให้ session เป็น `completed`

### Inspection Record Flow

| Table | Purpose |
| --- | --- |
| `inspection_inspectionrecord` | บันทึก production inspection แบบรวม |
| `inspection_inspectiondefect` | defect detail ที่พบใน record |

Relationship:

```text
ProductionLine 1 ---- N InspectionRecord
TestCondition 1 ---- N InspectionRecord

InspectionRecord 1 ---- N InspectionDefect
TestCondition    1 ---- N InspectionDefect
DefectType       1 ---- N InspectionDefect
```

Business rules:

- `InspectionRecord.result` ใช้ค่า `ok`, `ng`, `pending`
- defect quantity แยกเป็น `machine_quantity` และ `pqc_quantity`
- `quantity` คือผลรวมของ machine + PQC หรือใช้รองรับข้อมูลเดิม
- ใน 1 inspection record ห้ามมี defect ซ้ำใน condition เดียวกัน ด้วย unique constraint `inspection + test_condition + defect_type`

### Verification Record

`inspection_verificationrecord` เป็น flow เก่าที่เก็บผลตรวจซ้ำแบบ found/not_found/pending ปัจจุบัน view redirect ไปใช้ Test Session เป็นหลัก แต่ table ยังอยู่เพื่อรองรับข้อมูลเดิม

## PostgreSQL DDL Reference

> หมายเหตุ: ในโปรเจกต์จริงควรใช้ Django migration เป็นแหล่งความจริง คำสั่ง SQL ด้านล่างเป็น reference สำหรับอธิบายโครงสร้างฐานข้อมูล

```sql
CREATE TABLE inspection_productionline (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inspection_defecttype (LIKE inspection_productionline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES);
CREATE TABLE inspection_testcondition (LIKE inspection_productionline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES);
CREATE TABLE inspection_inspector (LIKE inspection_productionline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES);
CREATE TABLE inspection_inspectionresulttype (LIKE inspection_productionline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES);

CREATE INDEX inspection_productionline_is_active_idx ON inspection_productionline (is_active);
CREATE INDEX inspection_defecttype_is_active_idx ON inspection_defecttype (is_active);
CREATE INDEX inspection_testcondition_is_active_idx ON inspection_testcondition (is_active);
CREATE INDEX inspection_inspector_is_active_idx ON inspection_inspector (is_active);
CREATE INDEX inspection_inspectionresulttype_is_active_idx ON inspection_inspectionresulttype (is_active);

CREATE TABLE inspection_inspectionsession (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    session_number VARCHAR(50) NOT NULL UNIQUE,
    inspection_date DATE NOT NULL DEFAULT CURRENT_DATE,
    line_id BIGINT NOT NULL REFERENCES inspection_productionline (id) ON DELETE RESTRICT,
    test_condition_id BIGINT NOT NULL REFERENCES inspection_testcondition (id) ON DELETE RESTRICT,
    inspector_id BIGINT NOT NULL REFERENCES inspection_inspector (id) ON DELETE RESTRICT,
    overall_comment TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX inspection_inspectionsession_session_number_idx ON inspection_inspectionsession (session_number);
CREATE INDEX inspection_inspectionsession_inspection_date_idx ON inspection_inspectionsession (inspection_date);
CREATE INDEX inspection_inspectionsession_status_idx ON inspection_inspectionsession (status);
CREATE INDEX session_date_line_idx ON inspection_inspectionsession (inspection_date, line_id);
CREATE INDEX session_cond_date_idx ON inspection_inspectionsession (test_condition_id, inspection_date);
CREATE INDEX session_insp_date_idx ON inspection_inspectionsession (inspector_id, inspection_date);
CREATE INDEX session_status_date_idx ON inspection_inspectionsession (status, inspection_date);

CREATE TABLE inspection_inspectiontest (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES inspection_inspectionsession (id) ON DELETE CASCADE,
    defect_type_id BIGINT NULL REFERENCES inspection_defecttype (id) ON DELETE RESTRICT,
    test_name VARCHAR(150) NOT NULL DEFAULT '',
    total_rounds INTEGER NOT NULL DEFAULT 1 CHECK (total_rounds >= 0),
    completed_rounds INTEGER NOT NULL DEFAULT 0 CHECK (completed_rounds >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'finished')),
    stop_reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniq_session_defect_test UNIQUE (session_id, defect_type_id)
);

CREATE INDEX test_session_defect_idx ON inspection_inspectiontest (session_id, defect_type_id);
CREATE INDEX test_defect_idx ON inspection_inspectiontest (defect_type_id);
CREATE INDEX test_status_idx ON inspection_inspectiontest (status);

CREATE TABLE inspection_inspectionround (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    inspection_test_id BIGINT NOT NULL REFERENCES inspection_inspectiontest (id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL CHECK (round_number >= 0),
    result_type_id BIGINT NULL REFERENCES inspection_inspectionresulttype (id) ON DELETE RESTRICT,
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniq_test_round_number UNIQUE (inspection_test_id, round_number)
);

CREATE INDEX round_test_number_idx ON inspection_inspectionround (inspection_test_id, round_number);
CREATE INDEX round_result_type_idx ON inspection_inspectionround (result_type_id);

CREATE TABLE inspection_inspectionrecord (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    inspection_date DATE NOT NULL DEFAULT CURRENT_DATE,
    inspection_time TIME NOT NULL DEFAULT '08:00:00',
    initial_control BOOLEAN NOT NULL DEFAULT FALSE,
    verify BOOLEAN NOT NULL DEFAULT FALSE,
    sd_code VARCHAR(100) NOT NULL DEFAULT '',
    part_name VARCHAR(200) NOT NULL DEFAULT '',
    line_id BIGINT NOT NULL REFERENCES inspection_productionline (id) ON DELETE RESTRICT,
    test_condition_id BIGINT NOT NULL REFERENCES inspection_testcondition (id) ON DELETE RESTRICT,
    total_production INTEGER NOT NULL DEFAULT 0 CHECK (total_production >= 0),
    result VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (result IN ('ok', 'ng', 'pending')),
    machine_ng INTEGER NOT NULL DEFAULT 0 CHECK (machine_ng >= 0),
    machine_ok INTEGER NOT NULL DEFAULT 0 CHECK (machine_ok >= 0),
    pqc_ng INTEGER NOT NULL DEFAULT 0 CHECK (pqc_ng >= 0),
    pqc_ok INTEGER NOT NULL DEFAULT 0 CHECK (pqc_ok >= 0),
    kanban_mismatch_count INTEGER NOT NULL DEFAULT 0 CHECK (kanban_mismatch_count >= 0),
    bush_vertical_defect_count INTEGER NOT NULL DEFAULT 0 CHECK (bush_vertical_defect_count >= 0),
    spatter_count INTEGER NOT NULL DEFAULT 0 CHECK (spatter_count >= 0),
    forgotten_bush_vertical_count INTEGER NOT NULL DEFAULT 0 CHECK (forgotten_bush_vertical_count >= 0),
    not_enter_bush_vertical_count INTEGER NOT NULL DEFAULT 0 CHECK (not_enter_bush_vertical_count >= 0),
    bush_vertical_misaligned_count INTEGER NOT NULL DEFAULT 0 CHECK (bush_vertical_misaligned_count >= 0),
    stopper_leak_count INTEGER NOT NULL DEFAULT 0 CHECK (stopper_leak_count >= 0),
    round_recline_leak_count INTEGER NOT NULL DEFAULT 0 CHECK (round_recline_leak_count >= 0),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX inspection_inspectionrecord_inspection_date_idx ON inspection_inspectionrecord (inspection_date);
CREATE INDEX inspection_inspectionrecord_initial_control_idx ON inspection_inspectionrecord (initial_control);
CREATE INDEX inspection_inspectionrecord_verify_idx ON inspection_inspectionrecord (verify);
CREATE INDEX inspection_inspectionrecord_sd_code_idx ON inspection_inspectionrecord (sd_code);
CREATE INDEX inspection_inspectionrecord_result_idx ON inspection_inspectionrecord (result);
CREATE INDEX insp_date_line_idx ON inspection_inspectionrecord (inspection_date, line_id);
CREATE INDEX insp_line_date_time_idx ON inspection_inspectionrecord (line_id, inspection_date, inspection_time);
CREATE INDEX insp_cond_date_idx ON inspection_inspectionrecord (test_condition_id, inspection_date);
CREATE INDEX insp_sd_code_date_idx ON inspection_inspectionrecord (sd_code, inspection_date);
CREATE INDEX insp_result_date_idx ON inspection_inspectionrecord (result, inspection_date);

CREATE TABLE inspection_inspectiondefect (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    inspection_id BIGINT NOT NULL REFERENCES inspection_inspectionrecord (id) ON DELETE CASCADE,
    test_condition_id BIGINT NOT NULL REFERENCES inspection_testcondition (id) ON DELETE RESTRICT,
    defect_type_id BIGINT NOT NULL REFERENCES inspection_defecttype (id) ON DELETE RESTRICT,
    machine_quantity INTEGER NOT NULL DEFAULT 0 CHECK (machine_quantity >= 0),
    pqc_quantity INTEGER NOT NULL DEFAULT 0 CHECK (pqc_quantity >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniq_inspection_defect_condition_type UNIQUE (inspection_id, test_condition_id, defect_type_id)
);

CREATE INDEX inspdef_inspection_cond_idx ON inspection_inspectiondefect (inspection_id, test_condition_id);
CREATE INDEX inspdef_type_cond_idx ON inspection_inspectiondefect (defect_type_id, test_condition_id);
CREATE INDEX inspdef_cond_type_idx ON inspection_inspectiondefect (test_condition_id, defect_type_id);

CREATE TABLE inspection_verificationrecord (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    inspection_date DATE NOT NULL DEFAULT CURRENT_DATE,
    defect_type_id BIGINT NOT NULL REFERENCES inspection_defecttype (id) ON DELETE RESTRICT,
    test_condition_id BIGINT NOT NULL REFERENCES inspection_testcondition (id) ON DELETE RESTRICT,
    result VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (result IN ('found', 'not_found', 'pending')),
    round_no INTEGER NOT NULL DEFAULT 1 CHECK (round_no >= 0),
    found_count INTEGER NOT NULL DEFAULT 0 CHECK (found_count >= 0),
    not_found_count INTEGER NOT NULL DEFAULT 0 CHECK (not_found_count >= 0),
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX inspection_verificationrecord_inspection_date_idx ON inspection_verificationrecord (inspection_date);
CREATE INDEX inspection_verificationrecord_result_idx ON inspection_verificationrecord (result);
CREATE INDEX verify_date_defect_idx ON inspection_verificationrecord (inspection_date, defect_type_id);
CREATE INDEX verify_cond_date_idx ON inspection_verificationrecord (test_condition_id, inspection_date);
CREATE INDEX verify_result_date_idx ON inspection_verificationrecord (result, inspection_date);
```

## Environment Variables

Django อ่านค่า database จาก environment variables เหล่านี้:

| Variable | Default |
| --- | --- |
| `POSTGRES_DB` | `inspection_system` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |


## Prompt การเชื่อมต่อ DB

ใช้ prompt นี้เมื่อต้องการให้ AI ช่วยตั้งค่า, ตรวจสอบ, หรือแก้ปัญหาการเชื่อมต่อ PostgreSQL ของโปรเจกต์นี้

```text
คุณคือ senior Django/PostgreSQL engineer ช่วยตั้งค่าการเชื่อมต่อฐานข้อมูลให้โปรเจกต์ Django ชื่อ inspection_system

บริบทโปรเจกต์:
- Framework: Django 5
- Database: PostgreSQL
- Settings module: config/settings.py
- ใช้ database backend: django.db.backends.postgresql
- App หลัก: apps.inspection
- Time zone: Asia/Bangkok
- Default primary key: django.db.models.BigAutoField

ค่าการเชื่อมต่อฐานข้อมูลต้องอ่านจาก environment variables และมีค่า default สำหรับเครื่อง development ดังนี้:
- POSTGRES_DB default เป็น inspection_system
- POSTGRES_USER default เป็น postgres
- POSTGRES_PASSWORD default เป็น postgres
- POSTGRES_HOST default เป็น localhost
- POSTGRES_PORT default เป็น 5432

ต้องเขียน DATABASES ใน config/settings.py รูปแบบนี้:

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "inspection_system"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

ช่วยตรวจสอบให้ครบ:
1. import os แล้วหรือยัง
2. ติดตั้ง driver PostgreSQL สำหรับ Django แล้วหรือยัง เช่น psycopg2-binary หรือ psycopg
3. PostgreSQL service เปิดอยู่หรือไม่
4. database ชื่อ inspection_system มีอยู่หรือไม่
5. user/password ถูกต้องหรือไม่
6. host/port เชื่อมต่อได้หรือไม่
7. หลังแก้ config ให้รัน python manage.py check และ python manage.py migrate

ถ้าต้องสร้าง database ใน PostgreSQL ให้ใช้คำสั่งตัวอย่าง:
CREATE DATABASE inspection_system;

ถ้าต้องตั้งค่าใน PowerShell สำหรับ development ให้ใช้:
$env:POSTGRES_DB="inspection_system"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="postgres"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"

ถ้าต้องตั้งค่าใน .env ให้ใช้:
POSTGRES_DB=inspection_system
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

โปรดอธิบายขั้นตอนแบบสั้น ชัดเจน และให้คำสั่งที่รันได้บน Windows PowerShell
```

## ตัวอย่าง DATABASES ใน Django

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "inspection_system"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
```

## คำสั่งตรวจสอบการเชื่อมต่อ DB

```powershell
python manage.py check
python manage.py migrate
```

## Django Commands

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Seed Data แนะนำ

ควรมี master data เริ่มต้นอย่างน้อย:

```sql
INSERT INTO inspection_inspectionresulttype (name, description, is_active, created_at)
VALUES
    ('Found', 'Defect was detected during the test round.', TRUE, CURRENT_TIMESTAMP),
    ('Not Found', 'Defect was not detected during the test round.', TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;
```

