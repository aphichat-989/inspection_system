# Deployment Package Guide

เอกสารนี้ใช้สำหรับเตรียม `inspection_system/` เป็น clean package ก่อนย้ายขึ้น Production Server เพื่อ build และ run ด้วย Docker Production

> สถานะการตรวจรอบนี้: วิเคราะห์ไฟล์และสร้างคู่มือเท่านั้น ยังไม่ได้ลบไฟล์, build image, run container, migrate, restart container, commit หรือ push

## Required production package

หลัง cleanup แล้ว package ควรมีโครงสร้างหลักดังนี้:

```text
inspection_system/
├── apps/
├── config/
├── core/
├── templates/
├── static/                  # ถ้ามี static รวมระดับ project
├── requirements.txt
├── Dockerfile
├── entrypoint.sh
├── docker-compose.production.yml
├── .env.production.example
├── scripts/
└── README.md
```

หมายเหตุจาก workspace ปัจจุบัน:

- `docker-compose.production.yml` มีอยู่แล้ว และเป็นไฟล์ compose สำหรับ production
- `.env.production.example` มีอยู่แล้ว และเป็น template สำหรับสร้าง `.env.production` บน server
- `scripts/` มีอยู่แล้วสำหรับงาน backup/restore PostgreSQL
  - `scripts/backup_postgres.sh`
  - `scripts/restore_postgres.sh`
- `.gitignore` และ `.dockerignore` ต้อง ignore `.env.*` แต่ยกเว้น `.env.example` และ `.env.production.example` เพื่อให้ track template ได้ โดยยังไม่ track `.env.production` จริง

## A. ต้องเก็บไว้สำหรับ Production

- `apps/` source code ของ Django app
- `apps/inspection/migrations/` migrations ทั้งหมด ห้ามลบ
- `apps/inspection/templates/` templates ของ app
- `apps/inspection/static/` CSS/JS ที่ collectstatic ต้องใช้
- `config/` Django settings, URLs, ASGI/WSGI
- `templates/registration/login.html`
- `manage.py`
- `requirements.txt`
- `Dockerfile`
- `entrypoint.sh`
- `docker-compose.production.yml` ต้องมีใน package production
- `.env.production.example` ต้องมีเป็นตัวอย่าง config แต่ห้ามใส่ secret จริง
- `README.md`
- `scripts/` ถ้ามี backup/restore scripts ที่ใช้จริงบน server

## B. ควรเก็บไว้หรือควรตรวจสอบก่อนตัดสินใจ

- `core/fixtnres/Fixtnre.tson` เป็น data file ขนาดเล็ก ไม่พบการอ้างจาก source code ในรอบตรวจนี้ แต่ถ้าเป็น fixture/master data ให้เก็บไว้
- `data_load.py` และ `data_dnmp.py` เป็นสคริปต์โหลดข้อมูล/utility ควรตรวจว่าจำเป็นตอน bootstrap production หรือไม่
- `install.sh`, `setup.bat`, `start.bat`, `stop.bat`, `reset.bat`, `update.bat` เป็นสคริปต์ช่วยงาน dev/ops ควรเก็บเฉพาะที่ใช้จริงบน server
- `docker-compose.yml` เป็น compose สำหรับ dev/local ควรแยกจาก production package หรือเก็บไว้เฉพาะถ้าต้องใช้ reference
- `SYSTEM_BLUEPRINT.md` เป็นเอกสารระบบ เก็บได้ แต่ไม่จำเป็นต่อ runtime
- `.env.example` เก็บได้สำหรับ dev reference แต่ production package ควรใช้ `.env.production.example`
- `.dockerignore`, `.gitignore`, `.gitattributes` เก็บได้เพื่อคุม package/build context

## C. ไม่เกี่ยวข้องกับ Production ลบได้หลังอนุมัติ

รายการที่เสนอให้ลบ/ไม่รวมใน production package:

- `.kilo/` เครื่องมือ/agent workspace และ `node_modules` ภายใน ไม่เกี่ยวกับ runtime Django production
- `apps/__pycache__/`
- `apps/inspection/__pycache__/`
- `apps/inspection/services/__pycache__/`
- `apps/inspection/services/analytics/__pycache__/`
- `apps/inspection/services/dashboard/__pycache__/`
- `apps/inspection/services/inspection/__pycache__/`
- `apps/inspection/services/production/__pycache__/`
- `config/__pycache__/`
- ไฟล์ `*.pyc`, `*.pyo`, `*.pyd`
- `.pytest_cache/`, `.coverage`, `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`, `.tox/`, `.nox/`
- `.DS_Store`, `Thumbs.db`
- `*.log`, `*.tmp`, `*.bak`
- `.vscode/`, `.idea/`
- `.env` ห้ามนำเข้า package เพราะเป็น secret/local runtime file
- `actual_inspection_export.xlsx` ไม่พบการอ้างจาก source code และควรแยกเก็บเป็น export/backup เว้นแต่ยืนยันว่าใช้เป็น seed data จริง

## D. ห้ามลบ

- `apps/inspection/migrations/`
- `requirements.txt`
- `Dockerfile`
- `entrypoint.sh`
- `docker-compose.production.yml`
- `.env.production.example`
- `scripts/` ถ้าเป็น backup/restore scripts ที่ใช้จริง
- source code ใน `apps/`, `config/`, `core/`
- templates และ static ที่ใช้งานจริง
- database fixtures หรือ master data ที่ระบบต้องใช้
- `README.md`

## Large and data files review

ไฟล์ data/export ที่พบใน project หลัก (ไม่นับ `.git/` และ `.kilo/`):

| File | Size | Recommendation |
| --- | ---: | --- |
| `actual_inspection_export.xlsx` | ~6.5 KB | ย้ายไป backup/export แยก หรือไม่รวม production package เว้นแต่ใช้ seed data |
| `core/fixtnres/Fixtnre.tson` | ~2.2 KB | เก็บไว้ถ้าเป็น fixture/master data; ตรวจสอบ business owner ก่อนลบ |

ไฟล์ใหญ่ส่วนใหญ่ที่พบอยู่ใต้ `.kilo/node_modules/` ซึ่งไม่ควรอยู่ใน production package

## Production behavior notes

- `entrypoint.sh` จะรอ PostgreSQL แล้วรัน `python manage.py check --deploy`, `python manage.py migrate --noinput`, และ `python manage.py collectstatic --noinput` ตอน container start
- รอบ audit นี้ไม่ได้รันคำสั่งเหล่านั้นตามข้อห้าม
- Production server ต้องสร้าง `.env.production` จาก `.env.production.example` และใส่ secret จริงบน server เท่านั้น
- ไม่ควร copy `.env`, `media/`, `staticfiles/`, dump, export หรือ backup เข้า image build context เว้นแต่ตั้งใจใช้จริง

## Pre-delete approval list

ยังไม่ได้ลบไฟล์ใด ๆ

เสนอให้ลบหลังได้รับอนุมัติ:

```text
DELETE:
- .kilo/
- apps/__pycache__/
- apps/inspection/__pycache__/
- apps/inspection/services/__pycache__/
- apps/inspection/services/analytics/__pycache__/
- apps/inspection/services/dashboard/__pycache__/
- apps/inspection/services/inspection/__pycache__/
- apps/inspection/services/production/__pycache__/
- config/__pycache__/
- actual_inspection_export.xlsx
```

เสนอให้เก็บ:

```text
KEEP:
- apps/
- config/
- core/
- templates/
- apps/inspection/migrations/
- apps/inspection/static/
- apps/inspection/templates/
- requirements.txt
- Dockerfile
- entrypoint.sh
- README.md
- .dockerignore
- .gitignore
- .gitattributes
- core/fixtnres/Fixtnre.tson
```

ต้องคืน/ต้องมีใน package ก่อน deploy:

```text
REQUIRED PRESENT:
- docker-compose.production.yml
- .env.production.example
- scripts/
  - backup_postgres.sh
  - restore_postgres.sh
```
