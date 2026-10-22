"""
logic.py - منطق الشغل: الدخول والموظفين، الإعدادات، السلة والخصومات والضريبة، المنتجات،
المرتجعات، الديون، الموردين وفواتير الشراء، التقارير، الورديات، سجل النشاط، النسخ الاحتياطي.
"""
import hashlib
import hmac
import os
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import database as db
import tools

DEFAULT_ADMIN = ("admin", "admin123")     # غيّرها فور أول دخول
DEFAULT_EMPLOYEE = ("cashier", "1234")    # غيّرها فور أول دخول
MIN_PASSWORD_LEN = 4
PAYMENT_METHODS = ("cash", "visa", "vodafone")
ZERO = Decimal("0")


class POSError(Exception):
    """خطأ منطقي؛ الـ code بيترجم في الواجهة حسب اللغة."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


# ======================================================================
# أدوات مساعدة
# ======================================================================
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫،", "0123456789.,")


def q2(v):
    return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_decimal(text):
    try:
        value = Decimal(str(text).translate(_AR_DIGITS).replace(",", ".").strip())
    except InvalidOperation:
        raise POSError("invalid_number")
    if value < 0:
        raise POSError("invalid_number")
    return value


def parse_int(text):
    value = parse_decimal(text)
    if value != value.to_integral_value():
        raise POSError("invalid_number")
    return int(value)


def parse_date(text):
    text = str(text).translate(_AR_DIGITS).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise POSError("invalid_date")


def parse_discount(text):
    """'10%' = نسبة، '25' = مبلغ. ترجع (kind, value)."""
    text = str(text).strip()
    if not text:
        return "amount", ZERO
    if text.endswith("%"):
        v = parse_decimal(text[:-1])
        if v > 100:
            raise POSError("invalid_number")
        return "percent", v
    return "amount", parse_decimal(text)


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${digest}"


def verify_password(password, stored):
    return hmac.compare_digest(hash_password(password, stored.split("$", 1)[0]), stored)


def _is_admin(actor):
    """يتحقق من الصلاحية الحالية من الداتابيز (فالترقية/التنزيل تسري فورًا)."""
    if not actor:
        return False
    u = db.get_user(actor["username"])
    return bool(u and u["role"] == "admin")


def _require_admin(actor):
    if not _is_admin(actor):
        raise POSError("forbidden")


def log(actor, action, details=""):
    try:
        db.log_activity(actor["id"] if actor else None, actor["username"] if actor else "", action, details)
    except Exception:
        pass  # السجل لا يجب أن يعطّل العملية الأساسية


# ======================================================================
# الإعدادات
# ======================================================================
DEFAULT_SETTINGS = {"shop_name": "Go Shop", "shop_address": "", "shop_phone": "", "logo": "",
                    "vat_rate": "0", "country_code": "20", "auto_print": "1", "backup_dir": "backups"}
_cache = {}


def settings(refresh=False):
    if refresh or not _cache:
        _cache.clear()
        _cache.update(DEFAULT_SETTINGS)
        try:
            _cache.update(db.get_settings())
        except Exception:
            pass
    return _cache


def save_settings(actor, values):
    _require_admin(actor)
    if "vat_rate" in values and parse_decimal(values["vat_rate"]) > 100:
        raise POSError("invalid_number")
    if values.get("logo") and os.path.isabs(values["logo"]):
        values["logo"] = tools.store_file(values["logo"], "assets")
    for k, v in values.items():
        if k in DEFAULT_SETTINGS:
            db.set_setting(k, str(v))
    settings(refresh=True)
    log(actor, "settings", ", ".join(values))


# ======================================================================
# الدخول والمستخدمون
# ======================================================================
def bootstrap():
    """تجهيز الداتابيز: الجداول + مستخدمين افتراضيين."""
    db.init_schema()
    if db.count_users() == 0:
        db.create_user(DEFAULT_ADMIN[0], hash_password(DEFAULT_ADMIN[1]), "admin")
        db.create_user(DEFAULT_EMPLOYEE[0], hash_password(DEFAULT_EMPLOYEE[1]), "employee")
    settings(refresh=True)


def login(username, password):
    user = db.get_user(username or "")
    if not user or not verify_password(password or "", user["password_hash"]):
        raise POSError("bad_login")
    u = {"id": user["id"], "username": user["username"], "role": user["role"]}
    log(u, "login")
    return u


def list_users(actor):
    _require_admin(actor)
    return db.list_users()


def change_password(actor, username, new_password):
    _require_admin(actor)
    if len(new_password) < MIN_PASSWORD_LEN:
        raise POSError("short_password")
    db.update_user_password(username, hash_password(new_password))
    log(actor, "password_change", username)


def add_employee(actor, username, password):
    _require_admin(actor)
    username = username.strip()
    if not username or not password:
        raise POSError("empty_fields")
    if len(password) < MIN_PASSWORD_LEN:
        raise POSError("short_password")
    if db.get_user(username):
        raise POSError("user_exists")
    db.create_user(username, hash_password(password), "employee")
    log(actor, "employee_add", username)


def delete_employee(actor, username):
    """حذف موظف فقط. حساب الأدمن لا يُحذف أبدًا (لازم يتنزّل لموظف الأول)."""
    _require_admin(actor)
    target = db.get_user(username)
    if not target:
        raise POSError("not_found")
    if target["role"] == "admin":
        raise POSError("cant_delete_admin")
    db.delete_user(username)
    log(actor, "employee_delete", username)


def set_role(actor, username, role):
    """ترقية موظف لأدمن أو تنزيل أدمن لموظف. لازم يفضل أدمن واحد على الأقل."""
    _require_admin(actor)
    target = db.get_user(username)
    if not target or role not in ("admin", "employee"):
        raise POSError("not_found")
    if target["role"] == role:
        return
    if role == "employee":
        if target["username"] == actor["username"]:
            raise POSError("cant_demote_self")
        if db.count_admins() <= 1:
            raise POSError("last_admin")
    db.set_user_role(username, role)
    log(actor, "role_change", f"{username}: {target['role']} → {role}")


def activity(actor, search=""):
    _require_admin(actor)
    return db.list_activity(search)


# ======================================================================
# المنتجات
# ======================================================================
def new_barcode():
    """باركود EAN-13 فريد للمنتجات التي لا تحمل باركود."""
    while True:
        code = tools.random_ean13()
        if not db.get_product_by_barcode(code):
            return code


def product_image_path(filename):
    path = os.path.join(tools.folder("product_images"), filename or "")
    return path if filename and os.path.isfile(path) else None


def _prep_image(image):
    image = (image or "").strip()
    if image and os.path.isabs(image):
        if not os.path.isfile(image):
            raise POSError("bad_file")
        return tools.store_file(image, "product_images")
    return image


def _prep_product(name, price, stock, barcode, cost, min_stock, expiry, image):
    if not name.strip():
        raise POSError("empty_fields")
    return (name.strip(), parse_decimal(price), parse_int(stock or "0"), (barcode or "").strip(),
            parse_decimal(cost or "0"), parse_int(min_stock or "5"), parse_date(expiry), _prep_image(image))


def add_product(actor, name, price, stock, barcode="", category="", supplier="",
                cost="0", min_stock="5", expiry="", image=""):
    """إضافة منتج (للأدمن والموظف). لو الباركود موجود فهو تعديل ويتطلب أدمن. الباركود الفاضي يتولّد تلقائيًا."""
    name, price, stock, barcode, cost, mn, exp, img = _prep_product(
        name, price, stock, barcode, cost, min_stock, expiry, image)
    if not barcode:
        barcode = new_barcode()
    elif not _is_admin(actor) and db.get_product_by_barcode(barcode):
        raise POSError("forbidden")
    pid, created = db.add_or_update_product(name, price, stock, category, supplier, barcode, cost, mn, exp, img)
    log(actor, "product_add" if created else "product_restock",
        f"{name} | {barcode} | price {price} | qty +{stock}")
    return pid, created


def update_product(actor, pid, name, price, stock, barcode, category="", supplier="",
                   cost="0", min_stock="5", expiry="", image=""):
    """تعديل كل بيانات المنتج (أدمن فقط) مع تسجيل التغييرات في السجل."""
    _require_admin(actor)
    name, price, stock, barcode, cost, mn, exp, img = _prep_product(
        name, price, stock, barcode, cost, min_stock, expiry, image)
    if not barcode:
        raise POSError("empty_fields")
    old = db.get_product(pid)
    try:
        db.update_product(pid, name, price, stock, barcode, category, supplier, cost, mn, exp, img)
    except db.DuplicateBarcode:
        raise POSError("barcode_exists")
    changes = [f"{label}: {a} → {b}" for label, a, b in (
        ("name", old["name"], name), ("price", q2(old["price"]), q2(price)), ("stock", old["stock"], stock),
        ("cost", q2(old["cost_price"]), q2(cost)), ("barcode", old["barcode"], barcode),
        ("category", old["category_name"] or "", category.strip()),
        ("supplier", old["supplier_name"] or "", supplier.strip())) if a != b]
    log(actor, "product_edit", f"{old['name']} | " + ("; ".join(changes) or "-"))


def delete_product(actor, pid):
    """يرجع 'deleted' (حذف نهائي) أو 'archived' (له فواتير قديمة: اختفى من البرنامج وبقيت الفواتير)."""
    _require_admin(actor)
    old = db.get_product(pid)
    status = db.delete_product(pid)
    log(actor, "product_delete", (f"{old['name']} | {old['barcode']} | stock {old['stock']} | {status}"
                                  if old else str(pid)))
    return status


def find_product(barcode):
    return db.get_product_by_barcode(barcode) if barcode.strip() else None


def search_products(text="", flt="all"):
    return db.list_products(text, flt)


def alert_counts():
    return db.alert_counts()


def print_labels(products, copies, auto=True):
    if not products:
        raise POSError("select_row")
    html = tools.labels_html(products, max(1, copies), settings())
    return tools.open_html(html, "labels.html", "labels")


# ======================================================================
# السلة والخصومات والضريبة والدفع
# ======================================================================
class Cart:
    def __init__(self):
        self.items = {}
        self.created = datetime.now()

    def add_barcode(self, barcode, qty=1):
        """ضرب الباركود: يضيف المنتج للفاتورة بعد التحقق من المخزون. ترجع سطر المنتج."""
        barcode = barcode.strip()
        if not barcode:
            raise POSError("empty_fields")
        p = db.get_product_by_barcode(barcode)
        if not p:
            raise POSError("not_found")
        line = self.items.get(p["id"])
        new_qty = (line["qty"] if line else 0) + qty
        if new_qty > p["stock"]:
            raise POSError("out_of_stock")
        self.items[p["id"]] = {
            "product_id": p["id"], "name": p["name"], "barcode": p["barcode"], "price": Decimal(p["price"]),
            "cost_price": Decimal(p["cost_price"]), "stock": p["stock"], "qty": new_qty,
            "image": p["image_path"] or "",
            "disc_kind": line["disc_kind"] if line else "amount",
            "disc_val": line["disc_val"] if line else ZERO,
        }
        return self.items[p["id"]]

    def change_qty(self, pid, delta):
        line = self.items.get(pid)
        if not line:
            return
        new_qty = line["qty"] + delta
        if new_qty > line["stock"]:
            raise POSError("out_of_stock")
        if new_qty <= 0:
            del self.items[pid]
        else:
            line["qty"] = new_qty

    def set_discount(self, pid, text):
        """خصم على الصنف: '10%' أو '5' (مبلغ)."""
        kind, val = parse_discount(text)
        if pid in self.items:
            self.items[pid]["disc_kind"], self.items[pid]["disc_val"] = kind, val

    def remove(self, pid):
        self.items.pop(pid, None)

    def clear(self):
        self.items.clear()

    def lines(self):
        return list(self.items.values())

    @staticmethod
    def line_gross(l):
        return q2(l["price"] * l["qty"])

    def line_discount(self, l):
        gross = self.line_gross(l)
        d = gross * l["disc_val"] / 100 if l["disc_kind"] == "percent" else l["disc_val"]
        return q2(min(d, gross))

    def line_net(self, l):
        return self.line_gross(l) - self.line_discount(l)

    def totals(self, invoice_discount="", vat_rate=None):
        """subtotal (بعد خصم الأصناف) → خصم الفاتورة → الضريبة → الإجمالي."""
        if vat_rate is None:
            vat_rate = parse_decimal(settings()["vat_rate"])
        subtotal = sum((self.line_net(l) for l in self.items.values()), ZERO)
        kind, val = parse_discount(invoice_discount)
        disc = subtotal * val / 100 if kind == "percent" else val
        disc = q2(min(disc, subtotal))
        vat = q2((subtotal - disc) * Decimal(vat_rate) / 100)
        return {"subtotal": subtotal, "discount": disc, "vat": vat, "total": subtotal - disc + vat}

    def checkout(self, user, customer_id=None, paid_text="", method="cash", invoice_discount=""):
        """إتمام الفاتورة. ترجع (order_id, الباقي للعميل, totals)."""
        if not self.items:
            raise POSError("empty_cart")
        if method not in PAYMENT_METHODS:
            method = "cash"
        t = self.totals(invoice_discount)
        paid = parse_decimal(paid_text) if str(paid_text).strip() else t["total"]
        if paid < t["total"] and not customer_id:
            raise POSError("debt_needs_customer")
        items = [{"product_id": l["product_id"], "name": l["name"], "qty": l["qty"], "price": l["price"],
                  "discount": self.line_discount(l), "cost_price": l["cost_price"]} for l in self.lines()]
        try:
            oid = db.create_order(user["id"], customer_id, items, t["subtotal"], t["discount"], t["vat"],
                                  t["total"], min(paid, t["total"]), method)
        except db.StockError:
            raise POSError("out_of_stock")
        log(user, "sale", f"#{oid} | total {t['total']} | {method}")
        self.clear()
        return oid, max(paid - t["total"], ZERO), t


# ======================================================================
# الفواتير والمرتجعات والطباعة
# ======================================================================
def search_orders(text=""):
    return db.list_orders(text)


def order_details(order_id):
    o = db.get_order(order_id)
    if not o:
        raise POSError("not_found")
    return o, db.get_order_items(order_id)


def process_return(actor, order_id, qty_map, method="cash"):
    """مرتجع: qty_map = {order_item_id: qty}. المخزون يزيد والمبلغ يخصم من المبيعات."""
    o, items = order_details(order_id)
    by_id = {i["id"]: i for i in items}
    sub, disc, vat = Decimal(o["subtotal"]), Decimal(o["discount"]), Decimal(o["vat"])
    base = sub - disc
    f_disc = base / sub if sub > 0 else Decimal(1)
    vat_rate = vat / base if base > 0 else ZERO
    lines, amount, vat_total = [], ZERO, ZERO
    for iid, qty in qty_map.items():
        if qty <= 0:
            continue
        it = by_id.get(iid)
        if not it or qty > it["quantity"] - it["returned"]:
            raise POSError("return_too_many")
        net_unit = (Decimal(it["unit_price"]) * it["quantity"] - Decimal(it["discount"])) / it["quantity"]
        net_ref = net_unit * f_disc * qty
        vat_ref = net_ref * vat_rate
        lines.append({"order_item_id": iid, "product_id": it["product_id"], "qty": qty,
                      "unit_refund": q2((net_ref + vat_ref) / qty)})
        amount += net_ref + vat_ref
        vat_total += vat_ref
    if not lines:
        raise POSError("empty_cart")
    rid = db.create_return(order_id, actor["id"], lines, q2(amount), q2(vat_total), method)
    log(actor, "return", f"order #{order_id} | refund {q2(amount)}")
    return rid, q2(amount)


def print_receipt(order_id, labels, change=None):
    o, items = order_details(order_id)
    s = settings()
    html = tools.receipt_html(o, items, s, labels, change, auto_print=False)
    return tools.open_html(html, f"receipt_{order_id}.html", "receipts")


def whatsapp_url(phone, text):
    url = tools.whatsapp_link(phone, text, settings()["country_code"])
    if not url:
        raise POSError("no_phone")
    return url


# ======================================================================
# العملاء والديون
# ======================================================================
def add_customer(name, phone=""):
    if not name.strip():
        raise POSError("empty_fields")
    return db.add_customer(name, phone)


def list_customers():
    return db.list_customers()


def open_debts():
    return db.get_open_debts()


def pay_debt(actor, debt_id, amount_text, remaining, method="cash"):
    """سداد دين. لو المبلغ فاضي يتم سداد المتبقي كله."""
    amount = parse_decimal(amount_text) if str(amount_text).strip() else Decimal(remaining)
    if amount <= 0:
        raise POSError("invalid_number")
    paid = db.pay_debt(debt_id, amount, method, actor["id"])
    log(actor, "debt_payment", f"debt #{debt_id} | {paid} | {method}")
    return paid


def customer_statement(cid):
    orders, debts, pays = db.customer_orders(cid), db.customer_debts(cid), db.customer_payments(cid)
    return {"customer": db.get_customer(cid), "orders": orders, "debts": debts, "payments": pays,
            "total_bought": sum((o["total"] for o in orders), ZERO),
            "total_remaining": sum((d["remaining"] for d in debts), ZERO)}


# ======================================================================
# الموردين والتصنيفات وفواتير الشراء (أدمن فقط)
# ======================================================================
def list_suppliers(actor):
    _require_admin(actor)
    return db.list_suppliers_detailed()


def save_supplier(actor, sid, name, phone=""):
    _require_admin(actor)
    if not name.strip():
        raise POSError("empty_fields")
    if sid:
        db.update_supplier(sid, name, phone)
    else:
        db.add_supplier(name, phone)
    log(actor, "supplier_save", name)


def delete_supplier(actor, sid):
    _require_admin(actor)
    db.delete_supplier(sid)
    log(actor, "supplier_delete", str(sid))


def list_categories(actor):
    _require_admin(actor)
    return db.list_categories_detailed()


def save_category(actor, cid, name):
    _require_admin(actor)
    if not name.strip():
        raise POSError("empty_fields")
    db.rename_category(cid, name) if cid else db.add_category(name)
    log(actor, "category_save", name)


def delete_category(actor, cid):
    _require_admin(actor)
    db.delete_category(cid)
    log(actor, "category_delete", str(cid))


class PurchaseDraft:
    """فاتورة شراء من مورد: عند الحفظ يزيد المخزون تلقائيًا ويتحدث سعر الشراء."""

    def __init__(self):
        self.items = {}

    def add(self, query, qty_text, cost_text=""):
        query = query.strip()
        p = db.get_product_by_barcode(query)
        if not p:
            matches = db.list_products(query)
            if not matches:
                raise POSError("not_found")
            if len(matches) > 1:
                raise POSError("many_matches")
            p = matches[0]
        qty = parse_int(qty_text or "1")
        if qty <= 0:
            raise POSError("invalid_number")
        cost = parse_decimal(cost_text) if str(cost_text).strip() else Decimal(p["cost_price"])
        line = self.items.get(p["id"])
        self.items[p["id"]] = {"product_id": p["id"], "name": p["name"], "barcode": p["barcode"],
                               "qty": qty + (line["qty"] if line else 0), "cost": cost}

    def remove(self, pid):
        self.items.pop(pid, None)

    def lines(self):
        return list(self.items.values())

    def total(self):
        return sum((q2(l["cost"] * l["qty"]) for l in self.items.values()), ZERO)

    def save(self, actor, supplier_id, paid_text=""):
        _require_admin(actor)
        if not self.items:
            raise POSError("empty_cart")
        if not supplier_id:
            raise POSError("pick_supplier")
        total = self.total()
        paid = parse_decimal(paid_text) if str(paid_text).strip() else total
        pid = db.create_purchase(supplier_id, actor["id"], self.lines(), total, min(paid, total))
        log(actor, "purchase", f"#{pid} | total {total}")
        self.items.clear()
        return pid


def list_purchases(actor):
    _require_admin(actor)
    return db.list_purchases()


# ======================================================================
# التقارير (أدمن فقط)
# ======================================================================
_PERIOD_DAYS = {"today": 0, "7d": 6, "30d": 29}


def sales_report(actor, period="today"):
    _require_admin(actor)
    now = datetime.now().astimezone()
    since = None
    if period in _PERIOD_DAYS:
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = midnight - timedelta(days=_PERIOD_DAYS[period])
    s, rt, cogs = db.sales_summary(since), db.returns_summary(since), db.cogs(since)
    profit = (s["revenue"] - s["vat"]) - (rt["amount"] - rt["vat"]) - (cogs - rt["cogs"])
    return {
        "summary": {"orders": s["orders"], "sales": s["revenue"] - rt["amount"], "returns": rt["amount"],
                    "profit": profit, "collected": s["collected"], "outstanding": s["outstanding"]},
        "daily": db.sales_by_day(since, now.utcoffset()),
        "top": db.top_products(since),
        "by_user": db.sales_by_user(since),
        "by_method": db.sales_by_method(since),
    }


# ======================================================================
# تقفيل الوردية
# ======================================================================
def shift_info(user):
    now = datetime.now().astimezone()
    since = db.last_shift_close(user["id"]) or now.replace(hour=0, minute=0, second=0, microsecond=0)
    sales, debts, refunds = db.shift_totals(user["id"], since)
    to_map = lambda rows: {r["method"]: Decimal(r["amount"]) for r in rows}
    sales, debts, refunds = to_map(sales), to_map(debts), to_map(refunds)
    expected = sales.get("cash", ZERO) + debts.get("cash", ZERO) - refunds.get("cash", ZERO)
    return {"since": since, "sales": sales, "debt_payments": debts, "refunds": refunds,
            "expected_cash": expected}


def close_shift(user, counted_text, note=""):
    info = shift_info(user)
    counted = parse_decimal(counted_text)
    diff = counted - info["expected_cash"]
    db.close_shift(user["id"], user["username"], info["since"], info["expected_cash"], counted, diff, note)
    log(user, "shift_close", f"expected {info['expected_cash']} | counted {counted} | diff {diff}")
    return info["expected_cash"], diff


# ======================================================================
# النسخ الاحتياطي والتصدير
# ======================================================================
def backup_dir():
    return tools.folder(settings()["backup_dir"] or "backups")


def backup_now(actor=None):
    path = tools.backup_sql(backup_dir())
    tools.prune_backups(backup_dir())
    if actor:
        log(actor, "backup", os.path.basename(path))
    return path


def auto_backup_if_due():
    return backup_now() if tools.backup_due(backup_dir()) else None


def export_all(actor):
    _require_admin(actor)
    path = tools.export_csv(backup_dir())
    log(actor, "export", path)
    return path
