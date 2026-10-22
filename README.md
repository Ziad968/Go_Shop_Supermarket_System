<div align="center">

# 🛒 Go Shop POS — جو شوب

**A modern, bilingual (Arabic / English) Point-of-Sale system for retail shops**
**نظام نقاط بيع عصري ثنائي اللغة (عربي / إنجليزي) للمحلات التجارية**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Local%20%7C%20Cloud-4169E1?logo=postgresql&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-1f538d)
![Dark Mode](https://img.shields.io/badge/Theme-Dark-222222)

[English](#english) &nbsp;|&nbsp; [العربية](#arabic)

</div>

---

<a id="english"></a>

# English

## Overview

**Go Shop POS** is a desktop point-of-sale application built with **Python**, **CustomTkinter** (dark mode) and **PostgreSQL**. It runs against a local PostgreSQL server or a cloud one such as Supabase. It covers the daily work of a small or medium shop: fast barcode checkout, inventory, invoices and returns, customer debts, suppliers and purchases, shift closing, sales and profit reports, an audit log, and automatic backups.

The interface switches between **Arabic (RTL)** and **English** with one click, and the cashier's current invoice is preserved when you switch.

## Features

| Area | What you get |
|---|---|
| **Cashier** | Barcode scanning or search by product name · line and invoice discounts (`10%` or a fixed amount) · optional VAT · payment by Cash / Visa / Vodafone Cash · partial payment recorded as customer debt · hold and resume invoices · product image preview · receipt printing |
| **Inventory** | Add products by barcode or manually · auto-generated EAN-13 barcodes · cost price, minimum stock, expiry date, category, supplier, image · low-stock and near-expiry highlighting with header alerts · filters (All / Low / Sold out / Expiring) · barcode label printing · admin-only edit and delete |
| **Invoices** | Search by invoice number or customer · full details · **returns** (stock restored, amount deducted from sales) · reprint · WhatsApp |
| **Debts** | Open-debt list · partial or full payment · **customer statement** (invoices, debts, payments) · WhatsApp reminders |
| **Shift** | Close your shift: expected cash in the drawer vs. counted cash, with the difference recorded |
| **Suppliers** *(admin)* | Supplier list with totals purchased and amounts owed · **purchase invoices** that increase stock and update cost automatically · category management |
| **Reports** *(admin)* | Today / 7 days / 30 days / all time · invoices, net sales, returns, **profit**, collected, outstanding · bar charts · breakdown by payment method and by employee · CSV export (opens in Excel) |
| **Activity log** *(admin)* | Who changed a price, edited stock, deleted a product, made a sale or return, and when |
| **Settings** *(admin)* | Users, passwords, promotion/demotion · shop name, address, phone, logo · VAT rate · country code · backup folder |
| **Safety** | Hashed passwords (PBKDF2-SHA256) · role-based access · automatic SQL backups · one-click backup and export |

## Roles and permissions

| Capability | Admin | Employee |
|---|:---:|:---:|
| Sell, hold/resume invoices, returns, collect debts, close own shift | ✅ | ✅ |
| Add a **new** product | ✅ | ✅ |
| Edit an existing product / delete a product / see cost prices | ✅ | ❌ |
| Suppliers, purchases, categories | ✅ | ❌ |
| Sales and profit reports, activity log | ✅ | ❌ |
| Users, passwords, shop settings, backups | ✅ | ❌ |

- The **admin account can never be deleted**, an admin cannot demote themselves, and at least one admin always remains.
- An admin can **promote** an employee to admin and **demote** an admin back to employee. Permissions are re-checked against the database on every admin action, so a demotion applies immediately.

## Tech stack

- **Python 3.9+** (developed and tested on 3.11 / 3.12)
- **CustomTkinter** + **Pillow** — user interface
- **psycopg2** — PostgreSQL access with a connection pool and transactions
- **PostgreSQL** — local installation or a cloud service such as Supabase

## Project structure

```
go-shop-pos/
├── gui.py            # CustomTkinter interface (Arabic / English, dark mode)
├── logic.py          # Business logic: auth, cart, discounts, VAT, returns, reports, shifts
├── database.py       # PostgreSQL connection, schema and all queries
├── tools.py          # Receipts, barcode (EAN-13) and labels, WhatsApp links, backup, CSV export
├── requirements.txt
└── README.md
```

Folders created automatically at runtime: `receipts/`, `labels/`, `backups/`, `product_images/`, `assets/`.

## Installation

### 1. Install the dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare PostgreSQL

**Option A — Local PostgreSQL (recommended for a single shop)**

1. Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/) and remember the `postgres` user's password.
2. Create an empty database (pgAdmin → *Databases* → *Create*, or in the SQL shell):

   ```sql
   CREATE DATABASE Go_shop;
   ```

   Any name works as long as you use it in the connection URL below.

**Option B — Cloud (e.g. Supabase)**

Use the **Session pooler** connection string (it works over IPv4) and set `DB_SSLMODE=require`.

### 3. Configure the connection

Set the connection URL either by editing `DATABASE_URL` at the top of `database.py`, or with environment variables:

```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/Go_shop"
$env:DB_SSLMODE   = "prefer"      # use "require" for cloud databases
```

```bash
# Linux / macOS
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/Go_shop"
export DB_SSLMODE="prefer"
```

> If the password contains special characters, URL-encode them (for example `@` → `%40`).

### 4. Run

```bash
python gui.py
```

All tables are created automatically on first launch.

### Default accounts — change them immediately

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Employee | `cashier` | `1234` |

Go to **Settings → Users**, select a user and change the password.

## Quick usage guide

1. **First setup (admin):** *Settings* → enter the shop name, address, phone, VAT rate and logo → *Save*. Change the default passwords and add your employees.
2. **Add products:** *Inventory* → scan or type the barcode (or press 🎲 to generate one) → fill in the fields → *Save product*. Entering an existing barcode **adds** the quantity to its stock.
3. **Sell:** *Cashier* → scan the barcode (or type part of the product name and press Enter). Use *Discount* for a line discount, or the discount field for the whole invoice (`10%` or an amount). Choose the payment method and press *Checkout*.
4. **Customer owes money?** Select a customer, enter the paid amount (less than the total), and the remainder is saved as debt. Collect it later from the *Debts* tab.
5. **Customer wants to return an item?** *Invoices* → open the invoice → select the item → *Return selected*.
6. **End of day:** *Shift* → enter the cash you counted → *Close shift*.
7. **Check the business:** *Reports* → choose the period.

### Printing receipts and labels

Receipts and barcode labels open in your browser as a clean 80 mm page. Press **🖨 Print** (or `Ctrl+P`) and pick your thermal printer, or choose **Save as PDF**. Barcode labels use EAN-13.

### WhatsApp

The app opens WhatsApp (Web/Desktop) with a ready-made message to the customer's number; you press send. Set your **country code** in Settings so local numbers are converted to international format.

## Backup and restore

- **Automatic:** when an admin logs in, a SQL backup is created if the last one is older than 24 hours, then every 6 hours while the app stays open. The latest 30 backups are kept in `backups/`.
- **Manual:** *Settings → Backup now*. Use *Export (CSV)* for Excel-friendly files.
- **Restore into an empty database:**

  ```bash
  python gui.py                                   # run once to create the tables, then close
  psql -U postgres -d Go_shop -c "DELETE FROM users;"
  psql -U postgres -d Go_shop -f backups/goshop_backup_YYYYMMDD_HHMMSS.sql
  ```

Back up the `backups/` folder to another drive or cloud storage regularly.

## Troubleshooting

| Problem | Fix |
|---|---|
| `database "Go_shop" does not exist` | Create the database first (step 2), or point `DATABASE_URL` to an existing one. |
| `password authentication failed` | Check the password in `DATABASE_URL`; URL-encode special characters. |
| Cannot connect to a cloud database | Use the Session pooler string and set `DB_SSLMODE=require`. |
| Local server refuses SSL | Use `DB_SSLMODE=prefer` (default). |
| Receipt does not appear / blank browser page | Use the latest `tools.py` (opens the file directly on Windows). The receipt file is also saved in `receipts/`; you can open it manually. |
| Product images do not show on another computer | Images are stored next to the program on the computer where they were added. |

## Good to know

- Held invoices live in memory only and are lost when the app closes.
- Prices are treated as **excluding** VAT; VAT is added on top when a rate is set.
- Deleting a product that was never sold removes it completely. A product with sales history is archived instead: it disappears from the cashier and inventory, while old invoices keep its name.
- Barcode labels support EAN-13. Other barcode formats print as text only.
- Printing goes through the browser; direct ESC/POS printer commands are not included.

## Suggested `.gitignore`

```
__pycache__/
backups/
receipts/
labels/
product_images/
assets/
.env
```

---

<a id="arabic"></a>

<div dir="rtl" align="right">

# العربية

## نظرة عامة

**جو شوب (Go Shop POS)** تطبيق مكتبي لنقاط البيع مبني بلغة **Python** وواجهة **CustomTkinter** بتصميم داكن عصري وقاعدة بيانات **PostgreSQL**، ويعمل مع خادم محلي أو سحابي مثل Supabase. يغطي العمل اليومي للمحل الصغير والمتوسط: كاشير سريع بالباركود، مخزون، فواتير ومرتجعات، ديون العملاء، موردون وفواتير شراء، تقفيل الوردية، تقارير مبيعات وأرباح، سجل نشاط، ونسخ احتياطي تلقائي.

تتبدّل الواجهة بين **العربية (من اليمين لليسار)** و**الإنجليزية** بضغطة واحدة، مع الاحتفاظ بفاتورة الكاشير الحالية أثناء التبديل.

## المميزات

| القسم | ماذا يقدّم |
|---|---|
| **الكاشير** | ضرب الباركود أو البحث باسم المنتج · خصم على الصنف أو الفاتورة (`10%` أو مبلغ) · ضريبة قيمة مضافة اختيارية · الدفع كاش / فيزا / فودافون كاش · الدفع الجزئي يُسجَّل كدين على العميل · تعليق الفاتورة واسترجاعها · عرض صورة المنتج · طباعة الفاتورة |
| **المخزون** | إضافة المنتجات بالباركود أو يدويًا · توليد باركود EAN-13 تلقائيًا · سعر الشراء والحد الأدنى وتاريخ الصلاحية والتصنيف والمورد والصورة · تمييز الناقص وقريب الانتهاء بالألوان مع تنبيه أعلى الشاشة · فلاتر (الكل / ناقص / خلصان / قرب الانتهاء) · طباعة ملصقات الباركود · التعديل والحذف للأدمن فقط |
| **الفواتير** | بحث برقم الفاتورة أو العميل · تفاصيل كاملة · **مرتجعات** (يعود المخزون ويُخصم المبلغ من المبيعات) · إعادة الطباعة · واتساب |
| **الديون** | قائمة الديون المفتوحة · سداد جزئي أو كامل · **كشف حساب العميل** (فواتير وديون ومدفوعات) · تذكير عبر واتساب |
| **الوردية** | تقفيل الوردية: المفروض في الدرج مقابل الكاش الفعلي مع تسجيل الفرق |
| **الموردون** *(أدمن)* | قائمة الموردين مع إجمالي المشتريات والمستحق · **فواتير الشراء** التي تزيد المخزون وتحدّث سعر الشراء تلقائيًا · إدارة التصنيفات |
| **التقارير** *(أدمن)* | اليوم / 7 أيام / 30 يومًا / الكل · عدد الفواتير وصافي المبيعات والمرتجعات و**الأرباح** والمحصّل والمتبقي · رسوم بيانية · حسب طريقة الدفع وحسب الموظف · تصدير CSV يفتح في Excel |
| **سجل النشاط** *(أدمن)* | من غيّر سعرًا أو عدّل مخزونًا أو حذف منتجًا أو أجرى بيعًا أو مرتجعًا، ومتى |
| **الإعدادات** *(أدمن)* | المستخدمون وكلمات المرور والترقية/التنزيل · اسم المحل والعنوان والهاتف واللوجو · نسبة الضريبة · كود الدولة · مجلد النسخ الاحتياطي |
| **الأمان** | كلمات مرور مشفّرة (PBKDF2-SHA256) · صلاحيات حسب الدور · نسخ احتياطي SQL تلقائي · نسخ وتصدير بضغطة واحدة |

## الأدوار والصلاحيات

| الإمكانية | أدمن | موظف |
|---|:---:|:---:|
| البيع، تعليق الفواتير، المرتجعات، تحصيل الديون، تقفيل وردية الموظف نفسه | ✅ | ✅ |
| إضافة منتج **جديد** | ✅ | ✅ |
| تعديل منتج موجود / حذف منتج / رؤية أسعار الشراء | ✅ | ❌ |
| الموردون وفواتير الشراء والتصنيفات | ✅ | ❌ |
| تقارير المبيعات والأرباح وسجل النشاط | ✅ | ❌ |
| المستخدمون وكلمات المرور وإعدادات المحل والنسخ الاحتياطي | ✅ | ❌ |

- **حساب الأدمن لا يمكن حذفه إطلاقًا**، ولا يستطيع الأدمن تنزيل صلاحية نفسه، ويبقى أدمن واحد على الأقل دائمًا.
- يستطيع الأدمن **ترقية** موظف إلى أدمن و**تنزيل** أدمن إلى موظف. تُراجَع الصلاحيات من قاعدة البيانات عند كل إجراء إداري، فيسري التنزيل فورًا.

## التقنيات المستخدمة

- **Python 3.9+** (طُوِّر واختُبر على 3.11 و3.12)
- **CustomTkinter** و**Pillow** — الواجهة
- **psycopg2** — الاتصال بـ PostgreSQL مع مجمّع اتصالات ومعاملات (Transactions)
- **PostgreSQL** — محلي أو سحابي مثل Supabase

## هيكل المشروع

```
go-shop-pos/
├── gui.py            # الواجهة (عربي / إنجليزي، وضع داكن)
├── logic.py          # منطق العمل: الدخول، السلة، الخصومات، الضريبة، المرتجعات، التقارير، الورديات
├── database.py       # الاتصال بـ PostgreSQL والجداول وكل الاستعلامات
├── tools.py          # الفواتير، الباركود EAN-13 والملصقات، روابط واتساب، النسخ الاحتياطي، تصدير CSV
├── requirements.txt
└── README.md
```

تُنشأ هذه المجلدات تلقائيًا أثناء التشغيل: `receipts/` و`labels/` و`backups/` و`product_images/` و`assets/`.

## التثبيت

### 1. تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### 2. تجهيز PostgreSQL

**الخيار أ — PostgreSQL محلي (الأنسب لمحل واحد)**

1. ثبّت PostgreSQL من [postgresql.org](https://www.postgresql.org/download/) واحفظ كلمة مرور المستخدم `postgres`.
2. أنشئ قاعدة بيانات فارغة (من pgAdmin: *Databases* ← *Create*، أو من الـ SQL Shell):

   ```sql
   CREATE DATABASE Go_shop;
   ```

   يصلح أي اسم، بشرط استخدامه في رابط الاتصال أدناه.

**الخيار ب — سحابي (مثل Supabase)**

استخدم رابط **Session pooler** (يعمل على IPv4) واضبط `DB_SSLMODE=require`.

### 3. ضبط الاتصال

عدّل `DATABASE_URL` في أعلى ملف `database.py`، أو استخدم متغيرات البيئة:

```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/Go_shop"
$env:DB_SSLMODE   = "prefer"      # استخدم "require" مع القواعد السحابية
```

```bash
# Linux / macOS
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/Go_shop"
export DB_SSLMODE="prefer"
```

> إذا احتوت كلمة المرور على رموز خاصة فاستبدلها بالترميز المناسب في الرابط (مثل `@` ← `%40`).

### 4. التشغيل

```bash
python gui.py
```

تُنشأ كل الجداول تلقائيًا عند أول تشغيل.

### الحسابات الافتراضية — غيّرها فورًا

| الدور | اسم المستخدم | كلمة المرور |
|---|---|---|
| أدمن | `admin` | `admin123` |
| موظف | `cashier` | `1234` |

من **الإعدادات ← المستخدمون** اختر المستخدم وغيّر كلمة المرور.

## دليل الاستخدام السريع

1. **الإعداد الأول (الأدمن):** *الإعدادات* ← أدخل اسم المحل والعنوان والهاتف ونسبة الضريبة واللوجو ← *حفظ*. غيّر كلمات المرور الافتراضية وأضف موظفيك.
2. **إضافة المنتجات:** *المخزون* ← اضرب الباركود أو اكتبه (أو اضغط 🎲 لتوليد باركود) ← املأ الحقول ← *حفظ المنتج*. إدخال باركود موجود **يضيف** الكمية إلى مخزونه.
3. **البيع:** *الكاشير* ← اضرب الباركود (أو اكتب جزءًا من اسم المنتج واضغط Enter). استخدم زر *الخصم* لخصم على صنف، أو حقل الخصم لخصم الفاتورة كلها (`10%` أو مبلغ). اختر طريقة الدفع واضغط *إتمام البيع*.
4. **عميل عليه دين؟** اختر العميل واكتب المبلغ المدفوع (أقل من الإجمالي) ويُسجَّل الباقي كدين. حصّله لاحقًا من تبويب *الديون*.
5. **عميل يريد إرجاع صنف؟** *الفواتير* ← افتح الفاتورة ← اختر الصنف ← *ارتجاع المحدد*.
6. **نهاية اليوم:** *الوردية* ← اكتب الكاش الذي عددته ← *تقفيل الوردية*.
7. **متابعة المحل:** *التقارير* ← اختر الفترة.

### طباعة الفواتير والملصقات

تُفتح الفاتورة وملصقات الباركود في المتصفح كصفحة نظيفة بعرض 80 مم. اضغط **🖨 طباعة** (أو `Ctrl+P`) واختر الطابعة الحرارية، أو اختر **Save as PDF**. ملصقات الباركود بصيغة EAN-13.

### واتساب

يفتح التطبيق واتساب (ويب/ديسكتوب) برسالة جاهزة إلى رقم العميل وتضغط أنت إرسال. اضبط **كود الدولة** في الإعدادات ليتحوّل الرقم المحلي إلى الصيغة الدولية.

## النسخ الاحتياطي والاسترجاع

- **تلقائي:** عند دخول الأدمن تُنشأ نسخة SQL إذا مرّ أكثر من 24 ساعة على آخر نسخة، ثم كل 6 ساعات ما دام التطبيق مفتوحًا. تُحفظ آخر 30 نسخة في مجلد `backups/`.
- **يدوي:** *الإعدادات ← نسخة احتياطية الآن*، و*تصدير Excel (CSV)* لملفات تفتح في Excel.
- **الاسترجاع إلى قاعدة فارغة:**

  ```bash
  python gui.py                                   # شغّله مرة لإنشاء الجداول ثم أغلقه
  psql -U postgres -d Go_shop -c "DELETE FROM users;"
  psql -U postgres -d Go_shop -f backups/goshop_backup_YYYYMMDD_HHMMSS.sql
  ```

انسخ مجلد `backups/` بانتظام إلى قرص آخر أو تخزين سحابي.

## حل المشكلات

| المشكلة | الحل |
|---|---|
| `database "Go_shop" does not exist` | أنشئ قاعدة البيانات أولًا (الخطوة 2)، أو وجّه `DATABASE_URL` إلى قاعدة موجودة. |
| `password authentication failed` | راجع كلمة المرور في `DATABASE_URL` ورمّز الرموز الخاصة. |
| تعذّر الاتصال بقاعدة سحابية | استخدم رابط Session pooler واضبط `DB_SSLMODE=require`. |
| الخادم المحلي يرفض SSL | استخدم `DB_SSLMODE=prefer` (الافتراضي). |
| الفاتورة لا تظهر / صفحة المتصفح فارغة | استخدم أحدث `tools.py` (يفتح الملف مباشرة على ويندوز). وملف الفاتورة محفوظ أيضًا في `receipts/` ويمكنك فتحه يدويًا. |
| صور المنتجات لا تظهر على جهاز آخر | الصور تُحفظ بجوار البرنامج على الجهاز الذي أُضيفت منه. |

## ملاحظات مهمة

- الفواتير المعلّقة محفوظة في ذاكرة البرنامج فقط وتضيع عند إغلاقه.
- الأسعار تُعتبر **غير شاملة** للضريبة؛ تُضاف الضريبة فوقها عند تحديد نسبة.
- حذف منتج لم يُبَع قط يزيله تمامًا. أما المنتج الذي له مبيعات سابقة فيُؤرشَف: يختفي من الكاشير والمخزون، وتبقى الفواتير القديمة محتفظة باسمه.
- ملصقات الباركود تدعم EAN-13 فقط؛ الصيغ الأخرى تُطبع نصًا.
- الطباعة تتم عبر المتصفح، ولا تتضمن أوامر ESC/POS المباشرة للطابعات.

## ملف `.gitignore` المقترح

```
__pycache__/
backups/
receipts/
labels/
product_images/
assets/
.env
```

</div>
