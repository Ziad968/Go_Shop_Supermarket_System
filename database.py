"""
database.py - طبقة قاعدة البيانات (PostgreSQL محلي أو سحابي)
-----------------------------------------------------------
متغيرات البيئة (اختيارية):
    DATABASE_URL : postgresql://postgres:PASSWORD@localhost:5432/Go_Shop
    DB_SSLMODE   : prefer (محلي) | require (Supabase / سحابي)
"""
import os
from contextlib import contextmanager

from psycopg2 import errors as pg_errors
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1596@localhost:5432/Go_Shop")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")

_pool = None


class StockError(Exception):
    """الكمية في المخزن لا تكفي أثناء إتمام الفاتورة."""


class DuplicateBarcode(Exception):
    """الباركود مستخدم في منتج آخر."""


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(1, 8, DATABASE_URL, sslmode=DB_SSLMODE, connect_timeout=10)
    return _pool


@contextmanager
def cursor():
    """Cursor داخل transaction: commit عند النجاح و rollback عند أي خطأ."""
    p = _get_pool()
    conn = p.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def fetch_all(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


# ======================================================================
# الجداول (CREATE + ALTER بحيث تعمل على داتابيز جديدة أو قديمة)
# ======================================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS suppliers (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, phone TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    barcode TEXT UNIQUE NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','employee')),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    total NUMERIC(12,2) NOT NULL,
    paid NUMERIC(12,2) NOT NULL,
    payment_method TEXT DEFAULT 'cash',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS customer_debts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL,
    paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- أعمدة جديدة
ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS min_stock INTEGER NOT NULL DEFAULT 5;
ALTER TABLE products ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_path TEXT DEFAULT '';
ALTER TABLE products ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS vat NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS cost_price NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS discount NUMERIC(12,2) NOT NULL DEFAULT 0;

-- جداول جديدة
CREATE TABLE IF NOT EXISTS debt_payments (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES customer_debts(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL,
    method TEXT DEFAULT 'cash',
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    total NUMERIC(12,2) NOT NULL,
    paid NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS purchase_items (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    cost_price NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS returns (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL,
    vat NUMERIC(12,2) NOT NULL DEFAULT 0,
    method TEXT DEFAULT 'cash',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS return_items (
    id SERIAL PRIMARY KEY,
    return_id INTEGER NOT NULL REFERENCES returns(id) ON DELETE CASCADE,
    order_item_id INTEGER REFERENCES order_items(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    details TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS shifts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    period_start TIMESTAMPTZ,
    closed_at TIMESTAMPTZ DEFAULT now(),
    expected_cash NUMERIC(12,2),
    counted_cash NUMERIC(12,2),
    difference NUMERIC(12,2),
    note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders (created_at);
"""

TABLES = ["categories", "suppliers", "customers", "users", "products", "orders", "order_items",
          "customer_debts", "debt_payments", "purchases", "purchase_items", "returns",
          "return_items", "settings", "activity_log", "shifts"]


def init_schema():
    with cursor() as cur:
        cur.execute(SCHEMA)


# ======================================================================
# الإعدادات وسجل النشاط
# ======================================================================
def get_settings():
    return {r["key"]: r["value"] for r in fetch_all("SELECT key, value FROM settings")}


def set_setting(key, value):
    execute("INSERT INTO settings(key, value) VALUES(%s,%s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (key, value))


def log_activity(user_id, username, action, details=""):
    execute("INSERT INTO activity_log(user_id, username, action, details) VALUES(%s,%s,%s,%s)",
            (user_id, username, action, details))


def list_activity(search="", limit=300):
    like = f"%{search.strip()}%"
    return fetch_all(
        "SELECT created_at, username, action, details FROM activity_log "
        "WHERE username ILIKE %s OR action ILIKE %s OR details ILIKE %s ORDER BY id DESC LIMIT %s",
        (like, like, like, limit))


# ======================================================================
# التصنيفات / الموردين / العملاء
# ======================================================================
def add_category(name):
    return fetch_one("INSERT INTO categories(name) VALUES(%s) ON CONFLICT (name) DO UPDATE "
                     "SET name = EXCLUDED.name RETURNING id", (name.strip(),))["id"]


def list_categories():
    return fetch_all("SELECT * FROM categories ORDER BY name")


def list_categories_detailed():
    return fetch_all("SELECT c.id, c.name, COUNT(p.id) AS products FROM categories c "
                     "LEFT JOIN products p ON p.category_id = c.id GROUP BY c.id ORDER BY c.name")


def rename_category(cid, name):
    return execute("UPDATE categories SET name=%s WHERE id=%s", (name.strip(), cid))


def delete_category(cid):
    return execute("DELETE FROM categories WHERE id=%s", (cid,))


def add_supplier(name, phone=""):
    return fetch_one(
        "INSERT INTO suppliers(name, phone) VALUES(%s,%s) ON CONFLICT (name) DO UPDATE "
        "SET phone = COALESCE(NULLIF(EXCLUDED.phone,''), suppliers.phone) RETURNING id",
        (name.strip(), phone))["id"]


def list_suppliers():
    return fetch_all("SELECT * FROM suppliers ORDER BY name")


def list_suppliers_detailed():
    return fetch_all(
        """SELECT s.id, s.name, s.phone,
                  COALESCE(SUM(pu.total),0) AS total_purchased,
                  COALESCE(SUM(pu.paid),0) AS paid,
                  COALESCE(SUM(pu.total - pu.paid),0) AS owed
           FROM suppliers s LEFT JOIN purchases pu ON pu.supplier_id = s.id
           GROUP BY s.id ORDER BY s.name""")


def update_supplier(sid, name, phone):
    return execute("UPDATE suppliers SET name=%s, phone=%s WHERE id=%s", (name.strip(), phone, sid))


def delete_supplier(sid):
    return execute("DELETE FROM suppliers WHERE id=%s", (sid,))


def add_customer(name, phone=""):
    return fetch_one("INSERT INTO customers(name, phone) VALUES(%s,%s) RETURNING id",
                     (name.strip(), phone))["id"]


def list_customers():
    return fetch_all("SELECT * FROM customers ORDER BY name")


def get_customer(cid):
    return fetch_one("SELECT * FROM customers WHERE id=%s", (cid,))


# ======================================================================
# المنتجات
# ======================================================================
_PRODUCT_SELECT = """
SELECT p.id, p.name, p.price, p.cost_price, p.stock, p.min_stock, p.expiry_date, p.image_path,
       p.barcode, c.name AS category_name, s.name AS supplier_name
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN suppliers  s ON s.id = p.supplier_id
"""

_EXPIRING = "p.expiry_date IS NOT NULL AND p.expiry_date <= CURRENT_DATE + 30"


def add_or_update_product(name, price, stock, category, supplier, barcode,
                          cost=0, min_stock=5, expiry=None, image=""):
    """منتج جديد، أو (لو الباركود موجود) تحديث بياناته وزيادة المخزون. ترجع (id, created)."""
    cat_id = add_category(category) if category and category.strip() else None
    sup_id = add_supplier(supplier) if supplier and supplier.strip() else None
    row = fetch_one(
        """INSERT INTO products (name, price, stock, barcode, category_id, supplier_id,
                                 cost_price, min_stock, expiry_date, image_path)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (barcode) DO UPDATE SET
               name = EXCLUDED.name,
               price = EXCLUDED.price,
               stock = products.stock + EXCLUDED.stock,
               category_id = COALESCE(EXCLUDED.category_id, products.category_id),
               supplier_id = COALESCE(EXCLUDED.supplier_id, products.supplier_id),
               cost_price = CASE WHEN EXCLUDED.cost_price > 0 THEN EXCLUDED.cost_price ELSE products.cost_price END,
               min_stock = EXCLUDED.min_stock,
               expiry_date = COALESCE(EXCLUDED.expiry_date, products.expiry_date),
               image_path = COALESCE(NULLIF(EXCLUDED.image_path,''), products.image_path)
           RETURNING id, (xmax = 0) AS created""",
        (name.strip(), price, stock, barcode.strip(), cat_id, sup_id, cost, min_stock, expiry, image or ""))
    return row["id"], row["created"]


def update_product(pid, name, price, stock, barcode, category, supplier, cost, min_stock, expiry, image):
    """تعديل كل بيانات المنتج (الكمية قيمة نهائية وليست زيادة)."""
    cat_id = add_category(category) if category and category.strip() else None
    sup_id = add_supplier(supplier) if supplier and supplier.strip() else None
    try:
        return execute(
            """UPDATE products SET name=%s, price=%s, stock=%s, barcode=%s, category_id=%s, supplier_id=%s,
                      cost_price=%s, min_stock=%s, expiry_date=%s,
                      image_path = COALESCE(NULLIF(%s,''), image_path)
               WHERE id=%s""",
            (name.strip(), price, stock, barcode.strip(), cat_id, sup_id, cost, min_stock, expiry,
             image or "", pid))
    except pg_errors.UniqueViolation:
        raise DuplicateBarcode()


def get_product(pid):
    return fetch_one(_PRODUCT_SELECT + " WHERE p.id = %s", (pid,))


def get_product_by_barcode(barcode):
    return fetch_one(_PRODUCT_SELECT + " WHERE p.barcode = %s AND p.active", (barcode.strip(),))


def list_products(search="", flt="all", limit=500):
    like = f"%{search.strip()}%"
    where = "p.active AND (p.name ILIKE %s OR p.barcode ILIKE %s)"
    if flt == "out":
        where += " AND p.stock = 0"
    elif flt == "low":
        where += " AND p.stock <= p.min_stock"
    elif flt == "expiring":
        where += f" AND {_EXPIRING}"
    return fetch_all(_PRODUCT_SELECT + f" WHERE {where} ORDER BY p.name LIMIT %s", (like, like, limit))


def alert_counts():
    return fetch_one(f"""SELECT COUNT(*) FILTER (WHERE p.stock <= p.min_stock) AS low,
                                COUNT(*) FILTER (WHERE {_EXPIRING}) AS expiring FROM products p WHERE p.active""")


def delete_product(pid):
    """حذف نهائي لو المنتج ملوش تاريخ بيع/شراء، وإلا أرشفة: يختفي من البرنامج وتفضل فواتيره القديمة سليمة."""
    with cursor() as cur:
        cur.execute("""SELECT EXISTS(SELECT 1 FROM order_items WHERE product_id = %(p)s)
                       OR EXISTS(SELECT 1 FROM purchase_items WHERE product_id = %(p)s)
                       OR EXISTS(SELECT 1 FROM return_items WHERE product_id = %(p)s) AS used""", {"p": pid})
        if cur.fetchone()["used"]:
            cur.execute("UPDATE products SET active = FALSE, stock = 0, barcode = barcode || '~del' || id "
                        "WHERE id = %s", (pid,))
            return "archived"
        cur.execute("DELETE FROM products WHERE id = %s", (pid,))
        return "deleted"


# ======================================================================
# الفواتير والمرتجعات
# ======================================================================
def create_order(user_id, customer_id, items, subtotal, discount, vat, total, paid, method="cash"):
    """كل شيء داخل transaction واحدة: الفاتورة + البنود + خصم المخزون + الدين."""
    with cursor() as cur:
        cur.execute(
            "INSERT INTO orders(user_id, customer_id, subtotal, discount, vat, total, paid, payment_method) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (user_id, customer_id, subtotal, discount, vat, total, paid, method))
        order_id = cur.fetchone()["id"]
        for it in items:
            cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s",
                        (it["qty"], it["product_id"], it["qty"]))
            if cur.rowcount == 0:
                raise StockError(it["name"])
            cur.execute(
                "INSERT INTO order_items(order_id, product_id, quantity, unit_price, cost_price, discount) "
                "VALUES(%s,%s,%s,%s,%s,%s)",
                (order_id, it["product_id"], it["qty"], it["price"], it["cost_price"], it["discount"]))
        if customer_id and paid < total:
            cur.execute("INSERT INTO customer_debts(customer_id, order_id, amount) VALUES(%s,%s,%s)",
                        (customer_id, order_id, total - paid))
        return order_id


def get_order(oid):
    return fetch_one(
        """SELECT o.*, c.name AS customer_name, c.phone AS customer_phone, u.username
           FROM orders o LEFT JOIN customers c ON c.id = o.customer_id
           LEFT JOIN users u ON u.id = o.user_id WHERE o.id = %s""", (oid,))


def get_order_items(oid):
    return fetch_all(
        """SELECT oi.id, oi.product_id, COALESCE(p.name,'—') AS name, oi.quantity, oi.unit_price,
                  oi.discount, oi.cost_price,
                  COALESCE((SELECT SUM(ri.quantity) FROM return_items ri WHERE ri.order_item_id = oi.id),0)::int AS returned
           FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = %s ORDER BY oi.id""", (oid,))


def list_orders(search="", limit=200):
    s = search.strip()
    return fetch_all(
        """SELECT o.id, o.created_at, o.total, o.paid, o.payment_method,
                  c.name AS customer, u.username
           FROM orders o LEFT JOIN customers c ON c.id = o.customer_id
           LEFT JOIN users u ON u.id = o.user_id
           WHERE %s = '' OR o.id::text = %s OR c.name ILIKE %s
           ORDER BY o.id DESC LIMIT %s""", (s, s, f"%{s}%", limit))


def create_return(order_id, user_id, lines, amount, vat, method="cash"):
    with cursor() as cur:
        cur.execute("INSERT INTO returns(order_id, user_id, amount, vat, method) VALUES(%s,%s,%s,%s,%s) RETURNING id",
                    (order_id, user_id, amount, vat, method))
        rid = cur.fetchone()["id"]
        for l in lines:
            cur.execute("INSERT INTO return_items(return_id, order_item_id, product_id, quantity, unit_price) "
                        "VALUES(%s,%s,%s,%s,%s)",
                        (rid, l["order_item_id"], l["product_id"], l["qty"], l["unit_refund"]))
            if l["product_id"]:
                cur.execute("UPDATE products SET stock = stock + %s WHERE id = %s", (l["qty"], l["product_id"]))
        return rid


# ======================================================================
# الديون وكشف حساب العميل
# ======================================================================
def get_open_debts():
    return fetch_all(
        """SELECT d.id, d.customer_id, c.name AS customer, c.phone, d.amount, d.paid_amount,
                  d.amount - d.paid_amount AS remaining, d.created_at
           FROM customer_debts d JOIN customers c ON c.id = d.customer_id
           WHERE d.amount > d.paid_amount ORDER BY d.created_at""")


def pay_debt(debt_id, amount, method, user_id):
    """سداد دين جزئي/كامل وتسجيل الدفعة. ترجع المبلغ الفعلي المسدد."""
    with cursor() as cur:
        cur.execute("SELECT customer_id, amount - paid_amount AS rem FROM customer_debts "
                    "WHERE id=%s FOR UPDATE", (debt_id,))
        row = cur.fetchone()
        if not row or row["rem"] <= 0:
            return 0
        pay = min(amount, row["rem"])
        cur.execute("UPDATE customer_debts SET paid_amount = paid_amount + %s WHERE id=%s", (pay, debt_id))
        cur.execute("INSERT INTO debt_payments(debt_id, customer_id, amount, method, user_id) "
                    "VALUES(%s,%s,%s,%s,%s)", (debt_id, row["customer_id"], pay, method, user_id))
        return pay


def customer_orders(cid):
    return fetch_all("SELECT id, created_at, total, paid, payment_method FROM orders "
                     "WHERE customer_id=%s ORDER BY id DESC", (cid,))


def customer_debts(cid):
    return fetch_all("SELECT id, amount, paid_amount, amount - paid_amount AS remaining, created_at "
                     "FROM customer_debts WHERE customer_id=%s ORDER BY created_at DESC", (cid,))


def customer_payments(cid):
    return fetch_all("SELECT created_at, amount, method FROM debt_payments "
                     "WHERE customer_id=%s ORDER BY id DESC", (cid,))


# ======================================================================
# فواتير الشراء من الموردين
# ======================================================================
def create_purchase(supplier_id, user_id, items, total, paid):
    """زيادة المخزون تلقائيًا + تحديث سعر الشراء + ربط المنتج بالمورد."""
    with cursor() as cur:
        cur.execute("INSERT INTO purchases(supplier_id, user_id, total, paid) VALUES(%s,%s,%s,%s) RETURNING id",
                    (supplier_id, user_id, total, paid))
        pid = cur.fetchone()["id"]
        for it in items:
            cur.execute("INSERT INTO purchase_items(purchase_id, product_id, quantity, cost_price) "
                        "VALUES(%s,%s,%s,%s)", (pid, it["product_id"], it["qty"], it["cost"]))
            cur.execute("UPDATE products SET stock = stock + %s, cost_price = %s, supplier_id = %s WHERE id = %s",
                        (it["qty"], it["cost"], supplier_id, it["product_id"]))
        return pid


def list_purchases(limit=100):
    return fetch_all("SELECT pu.id, pu.created_at, s.name AS supplier, pu.total, pu.paid "
                     "FROM purchases pu LEFT JOIN suppliers s ON s.id = pu.supplier_id "
                     "ORDER BY pu.id DESC LIMIT %s", (limit,))


# ======================================================================
# تقارير المبيعات (since = بداية الفترة أو None)
# ======================================================================
_SO = "(%s::timestamptz IS NULL OR o.created_at >= %s)"
_SR = "(%s::timestamptz IS NULL OR r.created_at >= %s)"


def sales_summary(since):
    return fetch_one(
        f"""SELECT COUNT(*) AS orders, COALESCE(SUM(o.total),0) AS revenue, COALESCE(SUM(o.vat),0) AS vat,
                   COALESCE(SUM(o.paid),0) AS collected, COALESCE(SUM(o.total - o.paid),0) AS outstanding
            FROM orders o WHERE {_SO}""", (since, since))


def cogs(since):
    return fetch_one(
        f"""SELECT COALESCE(SUM(oi.quantity * oi.cost_price),0) AS cogs FROM order_items oi
            JOIN orders o ON o.id = oi.order_id WHERE {_SO}""", (since, since))["cogs"]


def returns_summary(since):
    row = fetch_one(f"SELECT COALESCE(SUM(r.amount),0) AS amount, COALESCE(SUM(r.vat),0) AS vat "
                    f"FROM returns r WHERE {_SR}", (since, since))
    row["cogs"] = fetch_one(
        f"""SELECT COALESCE(SUM(ri.quantity * oi.cost_price),0) AS c FROM return_items ri
            JOIN returns r ON r.id = ri.return_id JOIN order_items oi ON oi.id = ri.order_item_id
            WHERE {_SR}""", (since, since))["c"]
    return row


def sales_by_day(since, offset):
    return fetch_all(
        f"""SELECT ((o.created_at AT TIME ZONE 'UTC') + %s)::date AS day, COUNT(*) AS orders,
                   SUM(o.total) AS revenue FROM orders o WHERE {_SO} GROUP BY 1 ORDER BY 1 DESC""",
        (offset, since, since))


def top_products(since, limit=10):
    return fetch_all(
        f"""SELECT COALESCE(p.name,'—') AS name, SUM(oi.quantity) AS qty,
                   SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
            FROM order_items oi JOIN orders o ON o.id = oi.order_id
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE {_SO} GROUP BY oi.product_id, p.name ORDER BY qty DESC LIMIT %s""", (since, since, limit))


def sales_by_user(since):
    return fetch_all(
        f"""SELECT COALESCE(u.username,'—') AS username, COUNT(*) AS orders, SUM(o.total) AS revenue
            FROM orders o LEFT JOIN users u ON u.id = o.user_id WHERE {_SO}
            GROUP BY u.username ORDER BY revenue DESC""", (since, since))


def sales_by_method(since):
    return fetch_all(
        f"""SELECT o.payment_method AS method, COUNT(*) AS orders, SUM(o.paid) AS collected
            FROM orders o WHERE {_SO} GROUP BY 1 ORDER BY 3 DESC""", (since, since))


# ======================================================================
# الورديات
# ======================================================================
def last_shift_close(user_id):
    return fetch_one("SELECT MAX(closed_at) AS t FROM shifts WHERE user_id=%s", (user_id,))["t"]


def shift_totals(user_id, since):
    q = ("SELECT method, COALESCE(SUM(amount),0) AS amount FROM {t} "
         "WHERE user_id=%s AND created_at >= %s GROUP BY method")
    sales = fetch_all("SELECT payment_method AS method, COALESCE(SUM(paid),0) AS amount FROM orders "
                      "WHERE user_id=%s AND created_at >= %s GROUP BY 1", (user_id, since))
    debts = fetch_all(q.format(t="debt_payments"), (user_id, since))
    refunds = fetch_all(q.format(t="returns"), (user_id, since))
    return sales, debts, refunds


def close_shift(user_id, username, period_start, expected, counted, diff, note):
    return execute("INSERT INTO shifts(user_id, username, period_start, expected_cash, counted_cash, "
                   "difference, note) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                   (user_id, username, period_start, expected, counted, diff, note))


# ======================================================================
# المستخدمون
# ======================================================================
def create_user(username, password_hash, role):
    return fetch_one("INSERT INTO users(username, password_hash, role) VALUES(%s,%s,%s) RETURNING id",
                     (username.strip(), password_hash, role))["id"]


def get_user(username):
    return fetch_one("SELECT * FROM users WHERE username = %s", (username.strip(),))


def list_users():
    return fetch_all("SELECT id, username, role FROM users ORDER BY role, username")


def count_users():
    return fetch_one("SELECT COUNT(*) AS n FROM users")["n"]


def update_user_password(username, password_hash):
    return execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))


def set_user_role(username, role):
    return execute("UPDATE users SET role = %s WHERE username = %s", (role, username))


def count_admins():
    return fetch_one("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'")["n"]


def delete_user(username):
    return execute("DELETE FROM users WHERE username = %s AND role <> 'admin'", (username,))


# ======================================================================
# النسخ الاحتياطي والتصدير
# ======================================================================
def dump_sql(f):
    """يكتب كل البيانات كأوامر INSERT (تُستعاد على داتابيز جديدة بعد تشغيل البرنامج مرة)."""
    with cursor() as cur:
        for t in TABLES:
            cur.execute(f"SELECT * FROM {t} ORDER BY 1")
            rows = cur.fetchall()
            if not rows:
                continue
            cols = list(rows[0].keys())
            sql = f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))}) ON CONFLICT DO NOTHING;\n"
            for r in rows:
                f.write(cur.mogrify(sql, [r[c] for c in cols]).decode("utf-8"))
            if t != "settings":
                f.write(f"SELECT setval(pg_get_serial_sequence('{t}','id'), "
                        f"COALESCE((SELECT MAX(id) FROM {t}),1));\n")


EXPORTS = {
    "products": """SELECT p.barcode, p.name, p.price, p.cost_price, p.stock, p.min_stock, p.expiry_date,
                          c.name AS category, s.name AS supplier FROM products p
                   LEFT JOIN categories c ON c.id = p.category_id LEFT JOIN suppliers s ON s.id = p.supplier_id
                   WHERE p.active ORDER BY p.name""",
    "orders": """SELECT o.id, o.created_at, c.name AS customer, u.username AS cashier, o.subtotal, o.discount,
                        o.vat, o.total, o.paid, o.payment_method FROM orders o
                 LEFT JOIN customers c ON c.id = o.customer_id LEFT JOIN users u ON u.id = o.user_id ORDER BY o.id""",
    "order_items": """SELECT oi.order_id, p.name AS product, oi.quantity, oi.unit_price, oi.discount, oi.cost_price
                      FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id ORDER BY oi.order_id""",
    "customers": """SELECT c.name, c.phone, COALESCE(SUM(d.amount - d.paid_amount),0) AS debt FROM customers c
                    LEFT JOIN customer_debts d ON d.customer_id = c.id GROUP BY c.id ORDER BY c.name""",
    "purchases": """SELECT pu.id, pu.created_at, s.name AS supplier, pu.total, pu.paid FROM purchases pu
                    LEFT JOIN suppliers s ON s.id = pu.supplier_id ORDER BY pu.id""",
}


def export_queries():
    for name, sql in EXPORTS.items():
        rows = fetch_all(sql)
        yield name, (list(rows[0].keys()) if rows else []), rows
