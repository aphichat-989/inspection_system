# คู่มือโครงสร้างระบบ inspection_system (System Blueprint)

เอกสารนี้สรุปโครงสร้างระบบ **inspection_system** ทั้งหมด — ตั้งแต่ Model, URL, View, Business Logic, ระบบแปลภาษา (i18n), **ระบบสี/ธีม (Color System)**, ไฟล์ Static, ไปจนถึงวิธีติดตั้ง deploy ด้วย Docker / Linux / Windows — เพื่อให้ใครก็สามารถก๊อปปี้สร้างระบบนี้ได้ **100%**

> เหมาะสำหรับ: คนที่จะเอาโค้ดไปทำต่อ, ทำ Fork, หรือสร้างระบบใหม่ในรูปแบบเดียวกันทั้งหมด

---

## 1. ภาพรวม (Overview)

ระบบตวจสอบคุณภาพ (QA Inspection) สำหรับสายการผลิต แบบ Smart Factory

- **Framework:** Django 5.0 (Python 3.12)
- **Database:** PostgreSQL 16
- **Frontend:** Bootstrap 5.3.3 + Bootstrap Icons 1.11.1 + Google Font (Sarabun) + CSS ของโปรเจกต์เอง
- **WSGI Server:** Gunicorn (+ WhiteNoise สำหรับ static)
- **Deploy:** Docker Compose (Windows one-click) / Linux systemd + Nginx
- **ภาษา UI:** ไทย (ค่าเริ่มต้น) + อังกฤษ (สลับได้ทันที ไม่ต้อง reload)

ฟีเจอร์หลัก:
1. **Dashboard** — KPI + ตารางรอบทดสอบล่าสุด
2. **Test Sessions** — สร้างรอบทดสอบ เลือก defect กำหนดรอบ ทดสอบ (Found / Not Found) และสรุปผล
3. **Master Data** — ไลน์ผลิต, Inspector, Defect Type, Test Condition (CRUD)
4. **Users** — จัดการผู้ใช้ (เฉพาะ staff)
5. **Verification** — โฟลว์เก่า (legacy) เก็บผล found/not_found
6. **Export Excel** — ส่งออกรายการ session และรายงานรอบ (openpyxl)

---

## 2. Tech Stack & Dependencies

`requirements.txt` (เวอร์ชันล็อคช่วง):
```
Django>=5.0,<5.1
python-dotenv>=1.0,<2.0
gunicorn>=22.0,<23.0
psycopg2-binary>=2.9,<3.0
whitenoise>=6.6,<7.0
openpyxl>=3.1.2,<4.0
```

CDN ภายนอก (โหลดใน `<head>` ทุกหน้า):
- Bootstrap CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css`
- Bootstrap Icons: `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css`
- Font Sarabun: `https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&display=swap`
- Bootstrap JS (ท้าย `<body>`): `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js`

---

## 3. โครงสร้างโฟลเดอร์ (Directory Tree)

```
inspection_system/
├── apps/
│   └── inspection/
│       ├── __init__.py
│       ├── admin.py                 # Django admin registers
│       ├── apps.py                  # AppConfig: apps.inspection
│       ├── forms.py                 # TestSessionForm, VerificationRecordForm, master forms
│       ├── forms_auth.py            # BootstrapAuthenticationForm
│       ├── forms_users.py           # UserAdminForm (สร้าง/แก้ user + รหัสผ่าน)
│       ├── i18n.py                  # Dictionary แปล TH/EN + context processor
│       ├── models.py                # โมเดลทั้งหมด (ดูหัวข้อ 4)
│       ├── urls.py                  # routing ของ app
│       ├── views.py                 # re-export views ทั้งหมด
│       ├── views_dashboard.py       # DashboardView
│       ├── views_sessions.py        # Session CRUD, Detail, Export Excel, Bulk Delete
│       ├── views_master_data.py     # Master Data CRUD (ProductionLine/Inspector/DefectType/TestCondition)
│       ├── views_users.py           # User CRUD
│       ├── views_verification.py    # Verification CRUD
│       ├── views_helpers.py         # Business rules (ดูหัวข้อ 5)
│       ├── views_language.py        # set_language view
│       ├── migrations/              # Django migrations (0011 files)
│       ├── services/
│       │   ├── __init__.py          # export ProductionLineService
│       │   ├── analytics/defect_service.py   # สรุป defect distribution
│       │   ├── dashboard/service.py            # DashboardService (cached)
│       │   ├── inspection/service.py          # InspectionRead/WriteService
│       │   └── production/line_service.py     # ProductionLineService
│       ├── static/inspection/
│       │   ├── css/  base.css auth.css dashboard.css form.css list.css detail.css master_data_form.css
│       │   └── js/   base.js dashboard.js form.js detail.js list.js
│       └── templates/inspection/
│           ├── base.html            # Layout หลัก (sidebar + topbar)
│           ├── dashboard.html
│           ├── list.html
│           ├── form.html
│           ├── detail.html
│           ├── confirm_delete.html
│           ├── master_data_list.html
│           ├── master_data_form.html
│           ├── master_data_confirm_delete.html
│           ├── user_list.html
│           ├── user_form.html
│           ├── user_confirm_delete.html
│           ├── verification_list.html
│           ├── verification_form.html
│           └── verification_confirm_delete.html
├── config/
│   ├── __init__.py
│   ├── settings.py         # ตั้งค่า Django (env-driven)
│   ├── urls.py             # root urls + healthz + login/logout
│   ├── wsgi.py
│   └── asgi.py
├── templates/
│   └── registration/login.html      # หน้า Login
├── core/fixtnres/Fixtnre.tson       # (asset file)
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh                    # รอ DB + migrate + collectstatic
├── install.sh                       # ติดตั้ง Linux (systemd + nginx)
├── .env.example                     # ตัวอย่าง env
├── .env                             # (ถูกสร้างโดย setup)
├── README.md
├── data_load.py                     # สคริปต์โหลดข้อมูล
├── data_dnmp.py                     # สคริปต์ dump
├── setup.bat  start.bat  stop.bat  update.bat  reset.bat   # Windows one-click
├── .gitignore  .gitattributes  .dockerignore
└── actual_inspection_export.xlsx
```

> **หมายเหตุ services:** `services/` (dashboard/inspection/analytics/production) เป็นชุด service สำหรับ "InspectionRecord dashboard" (legacy) — ปัจจุบัน view หลัก (`views_dashboard.py`, `views_sessions.py`) ยัง **ไม่ได้เรียกใช้** ชุด service นี้โดยตรง แต่โค้ดยังอยู่ครบเพื่อใช้ต่อยอด/ทำ dashboard แบบ record-based.

---

## 4. Data Model (`apps/inspection/models.py`)

### 4.1 Master Data (ใช้ `BaseMasterModel` เหมือนกันทุกตัว)
มี field ชุดเดียวกัน: `id` (BigAutoField), `name` (unique, ≤100), `description` (text), `is_active` (bool, มี index), `created_at`.

| Model | ตาราง | หน้าที่ |
| --- | --- | --- |
| `ProductionLine` | `inspection_productionline` | ไลน์ผลิต |
| `DefectType` | `inspection_defecttype` | ประเภทของเสีย |
| `TestCondition` | `inspection_testcondition` | เงื่อนไข/ประเภทการทดสอบ |
| `Inspector` | `inspection_inspector` | ผู้ทดสอบ |
| `InspectionResultType` | `inspection_inspectionresulttype` | ผลรอบ (Found / Not Found) |

### 4.2 Test Session Flow
- `InspectionSession` (`inspection_inspectionsession`) — หัว session
  - `session_number` (unique), `inspection_date`, `line` (FK→ProductionLine, PROTECT), `test_condition` (FK→TestCondition, PROTECT), `inspector` (FK→Inspector, PROTECT), `overall_comment`, `status`, `created_at`
  - `STATUS_CHOICES = draft, in_progress, completed, cancelled`
- `InspectionTest` (`inspection_inspectiontest`) — defect แต่ละตัวใน session
  - `session` (FK CASCADE), `defect_type` (FK PROTECT, nullable), `test_name`, `total_rounds`, `completed_rounds`, `status` (in_progress/finished), `stop_reason`
  - unique: `(session, defect_type)`
- `InspectionRound` (`inspection_inspectionround`) — ผลแต่ละรอบ
  - `inspection_test` (FK CASCADE), `round_number`, `result_type` (FK→InspectionResultType, PROTECT, nullable), `comment`
  - unique: `(inspection_test, round_number)`

### 4.3 Inspection Record Flow (legacy / production)
- `InspectionRecord` (`inspection_inspectionrecord`) — บันทึกการตรวจแบบรวม มี field นับ defect เยอะมาก (machine_ng/ok, pqc_ng/ok, kanban_mismatch, bush_vertical_*, spatter, stopper_leak, round_recline_leak ...)
- `InspectionDefect` (`inspection_inspectiondefect`) — defect ที่พบใน record (machine_quantity / pqc_quantity / quantity)

### 4.4 Verification Record (legacy)
- `VerificationRecord` (`inspection_verificationrecord`) — `inspection_date`, `defect_type`, `test_condition`, `result` (found/not_found/pending), `round_no`, `found_count`, `not_found_count`, `comment`

### 4.5 ความสัมพันธ์ (ER)
```
ProductionLine  1──N  InspectionSession        TestCondition  1──N  InspectionSession
Inspector       1──N  InspectionSession
InspectionSession  1──N  InspectionTest         DefectType  1──N  InspectionTest
InspectionTest     1──N  InspectionRound        InspectionResultType  1──N  InspectionRound

ProductionLine  1──N  InspectionRecord          TestCondition  1──N  InspectionRecord
InspectionRecord   1──N  InspectionDefect       TestCondition  1──N  InspectionDefect   DefectType  1──N  InspectionDefect
```

---

## 5. Business Logic (`views_helpers.py`) — กฎสำคัญ

ค่าคงที่:
```python
FOUND_RESULT_NAME = "Found"
NOT_FOUND_RESULT_NAME = "Not Found"
NOT_FOUND_STOP_LIMIT = 4                                    # Not Found ครบ 4 รอบ => จบ test อัตโนมัติ
NOT_FOUND_STOP_REASON = "NOT_FOUND reached 4 occurrences"
AUTO_COMPLETED_MESSAGE = "Inspection completed automatically because NOT_FOUND reached 4 occurrences."
```

- **เลข session อัตโนมัติ** `build_next_session_number()` → รูปแบบ `TSYYYYMMDD-0001` (นับต่อจากรายการวันเดียวกัน)
- **บันทึก round** `record_inspection_round()`:
  - ต้องเลือก `found` หรือ `not_found`
  - เพิ่ม `completed_rounds` ทีละ 1, สร้าง `InspectionRound`
  - ถ้า `not_found_count >= 4` → `InspectionTest.status = finished` + `stop_reason`
  - ถ้าครบ `total_rounds` → `finished`
  - ถ้าทุก test ใน session เป็น `finished` → `InspectionSession.status = completed`
- **`test_summary(test)`** คืนค่า found/not_found/detection_rate/completed/total_rounds/next_round_number ฯลฯ
- **สร้าง session** (`InspectionCreateView.form_valid`): สร้าง `InspectionSession` (status=`in_progress`) แล้วสร้าง `InspectionTest` ต่อ defect ที่ถูกเลือก (rounds จาก `rounds_{defect.pk}`, ขั้นต่ำ 1)

---

## 6. URL Routing

### Root (`config/urls.py`)
| Path | View |
| --- | --- |
| `/healthz/` | healthz (เช็ค DB → `{"status":"ok"}`) |
| `/accounts/login/` | LoginView (template `registration/login.html`, form `BootstrapAuthenticationForm`) |
| `/accounts/logout/` | LogoutView |
| `/` | redirect → `inspection:dashboard` |
| `/admin/` | Django admin |
| `/inspection/` | include app urls (namespace `inspection`) |

### App (`apps/inspection/urls.py`)
```
language/<str:language>/        -> set_language
""                              -> DashboardView          (name=dashboard)
list/                           -> InspectionListView
list/export/                    -> InspectionSessionExportView
new/                            -> InspectionCreateView
bulk-delete/                    -> InspectionBulkDeleteView
<int:pk>/                       -> InspectionDetailView
<int:pk>/edit/                  -> InspectionUpdateView
<int:pk>/delete/                -> InspectionDeleteView
verification/  (+new/ <pk>/edit/ <pk>/delete/)  -> Verification*View
users/  (+new/ <pk>/edit/ <pk>/delete/)         -> User*View
master-data/production-lines/  (+new/ <pk>/edit/ <pk>/delete/) -> ProductionLine*View
master-data/inspectors/        ... -> Inspector*View
master-data/defect-types/      ... -> DefectType*View
master-data/test-conditions/   ... -> TestCondition*View
```

---

## 7. ระบบสี / ธีม (COLOR SYSTEM) — เอกสารสีครบทุกจุด

นี่คือหัวใจของ UI ถ้าจะทำซ้ำให้เหมือนเป๊ะ ให้ก็อปตัวแปรสีด้านล่างลงไฟล์ CSS ตามเดิม

### 7.1 ตัวแปรหลัก (Global) — `static/inspection/css/base.css` ใน `:root`
```css
:root {
  --ink: #101827;            /* ตัวอักษรหลัก */
  --muted: #667085;          /* ตัวอักษรรอง/คำอธิบาย */
  --line: #d8e0ea;           /* เส้นขอบ */
  --surface: #ffffff;        /* พื้นการ์ด */
  --surface-soft: #eef3f8;   /* พื้นนุ่ม */
  --blue: #00a8e8;           /* ฟ้า brand หลัก */
  --blue-dark: #005f99;      /* ฟ้าเข้ม (ลิงก์/ข้อความเน้น) */
  --blue-deep: #06284a;      /* ฟ้าน้ำเงินเข้ม (หัวข้อการ์ด) */
  --blue-soft: #e6f7ff;      /* ฟ้าอ่อน (chip/icon bg) */
  --green: #12b886;          /* เขียว success */
  --amber: #f59f00;          /* ส้ม warning */
  --red: #e03131;            /* แดง danger / ปุ่มหลัก */
  --nav: #071827;            /* พื้น sidebar เข้ม */
  --nav-2: #0a2742;          /* พื้น sidebar ไล่ระดับ */
  --shadow: 0 18px 42px rgba(4,24,43,0.12);
}
```

### 7.2 ธีม Dashboard (override เฉพาะหน้า dashboard) — `dashboard.css` ใน `.dashboard-page`
```css
.dashboard-page {
  --dash-primary: #0f4c81;
  --dash-primary-dark: #0a3a63;
  --dash-accent: #2da8ff;
  --dash-success: #10b981;
  --dash-warning: #f59e0b;
  --dash-danger: #ef4444;
  --dash-bg: #f4f7fa;
  --dash-text: #1e293b;
  --dash-muted: #64748b;
  --dash-border: #e2e8f0;
  --dash-radius: 12px;
  --dash-shadow: 0 4px 16px rgba(15,76,129,0.08);
  --dash-transition: 0.2s ease;
}
```
> หมายเหตุ: ใน dashboard KPI `.kpi-card.danger` ใช้ `--dash-accent` (#2da8ff) **ไม่ใช่** `--dash-danger` (ตั้งใจให้การ์ด danger เป็นสีฟ้า)

### 7.3 สีที่เขียนตายตัว (hardcoded) แยกตามไฟล์

**base.css (Layout / Sidebar / Topbar)**
| องค์ประกอบ | สี |
| --- | --- |
| Body background (grid lines) | `rgba(0,168,232,0.05)` + ไล่ระดับ `#f7fbff → #eef3f8 → #e8eef6` |
| Sidebar bg | ไล่ระดับ `var(--nav) #071827 → var(--nav-2) #0a2742` |
| Brand mark gradient | `#00a8e8 → #1fd1ff` (มีจุดแดง `#e03131` มุมล่างขวา) |
| Nav link text | `#d9e8f6` |
| Nav link icon | `#64d6ff` |
| Nav link hover/active bg | `rgba(0,168,232,0.16)` / border `rgba(100,214,255,0.34)` |
| Nav link active แถบซ้าย | `var(--red) #e03131` |
| Topbar gradient | radial `rgba(0,168,232,0.28)` + linear `#071827 → #0a3155 → #005f99` |
| Topbar text muted | `#c7d8e8` |
| Table header bg | `#071827` / border `#153958` / text #fff |
| Table hover row | `#edf9ff` |
| ปุ่ม `.btn-primary` | bg/border `#e03131`, hover `#c92a2a` (สีแดง) |
| ปุ่ม `.btn-outline-primary` | text `#005f99`, border `#00a8e8`, hover bg `#00a8e8` |
| `.chip` (ทั่วไป) | bg `#e6f7ff`, text `#005f99`, border `rgba(0,168,232,0.18)` |
| `.chip` (ใน topbar) | bg `rgba(255,255,255,0.12)`, text #fff |
| `.status-pill.on` | bg `#e7f8f1`, text `#12b886` |
| `.status-pill.off` | bg `#f1f5f9`, text `#667085` |
| Logout button | bg `rgba(224,49,49,0.12)`, border `rgba(224,49,49,0.35)`, text `#ffd7d7` |

**auth.css (หน้า Login)**
- auth-body bg: ไล่ระดับ `#071827 → #0a3155` (ครึ่งบน) ต่อด้วย `#eef3f8 → #f7fbff` (ครึ่งล่าง), grid lines `rgba(0,168,232,0.06)`
- auth-panel: #fff, border `var(--line)`
- input focus: border `var(--blue) #00a8e8`, shadow `rgba(0,168,232,0.18)`

**form.css (หน้าสร้าง/แก้ Session)**
- `.setup-step-icon` bg `var(--blue-soft)`, text `var(--blue-dark)`
- `.required-dot` (จุดแดงหน้า label) `#dc2626`
- `.defect-card` hover border `var(--blue) #00a8e8`, shadow `rgba(82,179,230,0.12)`
- `.defect-card.active` border `var(--blue-dark)`, bg `#f3fbff`, shadow `rgba(82,179,230,0.16)`
- `.field-shell` bg `#f8fafc`, border `#eeeeee`
- `.sticky-actions` bg `rgba(237,242,247,0.94)` (blur)

**list.css (หน้ารายการ)**
- `.session-total-chip` bg `#fff0f0`, text `#b42318`, border `rgba(224,49,49,0.18)`

**detail.css (หน้าทดสอบ/สรุป)**
| องค์ประกอบ | สี |
| --- | --- |
| ปุ่มผล `found` (active) | bg/border `#198754` (เขียว) |
| ปุ่มผล `not_found` (active) | bg/border `#dc3545` (แดง) |
| `.status-finished` | bg `#dcfce7`, text `#166534` |
| `.status-active` | bg `#dbeafe`, text `#1d4ed8` |
| `.round-panel` border | `#dbe3ef` |
| `.summary-defect-card` | bg #fff, shadow `rgba(15,23,42,0.05)` |

**master_data_form.css**
- help-panel / status-tile bg `#f8fafc`, border `var(--line)`
- `.master-help-icon` bg `var(--blue-soft)`, text `var(--blue-dark)`
- `.master-field` bg #fff, border `#eeeeee`

### 7.4 สีของ Bootstrap (override ผ่าน CSS variable)
ปุ่มหลักถูกเปลี่ยนให้เป็นสีแดงของระบบ:
```css
.btn-primary { --bs-btn-bg: #e03131; --bs-btn-border-color: #e03131; --bs-btn-hover-bg: #c92a2a; ... color:#fff; font-weight:800; }
.btn-outline-primary { --bs-btn-color: #005f99; --bs-btn-border-color: #00a8e8; --bs-btn-hover-bg: #00a8e8; font-weight:800; }
```

### 7.5 ฟอนต์ (Font)
- ครอบทั้งระบบ: `"Sarabun", "Noto Sans Thai", "Segoe UI", Arial, sans-serif`
- โหลดจาก Google Fonts (weights 300–800)

### 7.6 ไอคอน (Icon)
- ใช้ Bootstrap Icons (`bi-*`): `bi-cpu`, `bi-speedometer2`, `bi-clipboard2-pulse`, `bi-sliders`, `bi-exclamation-diamond`, `bi-diagram-3`, `bi-person-badge`, `bi-people`, `bi-layout-sidebar-inset`, `bi-translate`, `bi-calendar-check`, `bi-check2-circle`, `bi-activity`, `bi-graph-up-arrow`, `bi-plus-circle`, `bi-inbox`, `bi-person`, `bi-shield-lock`, `bi-box-arrow-in-right` ฯลฯ

### 7.7 สีใน Excel Report (`views_sessions.py`)
- หัว Section: ไล่ระดับ `fgColor="1F4E78"` (น้ำเงินเข้ม), ตัวอักษร #fff
- หัวตาราง: `fgColor="000000"` (ดำ), ตัวอักษร #fff
- ตารางรายงาน: แถวทั้งหมดพื้นดำ `fgColor="000000"`, ตัวอักษร #fff, เส้นขอบ `1F1F1F`
- เส้นขอบตาราง: `color="D9E2EC"`

---

## 8. ระบบแปลภาษา (i18n) — `apps/inspection/i18n.py`

- `DEFAULT_LANGUAGE = "th"`, `SUPPORTED_LANGUAGES = {"th": "ไทย", "en": "English"}`
- `TRANSLATIONS` dict แยก `en` และ `th` (กุญแจเป็นข้อความ EN/TH เต็มประโยค)
- **Context processor** `context(request)` → ส่ง `ui_language`, `ui_languages`, `ui_translations_json` ไปทุกเทมเพลต
- เปลี่ยนภาษา: ลิงก์ `set_language` (view ใน `views_language.py`) → เก็บลง `request.session["ui_language"]` + cookie
- **Runtime translate (JS):** `static/inspection/js/base.js` อ่าน JSON จาก `<script id="ui-translations">` แล้วแปล text node / placeholder / title / aria-label ทันทีในเบราว์เซอร์ (รวม pattern พิเศษ เช่น "Round 3" → "รอบที่ 3", "X selected" → "เลือก X รายการ")

---

## 9. Static JS (`static/inspection/js/`)

| ไฟล์ | หน้าที่ |
| --- | --- |
| `base.js` | เก็บภาษา, toggle sidebar (localStorage key `inspection.sidebar.collapsed`), แปล UI อัตโนมัติ, เติม csrf token ใน form POST |
| `dashboard.js` | นาฬิกา live (`[data-dashboard-clock]`, อัปเดตทุก 30 วิ) |
| `form.js` | logic เลือก defect card + กำหนดรอบ (front-end) |
| `detail.js` | logic บันทึก round / สลับ defect ในหน้าทดสอบ |
| `list.js` | bulk select / bulk delete |

`base.js` ถูกโหลดใน `base.html` ทุกหน้า (`{% static 'inspection/js/base.js' %}`)

---

## 10. การตั้งค่า Django (`config/settings.py`) — สำคัญ

- อ่านค่าจาก `.env` ผ่าน `python-dotenv` (มี `env()`, `env_bool()`, `env_int()`, `env_list()` helper)
- `INSTALLED_APPS` มีแค่ `apps.inspection` + Django built-in
- `MIDDLEWARE` เพิ่ม `whitenoise.middleware.WhiteNoiseMiddleware`
- `TEMPLATES` → context processor เพิ่ม `apps.inspection.i18n.context`
- `DATABASES` → PostgreSQL (`django.db.backends.postgresql`)
- `LANGUAGE_CODE = "th"`, `TIME_ZONE = "Asia/Bangkok"`, `USE_I18N = True`
- `LANGUAGES = [("th","ไทย"), ("en","English")]`
- Static: `STATIC_URL="/static/"`, `STATIC_ROOT=BASE_DIR/"staticfiles"` ใช้ `whitenoise.storage.CompressedManifestStaticFilesStorage`
- Security: อ่านจาก env (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `HSTS_*`) — เปิดอัตโนมัติใน production

---

## 11. ตัวแปรสภาพแวดล้อม (`.env`) — ดู `.env.example`

| ตัวแปร | คำอธิบาย |
| --- | --- |
| `DJANGO_ENV` | `production` สำหรับ deploy |
| `DEBUG` / `DJANGO_DEBUG` | false ใน production |
| `DJANGO_SECRET_KEY` | สร้าง random (setup.bat ทำให้) |
| `ALLOWED_HOSTS` | คั่นค่าด้วยจุลภาค เช่น `*` สำหรับ LAN |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | origin ที่ trusted (ถ้ามี) |
| `DJANGO_SECURE_SSL_REDIRECT` ฯลฯ | ตั้งค่า HTTPS/HSTS |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | PostgreSQL |
| `DB_HOST` | `db` (docker) |
| `DB_PORT` | `5432` |
| `DB_WAIT_TIMEOUT` | วินาทีที่รอ DB ตอน start |
| `DB_CONN_MAX_AGE` | อายุ connection |
| `DB_SSLMODE` | โหมด SSL (`prefer`) |
| `GUNICORN_WORKERS` / `GUNICORN_TIMEOUT` / `GUNICORN_LOG_LEVEL` | ตั้งค่า Gunicorn |

> ห้ามใส่ `POSTGRES_*` แยก `docker-compose.yml` map `DB_*` ให้ image postgres ให้เอง

---

## 12. การ Deploy

### 12.1 Docker (แนะนำ / Windows one-click)
- `docker-compose.yml`: service `web` (build จาก Dockerfile, port `0.0.0.0:8000:8000`, healthcheck `/healthz/`) + `db` (postgres:16-alpine, volume `postgres_data`)
- `Dockerfile`: base `python:3.12-slim`, ติดตั้ง requirements, สร้าง user `app`, รัน `entrypoint.sh`
- `entrypoint.sh`: รอ PostgreSQL → `manage.py check --deploy` → `migrate` → `collectstatic` → รัน cmd (gunicorn)
- **Windows scripts:**
  - `setup.bat` — เช็ค Docker → สร้าง `.env` + สร้าง secret → build → up → migrate → collectstatic → health check → เปิด browser
  - `start.bat` — `docker compose up -d`
  - `stop.bat` — `docker compose down`
  - `update.bat` — `git pull` → build --no-cache → up
  - `reset.bat` — `docker compose down -v` + `docker system prune` (พิมพ์ `RESET` ยืนยัน)

### 12.2 Linux (systemd + Nginx) — `install.sh`
- สร้าง venv, ติดตั้ง deps, migrate, collectstatic
- เขียน systemd service (`inspection.service`) รัน gunicorn ผ่าน unix socket `/run/inspection/gunicorn.sock`
- เขียน Nginx site (proxy ไป socket, เสิร์ฟ `/static/` `/media/`)
- ตั้ง permission และ restart services
- ตรวจ env: ต้อง `DJANGO_ENV=production`, `DEBUG=false`, เปลี่ยน `DJANGO_SECRET_KEY` จาก placeholder

---

## 13. ขั้นตอนสร้างระบบนี้ใหม่ให้เหมือน 100% (Checklist)

1. **สร้างโครงสร้างโปรเจกต์**
   - `config/` (settings, urls, wsgi) + `apps/inspection/` (app label `inspection`)
   - เพิ่ม `"apps.inspection"` ใน `INSTALLED_APPS`, `ROOT_URLCONF="config.urls"`
2. **คัดลอก Models** จากหัวข้อ 4 ลง `models.py` แล้วรัน `makemigrations` / `migrate`
3. **คัดลอก Forms / Views / URLs** ตามหัวข้อ 4–6 (แยกไฟล์ตามชื่อเพื่อให้ตรงกับ import)
4. **คัดลอก `i18n.py`** และลงทะเบียน context processor ใน settings
5. **คัดลอกโฟลเดอร์ `static/inspection/`** (css + js) และ **`templates/`** ทั้งหมด — **ต้องใช้ตัวแปรสีในหัวข้อ 7 ให้ตรงเท่านั้นถึงจะเหมือนเป๊ะ**
6. **ตั้ง `.env`** จาก `.env.example` (เดี๋ยว setup.bat / install.sh สร้าง secret ให้)
7. **Seed ข้อมูลตั้งต้น** (ผลรอบต้องมี Found/Not Found):
   ```sql
   INSERT INTO inspection_inspectionresulttype (name, description, is_active, created_at)
   VALUES
     ('Found', 'Defect was detected during the test round.', TRUE, CURRENT_TIMESTAMP),
     ('Not Found', 'Defect was not detected during the test round.', TRUE, CURRENT_TIMESTAMP)
   ON CONFLICT (name) DO NOTHING;
   ```
8. **Deploy:** Docker → `setup.bat` (Win) / `install.sh` (Linux) หรือ `docker compose up -d`
9. **สร้าง superuser:** `docker compose exec web python manage.py createsuperuser`
10. เปิด `http://localhost:8000` → Login → เริ่มสร้าง Master Data แล้วสร้าง Test Session

---

## 14. คำสั่งจัดการที่ใช้บ่อย

```powershell
# พัฒนา本地
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# Docker
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose ps
docker compose logs web
docker compose down

# สร้าง secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 15. สรุปจุดที่ต้อง "ก็อปให้ครบ" เพื่อเหมือน 100%

| ลำดับ | สิ่งที่ห้ามตก | อยู่ที่ไฟล์ |
| --- | --- | --- |
| 1 | ตัวแปรสี `:root` + `.dashboard-page` | `base.css`, `dashboard.css` (หัวข้อ 7.1–7.2) |
| 2 | สี hardcoded ตามตาราง | `auth/form/list/detail/master_data_form.css` (หัวข้อ 7.3) |
| 3 | Bootstrap override (`--bs-btn-*`) | `base.css` (7.4) |
| 4 | CDN Bootstrap/Icons/Sarabun | `<head>` ใน `base.html`, `login.html` |
| 5 | กฎ Not Found = 4 รอบ | `views_helpers.py` (หัวข้อ 5) |
| 6 | รูปแบบเลข session `TSYYYYMMDD-0001` | `views_helpers.build_next_session_number` |
| 7 | i18n dict TH/EN + JS translate | `i18n.py`, `base.js` |
| 8 | env-driven settings | `config/settings.py`, `.env.example` |
| 9 | Docker/Linux/Windows scripts | `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `install.sh`, `*.bat` |
| 10 | Seed result type (Found/Not Found) | หัวข้อ 13 ข้อ 7 |

> ทำตาม 10 ข้อนี้ ระบบที่ได้จะหน้าตา สี ภาษา และพฤติกรรม เหมือนต้นฉบับทุกประการ
