````markdown
# سیستم مدیریت پمپ‌ها - نسخه ماژولار

ساختار جدید ماژولار سیستم مدیریت پمپ‌ها

## ساختار پروژه
new_version/
├── app.py # برنامه اصلی Flask
├── run.py # نقطه ورود اجرا
├── config.py # تنظیمات
├── requirements.txt # نیازمندی‌ها
├── blueprints/ # ماژول‌های route
├── database/ # لایه دیتابیس
├── utils/ # ابزارها
├── templates/ # تمپلیت‌ها
└── static/ # فایل‌های استاتیک



## راه‌اندازی

```bash
# نصب نیازمندی‌ها
pip install -r requirements.txt

# سیستم مدیریت پمپ‌ها

این مخزن یک برنامه تحت وب ساده برای مدیریت پمپ‌های آب و چاه‌ها است. برنامه دو بخش اصلی دارد:

- ثبت و مدیریت ساعت‌های کارکرد پمپ‌ها و تاریخچه روشن/خاموش شدن پمپ‌ها (رویدادها در جدول `pump_history`).
- مدیریت مشخصات چاه‌ها، ثبت تغییرات در مشخصات هر چاه و تاریخچهٔ عملیات نگهداری (جداول `wells` و `wells_history`).

در ادامه یک README استاندارد برای راه‌اندازی و نگهداری پروژه آورده شده است.

## امکانات کلیدی

- ثبت رویدادهای روشن/خاموش پمپ‌ها و نگهداری تاریخچهٔ رویدادها (`pump_history`).
- رابط مدیریتی برای وارد کردن لیست چاه‌ها از یک فایل Excel و پیش‌نمایش قبل از اعمال.
- مدیریت مشخصات چاه (نام، موقعیت، عمق، مشخصات پمپ فعلی و ...).
- ثبت تغییرات چاه‌ها در `wells_history` به‌صورت قابل بازبینی (audit trail).
- صفحات گزارش‌گیری برای مشاهده تاریخچهٔ کامل پمپ‌ها و محاسبهٔ زمان‌های کارکرد.

## معماری و فایل‌های مهم

- `app.py`, `run.py` — نقطهٔ ورود برنامه (Flask).
- `blueprints/` — مجموعهٔ مسیرها (routes) برای پنل مدیریت، گزارش‌ها، چاه‌ها، پمپ‌ها و احراز هویت.
- `database/` — لایهٔ دیتابیس شامل: مدل‌ها، عملیات و توابع گزارش‌گیری (`models.py`, `operations.py`, `wells_operations.py`, `reports.py`).
- `utils/` — ابزارهای کمکی: تولید و واردسازی فایل Excel، بکاپ‌گیری و تبدیل تاریخ.
- `templates/` — قالب‌های Jinja برای رابط کاربری.
- `create_database.py` — اسکریپت ایجاد اسکیمای دیتابیس و درج رکوردهای نمونه (idempotent؛ از `CREATE TABLE IF NOT EXISTS` استفاده می‌کند).

## نقشهٔ خلاصهٔ جداول و روابط

- `users` (id)
- `pumps` (id, pump_number, name, ...)
- `pump_history` (id, pump_id -> pumps.id, user_id -> users.id, action, event_time, ...)
- `wells` (id, well_number, name, pump_id -> pumps.id, ...)
- `wells_history` (id, well_id -> wells.id, changed_by_user_id -> users.id, change_type/operation_type, operation_date, ...)
- `deletion_logs` (ذخیرهٔ لاگ رکوردهای حذف‌شده)

این رابطه‌ها در کد در `database/models.py`, `database/operations.py` و `database/wells_operations.py` مصرف می‌شوند.

## رفتار مهم هنگام واردسازی (Import)

- صفحهٔ واردسازی (admin) قابلیت دانلود قالب Excel و بارگذاری فایل را دارد، سپس پیش‌نمایش و یک Apply انجام می‌شود.
- عملیات Apply اکنون فقط در حالت "merge" (ادغام) پشتیبانی می‌شود؛ حالت overwrite حذف شده تا از حذف تصادفی داده جلوگیری شود.
- هنگام واردسازی سعی می‌شود invariant زیر حفظ شود: `pump_number == well_number == wells.id` (پمپ‌ها و چاه‌ها با شناسه‌های معادل ساخته می‌شوند).

## نصب و اجرا (Windows / PowerShell)

1. نصب پایتون (3.8+ یا سازگار با requirements).
2. (اختیاری) ایجاد virtualenv و فعال‌سازی:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. نصب وابستگی‌ها:

```powershell
py -m pip install -r requirements.txt
```

4. ایجاد یا بازسازی دیتابیس خام (این دستور جداول را با `IF NOT EXISTS` ایجاد می‌کند؛ اگر می‌خواهید دیتابیس از صفر ساخته شود، قبل از اجرا فایل `pump_management.db` را حذف یا بکاپ بگیرید):

```powershell
py .\create_database.py
```

5. اجرا کردن سرور Flask (نمونه):

```powershell
py .\run.py
# یا اگر از app.py استفاده می‌کنید
py .\app.py
```

6. باز کردن مرورگر و رفتن به: http://127.0.0.1:5000

## مرورگر مدیریتی و واردسازی

- از منوی مدیریت می‌توانید قالب Excel را دانلود کنید (دسته‌بندی ستون‌ها در `utils/import_utils.py`).
- پس از آپلود، سیستم پیش‌نمایش و تعداد insert/update احتمالی را نشان می‌دهد و سپس با انتخاب Apply در حالت merge داده‌ها درج/به‌روز می‌شوند.

## تست‌ها

- تست‌های واحد با unittest نوشته شده‌اند. برای اجرای آنها از این دستور استفاده کنید:

```powershell
py -m unittest discover -v
```

## مهاجرت و تغییر اسکیمای دیتابیس

- پروژه شامل چند اسکریپت مهاجرت و ابزار کمکی است، اما در زمان اجرا کد دیگر به صورت خودکار اسکیمای DB را تغییر نمی‌دهد (برای جلوگیری از تغییر ناخواسته اسکیمای محیط تولید).
- اگر نیاز به اضافه‌کردن ستون یا تغییر اسکیمای DB دارید، از اسکریپت‌های داخل `scripts/` یا `database/` استفاده کنید و حتماً قبل از اجرا از DB بکاپ بگیرید.

## فایل‌ها و توابع مرجع (برای توسعه‌دهنده)

- ثبت وضعیت پمپ و تاریخچهٔ رویدادها: `database/operations.py` → `change_pump_status`, `get_last_pump_event_time`
- مدیریت چاه‌ها و ثبت تغییرات: `database/wells_operations.py` → `record_well_event`, `get_all_wells`, `get_well_statistics`
- تولید و اعمال واردسازی Excel: `utils/import_utils.py` → `generate_template_bytes`, `parse_and_validate`, `apply_rows_to_db`
- ساخت دیتابیس: `create_database.py`

## نکات ایمنی و نگهداری

- حالت overwrite در واردسازی غیرفعال شده تا از حذف تصادفی داده جلوگیری شود.
- همیشه قبل از اجرای هر اسکریپت مهاجرت یا destructive از DB بکاپ بگیرید:

```powershell
Copy-Item .\pump_management.db .\pump_management.db.bak
```

## مشارکت

- اگر خواستید تغییر جدیدی اضافه کنید، ابتدا یک شاخه (branch) جدید بسازید و یک Pull Request ارسال کنید.

## مجوز

- (در صورت تمایل، نوع مجوز را اینجا اضافه کنید — مثال: MIT)

---

اگر مایل باشید من می‌توانم این README را به انگلیسی نیز اضافه کنم یا بخش‌های فنی (ER diagram کوچک، قرارداد API یا برنامه تست CI) را تکمیل کنم.
