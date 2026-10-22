"""
gui.py - واجهة جو شوب (CustomTkinter - Dark Mode - عربي / English)
التشغيل:  python gui.py
"""
import threading
import tkinter as tk
import webbrowser
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image

import logic

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT = ("Segoe UI", 14)
FONT_B = ("Segoe UI", 14, "bold")

# ======================================================================
# الترجمة: المفتاح -> (English, العربية)
# ======================================================================
T = {
    "title": ("Go Shop POS", "جو شوب - نقاط البيع"), "username": ("Username", "اسم المستخدم"),
    "password": ("Password", "كلمة المرور"), "login": ("Login", "دخول"), "logout": ("Logout", "تسجيل خروج"),
    "lang_btn": ("العربية", "English"), "cashier": ("Cashier", "الكاشير"), "inventory": ("Inventory", "المخزون"),
    "invoices": ("Invoices", "الفواتير"), "debts": ("Debts", "الديون"), "shift": ("Shift", "الوردية"),
    "sup_tab": ("Suppliers", "الموردين"), "reports": ("Reports", "التقارير"), "activity": ("Activity", "السجل"),
    "settings": ("Settings", "الإعدادات"), "info": ("Info", "تنبيه"), "error": ("Error", "خطأ"),
    "scan": ("Scan barcode or type product name, then Enter", "اضرب الباركود أو اكتب اسم المنتج ثم Enter"),
    "add": ("Add", "إضافة"), "barcode": ("Barcode", "الباركود"), "name": ("Name", "الاسم"),
    "price": ("Price", "السعر"), "qty": ("Qty", "الكمية"), "discount": ("Discount", "الخصم"),
    "subtotal": ("Subtotal", "الإجمالي الفرعي"), "total": ("Total", "الإجمالي"), "vat": ("VAT", "الضريبة"),
    "disc_hint": ("Discount: 10% or amount", "خصم: 10% أو مبلغ"), "remove": ("Remove", "حذف"),
    "clear": ("Clear", "مسح"), "hold": ("Hold", "تعليق"), "resume": ("Resume", "استرجاع"),
    "no_held": ("No held invoices", "لا توجد فواتير معلقة"), "held_items": ("Items", "الأصناف"),
    "customer": ("Customer", "العميل"), "no_customer": ("— Walk-in —", "— عميل نقدي —"),
    "new_customer": ("+ Customer", "+ عميل"), "customer_name": ("Customer name", "اسم العميل"),
    "customer_phone": ("Phone (optional)", "الموبايل (اختياري)"), "phone": ("Phone", "الموبايل"),
    "pay_method": ("Payment method", "طريقة الدفع"), "pm_cash": ("Cash", "كاش"), "pm_visa": ("Visa", "فيزا"),
    "pm_vodafone": ("Vodafone Cash", "فودافون كاش"), "paid": ("Paid (blank = full)", "المدفوع (فاضي = كامل)"),
    "paid_short": ("Paid", "المدفوع"), "checkout": ("Checkout", "إتمام البيع"),
    "print_receipt": ("Print receipt", "طباعة الفاتورة"), "order_no": ("Invoice #", "فاتورة رقم"),
    "change": ("Change", "الباقي للعميل"), "remaining": ("Remaining", "المتبقي"),
    # المخزون
    "cost_price": ("Cost price", "سعر الشراء"), "init_qty": ("Initial / added qty", "الكمية المبدئية / المضافة"),
    "stock": ("Stock", "المخزون"), "min_stock": ("Min stock", "الحد الأدنى"),
    "expiry": ("Expiry (YYYY-MM-DD)", "الصلاحية (YYYY-MM-DD)"), "category": ("Category", "التصنيف"),
    "supplier": ("Supplier", "المورد"), "image": ("Image", "الصورة"), "save": ("Save", "حفظ"),
    "save_product": ("Save product", "حفظ المنتج"), "created": ("Product added", "تمت إضافة المنتج"),
    "updated": ("Product exists: stock increased", "المنتج موجود: تمت زيادة المخزون"),
    "search": ("Search by name or barcode...", "بحث بالاسم أو الباركود..."), "flt_all": ("All", "الكل"),
    "search_btn": ("Search", "بحث"), "act_search": ("Search activity...", "بحث في السجل..."),
    "flt_out": ("Sold out", "خلصان"), "promote": ("Promote to admin", "ترقية لأدمن"),
    "demote": ("Demote to employee", "تنزيل لموظف"),
    "role_changed": ("Role updated (takes effect at next login)", "تم تغيير الصلاحية (تسري عند الدخول التالي)"),
    "cant_delete_admin": ("The admin account cannot be deleted", "حساب الأدمن لا يمكن حذفه"),
    "last_admin": ("At least one admin must remain", "لازم يفضل أدمن واحد على الأقل"),
    "cant_demote_self": ("You cannot demote yourself", "لا يمكنك تنزيل صلاحيتك أنت"),
    "confirm_delete_product": ("Delete the selected product(s)? They will disappear from the cashier and inventory; old invoices stay intact.",
                               "حذف المنتج المحدد؟ هيختفي من الكاشير والمخزون، والفواتير القديمة بتفضل زي ما هي."),
    "product_deleted": ("Product deleted", "تم حذف المنتج"),
    "product_archived": ("Product removed (it has sales history, so old invoices are kept)",
                         "تم حذف المنتج، والفواتير القديمة بتاعته محفوظة"),
    "act_role_change": ("Role changed", "تغيير صلاحية"),
    "flt_low": ("Low stock", "ناقص"), "flt_expiring": ("Expiring", "قرب الانتهاء"),
    "edit_product": ("Edit product", "تعديل المنتج"), "edit_selected": ("Edit selected", "تعديل المحدد"),
    "delete_product": ("Delete product", "حذف المنتج"), "confirm_delete": ("Delete permanently?", "حذف نهائيًا؟"),
    "saved_changes": ("Changes saved", "تم حفظ التعديلات"), "labels": ("Print labels", "طباعة ملصقات"),
    "copies": ("Copies per product", "عدد النسخ لكل منتج"), "pick_product": ("Select product", "اختار المنتج"),
    "exists_hint": ("Existing product loaded - quantity will be ADDED", "المنتج موجود - الكمية هتتضاف على المخزون"),
    "alert_low": ("Low stock", "ناقص"), "alert_exp": ("Expiring", "قرب انتهاء"),
    "select_row": ("Select a row first", "اختار صف الأول"),
    # الفواتير والمرتجعات
    "inv_search": ("Invoice # or customer", "رقم الفاتورة أو العميل"), "date": ("Date", "التاريخ"),
    "invoice": ("Invoice", "فاتورة"), "details": ("Details / Return", "تفاصيل / مرتجع"),
    "order_details": ("Invoice details", "تفاصيل الفاتورة"), "returned": ("Returned", "المرتجع"),
    "do_return": ("Return selected", "ارتجاع المحدد"), "refunded": ("Refunded", "تم رد"),
    "whatsapp": ("WhatsApp", "واتساب"), "wa_invoice_intro": ("Thank you for shopping at", "شكراً لتسوقك من"),
    # الديون
    "total_debts": ("Total debts", "إجمالي الديون"), "debt_amount": ("Debt", "الدين"),
    "paid_so_far": ("Paid", "المدفوع"), "pay": ("Collect", "تسديد"),
    "pay_amount": ("Amount (blank = all)", "المبلغ (فاضي = الكل)"), "pay_ok": ("Payment recorded", "تم تسجيل السداد"),
    "statement": ("Statement", "كشف حساب"), "total_bought": ("Total purchases", "إجمالي المشتريات"),
    "payments": ("Payments", "المدفوعات"), "reminder": ("WhatsApp reminder", "تذكير واتساب"),
    "wa_debt": ("Hello {name}, a friendly reminder: your balance at {shop} is {amount}. Thank you.",
                "أهلاً {name}، تذكير بسيط: المبلغ المستحق عليك لدى {shop} هو {amount}. شكراً لك."),
    "pick_customer": ("Select customer", "اختار عميل"),
    # الوردية
    "shift_since": ("Shift started", "بداية الوردية"), "sales_by": ("Sales", "مبيعات"),
    "debt_collected": ("Debt collections", "تحصيل ديون"), "refunds": ("Refunds", "مرتجعات"),
    "expected_cash": ("Expected cash in drawer", "المفروض في الدرج (كاش)"),
    "counted_cash": ("Counted cash", "الكاش الفعلي"), "note": ("Note", "ملاحظة"),
    "close_shift": ("Close shift", "تقفيل الوردية"), "difference": ("Difference", "الفرق"),
    "shift_closed": ("Shift closed", "تم تقفيل الوردية"),
    # الموردين
    "suppliers": ("Suppliers", "الموردين"), "purchases": ("Purchase invoices", "فواتير الشراء"),
    "categories": ("Categories", "التصنيفات"), "total_purchased": ("Purchased", "إجمالي المشتريات"),
    "owed": ("Owed", "مستحق للمورد"), "new": ("New", "جديد"), "delete": ("Delete", "حذف"),
    "cost": ("Cost", "التكلفة"), "save_purchase": ("Save purchase", "حفظ فاتورة الشراء"),
    "purchase_saved": ("Purchase saved, stock updated", "تم الحفظ وزاد المخزون"),
    "products_count": ("Products", "المنتجات"), "pay_supplier": ("Paid to supplier (blank = full)", "المدفوع للمورد (فاضي = كامل)"),
    # التقارير
    "period_today": ("Today", "اليوم"), "period_7d": ("7 days", "7 أيام"), "period_30d": ("30 days", "30 يوم"),
    "period_all": ("All time", "الكل"), "orders_count": ("Invoices", "عدد الفواتير"),
    "sales": ("Net sales", "صافي المبيعات"), "returns": ("Returns", "المرتجعات"), "profit": ("Profit", "الأرباح"),
    "collected": ("Collected", "المحصّل"), "outstanding": ("Outstanding", "ديون متبقية"),
    "daily_sales": ("Daily sales", "المبيعات اليومية"), "top_products": ("Top products (qty)", "الأكثر مبيعًا (كمية)"),
    "by_method": ("By payment method", "حسب طريقة الدفع"), "by_employee": ("By employee", "حسب الموظف"),
    "export": ("Export Excel (CSV)", "تصدير Excel (CSV)"), "exported": ("Exported to", "تم التصدير إلى"),
    "revenue": ("Sales", "المبيعات"), "cashier_col": ("Cashier", "الكاشير"), "method": ("Method", "الطريقة"),
    "action": ("Action", "العملية"), "details_col": ("Details", "التفاصيل"), "time": ("Time", "الوقت"),
    # الإعدادات
    "users": ("Users", "المستخدمون"), "role": ("Role", "الصلاحية"), "admin": ("Admin", "أدمن"),
    "employee": ("Employee", "موظف"), "new_password": ("New password", "كلمة مرور جديدة"),
    "change_password": ("Change password", "تغيير كلمة المرور"), "add_employee": ("Add employee", "إضافة موظف"),
    "delete_selected": ("Delete selected", "حذف المحدد"), "pw_changed": ("Password changed", "تم تغيير كلمة المرور"),
    "emp_added": ("Employee added", "تمت إضافة الموظف"), "emp_deleted": ("Employee deleted", "تم حذف الموظف"),
    "shop_settings": ("Shop & receipt settings", "إعدادات المحل والفاتورة"), "shop_name": ("Shop name", "اسم المحل"),
    "shop_address": ("Address", "العنوان"), "shop_phone": ("Shop phone", "تليفون المحل"),
    "vat_rate": ("VAT % (0 = none)", "الضريبة % (0 = بدون)"), "country_code": ("Country code (WhatsApp)", "كود الدولة (واتساب)"),
    "logo": ("Logo", "اللوجو"), "backup_dir": ("Backup folder", "مجلد النسخ الاحتياطي"),
    "auto_print": ("Print receipt automatically", "طباعة الفاتورة تلقائيًا بعد البيع"),
    "settings_saved": ("Settings saved", "تم حفظ الإعدادات"), "backup_now": ("Backup now (SQL)", "نسخة احتياطية الآن (SQL)"),
    "backup_done": ("Backup saved", "تم حفظ النسخة"), "browse": ("Browse", "استعراض"),
    # الإيصال
    "thanks": ("Thank you!", "شكراً لزيارتكم"),
    # الأخطاء
    "bad_login": ("Wrong username or password", "اسم المستخدم أو كلمة المرور غلط"),
    "not_found": ("Not found", "غير موجود"), "out_of_stock": ("Not enough stock", "الكمية في المخزن غير كافية"),
    "invalid_number": ("Invalid number", "رقم غير صحيح"), "invalid_date": ("Invalid date (YYYY-MM-DD)", "تاريخ غير صحيح (YYYY-MM-DD)"),
    "empty_fields": ("Please fill the required fields", "من فضلك املأ الحقول المطلوبة"),
    "empty_cart": ("Nothing to process", "لا يوجد شيء للتنفيذ"),
    "debt_needs_customer": ("Select a customer to record the remaining amount as debt", "اختار عميل لتسجيل المتبقي كدين"),
    "short_password": ("Password is too short (min 4)", "كلمة المرور قصيرة (4 على الأقل)"),
    "user_exists": ("Username already exists", "اسم المستخدم موجود بالفعل"), "forbidden": ("Admin only", "للأدمن فقط"),
    "cant_delete": ("Cannot delete this user", "لا يمكن حذف هذا المستخدم"),
    "barcode_exists": ("Barcode belongs to another product", "الباركود تابع لمنتج تاني"),
    "return_too_many": ("Return quantity exceeds sold quantity", "كمية المرتجع أكبر من المباعة"),
    "no_phone": ("No valid phone number", "لا يوجد رقم موبايل صحيح"), "many_matches": ("Several matches: use the barcode", "أكتر من منتج مطابق: استخدم الباركود"),
    "pick_supplier": ("Select a supplier", "اختار المورد"), "bad_file": ("File not found", "الملف غير موجود"),
    # سجل النشاط
    "act_login": ("Login", "دخول"), "act_sale": ("Sale", "بيع"), "act_product_add": ("Product added", "إضافة منتج"),
    "act_product_restock": ("Restock", "زيادة مخزون"), "act_product_edit": ("Product edited", "تعديل منتج"),
    "act_product_delete": ("Product deleted", "حذف منتج"), "act_return": ("Return", "مرتجع"),
    "act_debt_payment": ("Debt payment", "سداد دين"), "act_purchase": ("Purchase", "فاتورة شراء"),
    "act_shift_close": ("Shift closed", "تقفيل وردية"), "act_password_change": ("Password changed", "تغيير باسورد"),
    "act_employee_add": ("Employee added", "إضافة موظف"), "act_employee_delete": ("Employee deleted", "حذف موظف"),
    "act_settings": ("Settings", "إعدادات"), "act_backup": ("Backup", "نسخة احتياطية"), "act_export": ("Export", "تصدير"),
}

RECEIPT_KEYS = ["invoice", "cashier", "customer", "subtotal", "discount", "vat", "total", "paid",
                "remaining", "change", "thanks"]


# ======================================================================
# رسم بياني بسيط (Canvas) مع Tooltip عند المرور بالماوس
# ======================================================================
class BarChart(tk.Canvas):
    def __init__(self, master, color="#4a90d9", horizontal=False, height=210):
        super().__init__(master, bg="#2b2b2b", highlightthickness=0, height=height)
        self.color, self.horizontal = color, horizontal
        self.labels, self.values, self.rects = [], [], []
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Motion>", self.hover)

    def set_data(self, labels, values):
        self.labels, self.values = list(labels), [float(v) for v in values]
        self.draw()

    def draw(self):
        self.delete("all")
        self.rects = []
        w, h, n = self.winfo_width(), self.winfo_height(), len(self.values)
        mx = max(self.values, default=0)
        if n == 0 or mx <= 0 or w < 60:
            return
        if not self.horizontal:
            pl, pb, pt = 10, 24, 20
            slot = (w - 2 * pl) / n
            bw = min(slot * 0.7, 60)
            for i, v in enumerate(self.values):
                x0 = pl + i * slot + (slot - bw) / 2
                y0 = h - pb - (h - pb - pt) * v / mx
                self.create_rectangle(x0, y0, x0 + bw, h - pb, fill=self.color, width=0)
                self.create_text(x0 + bw / 2, y0 - 9, text=f"{v:.0f}", fill="#ccc", font=("Segoe UI", 9))
                self.create_text(x0 + bw / 2, h - 11, text=self.labels[i], fill="#aaa", font=("Segoe UI", 9))
                self.rects.append((x0, y0, x0 + bw, h - pb, i))
        else:
            pl, pr = 120, 50
            slot = (h - 10) / n
            bh = min(slot * 0.7, 24)
            for i, v in enumerate(self.values):
                y0 = 5 + i * slot + (slot - bh) / 2
                x1 = pl + (w - pl - pr) * v / mx
                self.create_text(pl - 6, y0 + bh / 2, text=self.labels[i], fill="#ccc", anchor="e",
                                 font=("Segoe UI", 10))
                self.create_rectangle(pl, y0, x1, y0 + bh, fill=self.color, width=0)
                self.create_text(x1 + 6, y0 + bh / 2, text=f"{v:.0f}", fill="#ccc", anchor="w", font=("Segoe UI", 9))
                self.rects.append((pl, y0, x1, y0 + bh, i))

    def hover(self, e):
        self.delete("tip")
        for x0, y0, x1, y1, i in self.rects:
            if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                txt = f"{self.labels[i]}: {self.values[i]:,.2f}"
                tx = min(e.x + 12, max(self.winfo_width() - 150, 0))
                t = self.create_text(tx, max(e.y - 14, 10), text=txt, anchor="w", fill="white", tags="tip")
                bx = self.bbox(t)
                bg = self.create_rectangle(bx[0] - 4, bx[1] - 2, bx[2] + 4, bx[3] + 2, fill="#111", outline="#555", tags="tip")
                self.tag_raise(t, bg)
                return


# ======================================================================
# التطبيق
# ======================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1320x800")
        self.minsize(1100, 650)
        self.lang, self.user = "ar", None
        self.cart, self.held = logic.Cart(), []
        self.blank_img = ctk.CTkImage(Image.new("RGBA", (96, 96), (60, 60, 60, 255)), size=(96, 96))
        self._backup_job = None
        self._style_tree()
        try:
            logic.bootstrap()
        except Exception as e:
            messagebox.showerror("Database", f"{e}")
        self.show_login()

    # ------------------------------------------------------------ helpers
    def t(self, key):
        v = T.get(key)
        return v[0 if self.lang == "en" else 1] if v else key

    @property
    def rtl(self):
        return self.lang == "ar"

    @property
    def anc(self):
        return "e" if self.rtl else "w"

    @property
    def just(self):
        return "right" if self.rtl else "left"

    def side(self, primary=True):
        a, b = ("right", "left") if self.rtl else ("left", "right")
        return a if primary else b

    def app_title(self):
        name = logic.settings().get("shop_name", "")
        return self.t("title") if name in ("", "Go Shop", "Go Shop") else f"{name} POS"

    def err(self, e):
        code = e.code if isinstance(e, logic.POSError) else None
        messagebox.showerror(self.t("error"), self.t(code) if code else str(e))

    def info(self, key):
        messagebox.showinfo(self.t("info"), self.t(key))

    def popup(self, title_key, w, h):
        win = ctk.CTkToplevel(self)
        win.title(self.t(title_key))
        win.geometry(f"{w}x{h}")
        win.transient(self)
        win.after(200, win.grab_set)
        return win

    def clear_window(self):
        for w in self.winfo_children():
            w.destroy()

    def toggle_lang(self):
        self.lang = "en" if self.lang == "ar" else "ar"
        self.build_main() if self.user else self.show_login()

    def _style_tree(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b",
                    rowheight=30, borderwidth=0, font=("Segoe UI", 12))
        s.configure("Treeview.Heading", background="#1f538d", foreground="white",
                    font=("Segoe UI", 12, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", "#1f538d")])

    def make_tree(self, parent, cols, height=10):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        tree = ttk.Treeview(wrap, columns=[c[0] for c in cols], show="headings", height=height)
        for cid, key, width in cols:
            tree.heading(cid, text=self.t(key))
            tree.column(cid, width=width, anchor="center")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        tree.tag_configure("low", foreground="#ff6b6b")
        tree.tag_configure("exp", foreground="#ffb347")
        return wrap, tree

    def entry(self, parent, placeholder="", show=None, width=200):
        return ctk.CTkEntry(parent, placeholder_text=placeholder, show=show, height=40, width=width,
                            font=FONT, justify=self.just)

    def btn(self, parent, key, cmd, width=110, **kw):
        kw.setdefault("height", 38)
        kw.setdefault("font", FONT)
        return ctk.CTkButton(parent, text=self.t(key), command=cmd, width=width, **kw)

    def label(self, parent, key, **kw):
        return ctk.CTkLabel(parent, text=self.t(key), font=kw.pop("font", FONT), anchor=self.anc, **kw)

    def combo(self, parent, values, width=200):
        return ctk.CTkComboBox(parent, values=values or [""], height=40, width=width, font=FONT, justify=self.just)

    def method_combo(self, parent, width=170):
        c = ctk.CTkComboBox(parent, values=[self.t("pm_" + m) for m in logic.PAYMENT_METHODS], height=40,
                            width=width, font=FONT, state="readonly")
        c.set(self.t("pm_cash"))
        return c

    def method_of(self, combo):
        return {self.t("pm_" + m): m for m in logic.PAYMENT_METHODS}.get(combo.get(), "cash")

    @staticmethod
    def _set(w, value):
        if isinstance(w, ctk.CTkComboBox):
            w.set(value)
        else:
            w.delete(0, "end")
            w.insert(0, value)

    @staticmethod
    def fmt_dt(dt):
        return dt.astimezone().strftime("%Y-%m-%d %H:%M") if dt else ""

    def sel_id(self, tree, silent=False):
        sel = tree.selection()
        if not sel and not silent:
            self.info("select_row")
        return int(sel[0]) if sel else None

    def receipt_labels(self):
        L = {k: self.t(k) for k in RECEIPT_KEYS}
        L["cashier"] = self.t("cashier_col")
        L["dir"] = "rtl" if self.rtl else "ltr"
        return L

    # -------------------------------------------------------------- login
    def show_login(self):
        if self._backup_job:
            self.after_cancel(self._backup_job)
            self._backup_job = None
        self.user = None
        self.clear_window()
        self.title(self.app_title())
        box = ctk.CTkFrame(self, corner_radius=16)
        box.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(box, text="🛒 " + self.app_title(), font=("Segoe UI", 26, "bold")).pack(padx=60, pady=(30, 20))
        u = self.entry(box, self.t("username"), width=280)
        u.pack(pady=6, padx=30)
        p = self.entry(box, self.t("password"), show="•", width=280)
        p.pack(pady=6, padx=30)

        def do_login(_=None):
            try:
                self.user = logic.login(u.get(), p.get())
            except Exception as e:
                self.err(e)
                return
            self.build_main()
            if self.user["role"] == "admin":
                self.schedule_backup()

        p.bind("<Return>", do_login)
        u.bind("<Return>", lambda e: p.focus())
        ctk.CTkButton(box, text=self.t("login"), height=42, font=FONT_B, command=do_login).pack(
            pady=(14, 6), padx=30, fill="x")
        ctk.CTkButton(box, text=self.t("lang_btn"), height=34, fg_color="transparent", border_width=1,
                      command=self.toggle_lang).pack(pady=(0, 24), padx=30, fill="x")
        u.focus()

    def schedule_backup(self):
        """نسخة احتياطية تلقائية: عند دخول الأدمن (لو مر 24 ساعة) ثم كل 6 ساعات."""
        if not self.user or self.user["role"] != "admin":
            return

        def work():
            try:
                logic.auto_backup_if_due()
            except Exception:
                pass

        threading.Thread(target=work, daemon=True).start()
        self._backup_job = self.after(6 * 3600 * 1000, self.schedule_backup)

    # --------------------------------------------------------------- main
    def build_main(self):
        self.clear_window()
        self.__dict__.pop("debt_cust_box", None)  # ويدجت قديمة بعد تبديل اللغة
        self.title(self.app_title())
        header = ctk.CTkFrame(self, height=54)
        header.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(header, text="🛒 " + self.app_title(), font=("Segoe UI", 20, "bold")).pack(side=self.side(), padx=14)
        self.alert_lbl = ctk.CTkLabel(header, text="", font=FONT_B, text_color="#ff9f43")
        self.alert_lbl.pack(side=self.side(), padx=20)
        ctk.CTkButton(header, text=self.t("logout"), width=100, fg_color="#8b2e2e", hover_color="#a33",
                      command=self.show_login).pack(side=self.side(False), padx=8, pady=8)
        ctk.CTkButton(header, text=self.t("lang_btn"), width=100, command=self.toggle_lang).pack(
            side=self.side(False), padx=4, pady=8)
        role = self.t("admin") if self.user["role"] == "admin" else self.t("employee")
        ctk.CTkLabel(header, text=f"👤 {self.user['username']} ({role})", font=FONT).pack(
            side=self.side(False), padx=14)

        admin = self.user["role"] == "admin"
        spec = [("cashier", self.build_cashier, 0), ("inventory", self.build_inventory, 0),
                ("invoices", self.build_invoices, 0), ("debts", self.build_debts, 0),
                ("shift", self.build_shift, 0), ("sup_tab", self.build_suppliers, 1),
                ("reports", self.build_reports, 1), ("activity", self.build_activity, 1),
                ("settings", self.build_settings, 1)]
        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_keys = {}
        for key, builder, adm in spec:
            if adm and not admin:
                continue
            self.tab_keys[self.t(key)] = key
            builder(self.tabs.add(self.t(key)))
        self.tabs.set(self.t("cashier"))
        self.refresh_alerts()
        self.scan.focus()

    def on_tab_change(self):
        key = self.tab_keys.get(self.tabs.get())
        actions = {
            "cashier": lambda: (self.reload_customers(), self.refresh_alerts(), self.scan.focus()),
            "inventory": lambda: (self.refresh_products(), self.refresh_alerts()),
            "invoices": self.refresh_invoices, "debts": self.refresh_debts, "shift": self.refresh_shift,
            "sup_tab": self.refresh_suppliers_all, "reports": self.refresh_report,
            "activity": self.refresh_activity,
        }
        if key in actions:
            actions[key]()

    def refresh_alerts(self):
        try:
            c = logic.alert_counts()
        except Exception:
            return
        parts = []
        if c["low"]:
            parts.append(f"⚠ {self.t('alert_low')}: {c['low']}")
        if c["expiring"]:
            parts.append(f"⏳ {self.t('alert_exp')}: {c['expiring']}")
        self.alert_lbl.configure(text="   ".join(parts))

    # ============================================================ الكاشير
    def build_cashier(self, tab):
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(side=self.side(), fill="both", expand=True, padx=6)
        panel = ctk.CTkScrollableFrame(tab, width=330)
        panel.pack(side=self.side(False), fill="y", padx=6)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))
        self.scan = self.entry(top, self.t("scan"), width=400)
        self.scan.configure(height=46)
        self.scan.pack(side=self.side(), fill="x", expand=True)
        self.scan.bind("<Return>", self.on_scan)
        self.btn(top, "add", self.on_scan, 90, height=46, font=FONT_B).pack(side=self.side(), padx=6)

        cols = [("name", "name", 240), ("price", "price", 80), ("qty", "qty", 60),
                ("disc", "discount", 80), ("sub", "subtotal", 100)]
        wrap, self.cart_tree = self.make_tree(main, cols, 6)
        wrap.pack(fill="both", expand=True)
        self.cart_tree.bind("<<TreeviewSelect>>", self.on_cart_select)

        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.pack(fill="x", pady=8)
        for key, cmd, w in (("＋", lambda: self.cart_delta(1), 50), ("－", lambda: self.cart_delta(-1), 50),
                            ("discount", self.cart_discount, 90), ("remove", self.cart_remove, 80),
                            ("clear", self.cart_clear, 80), ("hold", self.hold_cart, 80)):
            self.btn(bar, key, cmd, w).pack(side=self.side(), padx=3)
        self.resume_btn = self.btn(bar, "resume", self.resume_cart, 110, fg_color="#6b4fa0")
        self.resume_btn.pack(side=self.side(), padx=3)

        self.img_lbl = ctk.CTkLabel(panel, text="", image=self.blank_img, width=96, height=96)
        self.img_lbl.pack(pady=(6, 8))
        self.sub_lbl = self.stat_row(panel, "subtotal")
        ctk.CTkLabel(panel, text=self.t("disc_hint"), font=("Segoe UI", 12), anchor=self.anc).pack(fill="x", padx=12)
        self.disc_entry = self.entry(panel, "")
        self.disc_entry.pack(fill="x", padx=12, pady=(0, 6))
        self.disc_entry.bind("<KeyRelease>", lambda e: self.refresh_totals())
        self.vat_lbl = self.stat_row(panel, "vat")
        ctk.CTkLabel(panel, text=self.t("total"), font=FONT_B).pack(pady=(8, 0))
        self.total_lbl = ctk.CTkLabel(panel, text="0.00", font=("Segoe UI", 38, "bold"), text_color="#4cc38a")
        self.total_lbl.pack(pady=(0, 8))

        self.label(panel, "customer").pack(fill="x", padx=12)
        crow = ctk.CTkFrame(panel, fg_color="transparent")
        crow.pack(fill="x", padx=12, pady=(0, 6))
        self.cust_box = ctk.CTkComboBox(crow, values=[""], height=40, font=FONT, state="readonly", width=190)
        self.cust_box.pack(side=self.side(), fill="x", expand=True)
        self.btn(crow, "new_customer", self.new_customer, 80, height=40).pack(side=self.side(), padx=3)
        self.reload_customers()

        self.label(panel, "pay_method").pack(fill="x", padx=12)
        self.method_box = self.method_combo(panel, 290)
        self.method_box.pack(fill="x", padx=12, pady=(0, 6))
        self.label(panel, "paid").pack(fill="x", padx=12)
        self.paid_entry = self.entry(panel)
        self.paid_entry.pack(fill="x", padx=12, pady=(0, 6))
        self.print_var = ctk.BooleanVar(value=logic.settings().get("auto_print") == "1")
        ctk.CTkCheckBox(panel, text=self.t("print_receipt"), variable=self.print_var, font=FONT).pack(
            padx=12, pady=6, anchor=self.anc)
        ctk.CTkButton(panel, text=self.t("checkout"), height=54, font=("Segoe UI", 18, "bold"),
                      fg_color="#2e8b57", hover_color="#3aa76d", command=self.checkout).pack(fill="x", padx=12, pady=8)
        self.refresh_cart()

    def stat_row(self, parent, key):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(f, text=self.t(key), font=FONT).pack(side=self.side())
        v = ctk.CTkLabel(f, text="0.00", font=FONT_B)
        v.pack(side=self.side(False))
        return v

    def reload_customers(self):
        try:
            custs = logic.list_customers()
        except Exception as e:
            self.err(e)
            custs = []
        self.cust_map = {self.t("no_customer"): None}
        for c in custs:
            self.cust_map[f"{c['name']} #{c['id']}"] = c["id"]
        self.cust_box.configure(values=list(self.cust_map))
        self.cust_box.set(self.t("no_customer"))
        if hasattr(self, "debt_cust_box"):
            self.fill_debt_customers()

    def new_customer(self):
        name = ctk.CTkInputDialog(text=self.t("customer_name"), title=self.t("new_customer")).get_input()
        if not name:
            return
        phone = ctk.CTkInputDialog(text=self.t("customer_phone"), title=self.t("new_customer")).get_input() or ""
        try:
            logic.add_customer(name, phone)
            self.reload_customers()
        except Exception as e:
            self.err(e)

    def on_scan(self, _=None):
        code = self.scan.get().strip()
        if not code:
            return
        try:
            try:
                line = self.cart.add_barcode(code)
                self.show_image(line["image"])
            except logic.POSError as e:
                if e.code != "not_found":
                    raise
                matches = logic.search_products(code)  # بحث بالاسم
                if not matches:
                    raise
                if len(matches) == 1:
                    self.show_image(self.cart.add_barcode(matches[0]["barcode"])["image"])
                else:
                    self.pick_product(matches[:50])
        except Exception as e:
            self.err(e)
        self.scan.delete(0, "end")
        self.refresh_cart()
        self.scan.focus()

    def pick_product(self, matches):
        win = self.popup("pick_product", 700, 430)
        cols = [("name", "name", 260), ("barcode", "barcode", 140), ("price", "price", 90), ("stock", "stock", 80)]
        wrap, tree = self.make_tree(win, cols, 12)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)
        for i, m in enumerate(matches):
            tree.insert("", "end", iid=str(i), values=(m["name"], m["barcode"], f"{m['price']:.2f}", m["stock"]))

        def choose(_=None):
            i = self.sel_id(tree, True)
            if i is None:
                return
            try:
                self.show_image(self.cart.add_barcode(matches[i]["barcode"])["image"])
            except Exception as e:
                self.err(e)
                return
            win.destroy()
            self.refresh_cart()
            self.scan.focus()

        tree.bind("<Double-1>", choose)
        tree.bind("<Return>", choose)
        self.btn(win, "add", choose, 100).pack(fill="x", padx=10, pady=(0, 10))

    def show_image(self, filename):
        img, path = self.blank_img, logic.product_image_path(filename)
        if path:
            try:
                im = Image.open(path)
                w, h = im.size
                s = 96 / max(w, h)
                img = ctk.CTkImage(im, size=(max(1, int(w * s)), max(1, int(h * s))))
            except Exception:
                pass
        self.img_lbl.configure(image=img)
        self.img_lbl.image = img

    def on_cart_select(self, _=None):
        pid = self.sel_id(self.cart_tree, True)
        if pid in self.cart.items:
            self.show_image(self.cart.items[pid]["image"])

    def refresh_cart(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        for l in self.cart.lines():
            self.cart_tree.insert("", "end", iid=str(l["product_id"]), values=(
                l["name"], f"{l['price']:.2f}", l["qty"], f"{self.cart.line_discount(l):.2f}",
                f"{self.cart.line_net(l):.2f}"))
        self.refresh_totals()
        if hasattr(self, "resume_btn"):
            n = len(self.held)
            self.resume_btn.configure(text=f"{self.t('resume')} ({n})" if n else self.t("resume"))

    def refresh_totals(self):
        try:
            t = self.cart.totals(self.disc_entry.get())
        except logic.POSError:
            t = self.cart.totals("")
        self.sub_lbl.configure(text=f"{t['subtotal']:.2f}")
        self.vat_lbl.configure(text=f"{t['vat']:.2f}")
        self.total_lbl.configure(text=f"{t['total']:.2f}")

    def cart_delta(self, d):
        pid = self.sel_id(self.cart_tree)
        if pid is None:
            return
        try:
            self.cart.change_qty(pid, d)
        except Exception as e:
            self.err(e)
        self.refresh_cart()
        if str(pid) in self.cart_tree.get_children():
            self.cart_tree.selection_set(str(pid))

    def cart_discount(self):
        pid = self.sel_id(self.cart_tree)
        if pid is None:
            return
        text = ctk.CTkInputDialog(text=self.t("disc_hint"), title=self.t("discount")).get_input()
        if text is None:
            return
        try:
            self.cart.set_discount(pid, text)
        except Exception as e:
            self.err(e)
        self.refresh_cart()

    def cart_remove(self):
        pid = self.sel_id(self.cart_tree)
        if pid is not None:
            self.cart.remove(pid)
            self.refresh_cart()

    def cart_clear(self):
        self.cart.clear()
        self.refresh_cart()

    def hold_cart(self):
        if not self.cart.items:
            return self.info("empty_cart")
        self.held.append(self.cart)
        self.cart = logic.Cart()
        self.refresh_cart()

    def resume_cart(self):
        if not self.held:
            return self.info("no_held")
        win = self.popup("resume", 520, 360)
        cols = [("time", "time", 130), ("n", "held_items", 90), ("total", "total", 110)]
        wrap, tree = self.make_tree(win, cols, 8)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)
        for i, c in enumerate(self.held):
            tree.insert("", "end", iid=str(i), values=(c.created.strftime("%H:%M"), len(c.items),
                                                      f"{c.totals('')['total']:.2f}"))

        def choose(_=None):
            i = self.sel_id(tree, True)
            if i is None:
                return
            chosen = self.held.pop(i)
            if self.cart.items:
                self.held.append(self.cart)
            self.cart = chosen
            win.destroy()
            self.refresh_cart()

        tree.bind("<Double-1>", choose)
        self.btn(win, "resume", choose, 100).pack(fill="x", padx=10, pady=(0, 10))

    def checkout(self):
        try:
            cid = self.cust_map.get(self.cust_box.get())
            oid, change, _ = self.cart.checkout(self.user, cid, self.paid_entry.get(),
                                                self.method_of(self.method_box), self.disc_entry.get())
        except Exception as e:
            self.err(e)
            return
        if self.print_var.get():
            try:
                logic.print_receipt(oid, self.receipt_labels(), change)
            except Exception as e:
                self.err(e)
        messagebox.showinfo(self.t("info"), f"{self.t('order_no')} {oid}\n{self.t('change')}: {change:.2f}")
        for w in (self.paid_entry, self.disc_entry):
            w.delete(0, "end")
        self.cust_box.set(self.t("no_customer"))
        self.img_lbl.configure(image=self.blank_img)
        self.refresh_cart()
        self.refresh_alerts()
        self.scan.focus()

    # ============================================================ المخزون
    FORM_FIELDS = [("barcode", "barcode"), ("name", "name"), ("price", "price"), ("cost", "cost_price"),
                   ("qty", "init_qty"), ("min", "min_stock"), ("expiry", "expiry"),
                   ("category", "category"), ("supplier", "supplier"), ("image", "image")]

    def _cat_sup_lists(self):
        try:
            return ([c["name"] for c in logic.db.list_categories()], [s["name"] for s in logic.db.list_suppliers()])
        except Exception:
            return [], []

    def product_form(self, parent, cols=3, qty_label="init_qty"):
        f, admin = {}, self.user["role"] == "admin"
        cats, sups = self._cat_sup_lists()
        i = 0
        for key, label in self.FORM_FIELDS:
            if key == "cost" and not admin:
                continue
            r, c = divmod(i, cols)
            i += 1
            cell = ctk.CTkFrame(parent, fg_color="transparent")
            cell.grid(row=r, column=c, padx=8, pady=3, sticky="ew")
            parent.grid_columnconfigure(c, weight=1)
            self.label(cell, qty_label if key == "qty" else label).pack(fill="x")
            if key in ("category", "supplier"):
                w = self.combo(cell, cats if key == "category" else sups, 150)
                w.set("")
                w.pack(fill="x")
            elif key in ("barcode", "image"):
                row = ctk.CTkFrame(cell, fg_color="transparent")
                row.pack(fill="x")
                w = self.entry(row, width=100)
                w.pack(side="left", fill="x", expand=True)
                if key == "barcode":
                    cmd = lambda w=w: self._set(w, logic.new_barcode())
                    ctk.CTkButton(row, text="🎲", width=40, height=40, command=cmd).pack(side="left", padx=(4, 0))
                else:
                    cmd = lambda w=w: self._browse_file(w)
                    ctk.CTkButton(row, text="…", width=40, height=40, command=cmd).pack(side="left", padx=(4, 0))
            else:
                w = self.entry(cell, width=100)
                w.pack(fill="x")
            f[key] = w
        return f

    def _browse_file(self, widget):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.webp")])
        if path:
            self._set(widget, path)

    @staticmethod
    def form_values(f):
        g = lambda k, d="": f[k].get() if k in f else d
        return dict(name=g("name"), price=g("price"), stock=g("qty") or "0", barcode=g("barcode"),
                    category=g("category"), supplier=g("supplier"), cost=g("cost") or "0",
                    min_stock=g("min") or "5", expiry=g("expiry"), image=g("image"))

    def build_inventory(self, tab):
        admin = self.user["role"] == "admin"
        form = ctk.CTkFrame(tab)
        form.pack(fill="x", padx=6, pady=(0, 6))
        self.f = self.product_form(form)
        self.f["barcode"].bind("<Return>", self.lookup_barcode)
        self.hint = ctk.CTkLabel(form, text="", font=FONT, text_color="#e0b040")
        self.hint.grid(row=4, column=0, columnspan=3)
        self.btn(form, "save_product", self.save_product, 200, font=FONT_B).grid(
            row=5, column=0, columnspan=3, pady=(2, 8), padx=10, sticky="ew")

        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(0, 4))
        self.flt_map = {self.t("flt_" + k): k for k in ("all", "low", "expiring", "out")}
        self.flt_btn = ctk.CTkSegmentedButton(bar, values=list(self.flt_map), font=FONT,
                                              command=lambda _v: self.refresh_products())
        self.flt_btn.set(self.t("flt_all"))
        self.flt_btn.pack(side=self.side(False), padx=6)
        self.inv_search = self.entry(bar, self.t("search"))
        self.inv_search.pack(side=self.side(), fill="x", expand=True)
        self.inv_search.bind("<KeyRelease>", lambda e: self.refresh_products())

        cols = [("barcode", "barcode", 130), ("name", "name", 220), ("price", "price", 80)]
        if admin:
            cols.append(("cost", "cost_price", 80))
        cols += [("stock", "stock", 70), ("min", "min_stock", 70), ("expiry", "expiry", 100),
                 ("category", "category", 110), ("supplier", "supplier", 110)]
        self.prod_admin_cols = admin
        acts = ctk.CTkFrame(tab, fg_color="transparent")
        acts.pack(side="bottom", fill="x", padx=6, pady=6)
        wrap, self.prod_tree = self.make_tree(tab, cols, 5)
        wrap.pack(fill="both", expand=True, padx=6)
        self.btn(acts, "labels", self.print_labels_selected, 140).pack(side=self.side(), padx=4)
        if admin:
            self.btn(acts, "edit_selected", self.edit_product, 130).pack(side=self.side(), padx=4)
            self.btn(acts, "delete_product", self.delete_selected_product, 130, fg_color="#8b2e2e",
                     hover_color="#a33").pack(side=self.side(), padx=4)
            self.prod_tree.bind("<Double-1>", self.edit_product)
            self.prod_tree.bind("<Delete>", lambda e: self.delete_selected_product())
        self.refresh_products()

    def lookup_barcode(self, _=None):
        try:
            p = logic.find_product(self.f["barcode"].get())
        except Exception as e:
            self.err(e)
            return
        if p:
            vals = {"name": p["name"], "price": f"{p['price']:.2f}", "cost": f"{p['cost_price']:.2f}",
                    "min": str(p["min_stock"]), "expiry": p["expiry_date"].isoformat() if p["expiry_date"] else "",
                    "category": p["category_name"] or "", "supplier": p["supplier_name"] or ""}
            for k, v in vals.items():
                if k in self.f:
                    self._set(self.f[k], v)
            self.hint.configure(text=self.t("exists_hint"))
            self.f["qty"].focus()
        else:
            self.hint.configure(text="")
            self.f["name"].focus()

    def save_product(self):
        try:
            _, created = logic.add_product(self.user, **self.form_values(self.f))
        except Exception as e:
            self.err(e)
            return
        self.info("created" if created else "updated")
        for w in self.f.values():
            self._set(w, "")
        self.hint.configure(text="")
        self.refresh_products()
        self.refresh_alerts()
        self.f["barcode"].focus()

    def refresh_products(self):
        try:
            rows = logic.search_products(self.inv_search.get(), self.flt_map.get(self.flt_btn.get(), "all"))
        except Exception as e:
            self.err(e)
            return
        self.prod_tree.delete(*self.prod_tree.get_children())
        self.products = {p["id"]: p for p in rows}
        today = date.today()
        for p in rows:
            tags = ()
            if p["stock"] <= p["min_stock"]:
                tags = ("low",)
            elif p["expiry_date"] and (p["expiry_date"] - today).days <= 30:
                tags = ("exp",)
            vals = [p["barcode"], p["name"], f"{p['price']:.2f}"]
            if self.prod_admin_cols:
                vals.append(f"{p['cost_price']:.2f}")
            vals += [p["stock"], p["min_stock"], p["expiry_date"].isoformat() if p["expiry_date"] else "",
                     p["category_name"] or "", p["supplier_name"] or ""]
            self.prod_tree.insert("", "end", iid=str(p["id"]), values=vals, tags=tags)

    def print_labels_selected(self):
        sel = self.prod_tree.selection()
        if not sel:
            return self.info("select_row")
        txt = ctk.CTkInputDialog(text=self.t("copies"), title=self.t("labels")).get_input()
        if txt is None:
            return
        try:
            logic.print_labels([self.products[int(i)] for i in sel], logic.parse_int(txt or "1"))
        except Exception as e:
            self.err(e)

    def edit_product(self, _=None):
        if self.user["role"] != "admin":
            return
        pid = self.sel_id(self.prod_tree)
        if pid is None:
            return
        p = self.products[pid]
        win = self.popup("edit_product", 760, 380)
        box = ctk.CTkFrame(win, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)
        f = self.product_form(box, cols=3, qty_label="stock")
        vals = {"barcode": p["barcode"], "name": p["name"], "price": f"{p['price']:.2f}",
                "cost": f"{p['cost_price']:.2f}", "qty": str(p["stock"]), "min": str(p["min_stock"]),
                "expiry": p["expiry_date"].isoformat() if p["expiry_date"] else "",
                "category": p["category_name"] or "", "supplier": p["supplier_name"] or ""}
        for k, v in vals.items():
            self._set(f[k], v)

        def save():
            try:
                logic.update_product(self.user, pid, **self.form_values(f))
            except Exception as e:
                self.err(e)
                return
            win.destroy()
            self.refresh_products()
            self.refresh_alerts()
            self.info("saved_changes")

        self.btn(win, "save", save, 200, font=FONT_B).pack(fill="x", padx=20, pady=12)

    def delete_selected_product(self):
        sel = self.prod_tree.selection()
        if not sel:
            return self.info("select_row")
        if not messagebox.askyesno(self.t("info"), self.t("confirm_delete_product")):
            return
        archived = False
        try:
            for i in sel:
                archived |= logic.delete_product(self.user, int(i)) == "archived"
        except Exception as e:
            self.err(e)
            return
        finally:
            self.refresh_products()
            self.refresh_alerts()
        self.info("product_archived" if archived else "product_deleted")

    # ============================================================ الفواتير
    def build_invoices(self, tab):
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(0, 6))
        self.btn(bar, "search_btn", lambda: self.refresh_invoices(), 90).pack(side=self.side(False), padx=4)
        self.inv_q = self.entry(bar, self.t("inv_search"))
        self.inv_q.pack(side=self.side(), fill="x", expand=True)
        self.inv_q.bind("<Return>", lambda e: self.refresh_invoices())
        cols = [("id", "invoice", 70), ("date", "date", 150), ("cust", "customer", 170), ("user", "cashier_col", 110),
                ("total", "total", 90), ("paid", "paid_short", 90), ("method", "method", 110)]
        wrap, self.order_tree = self.make_tree(tab, cols, 6)
        wrap.pack(fill="both", expand=True, padx=6)
        self.order_tree.bind("<Double-1>", lambda e: self.open_order_selected())
        acts = ctk.CTkFrame(tab, fg_color="transparent")
        acts.pack(fill="x", padx=6, pady=6)
        self.btn(acts, "details", self.open_order_selected, 150).pack(side=self.side(), padx=4)
        self.btn(acts, "print_receipt", self.reprint_selected, 150).pack(side=self.side(), padx=4)

    def refresh_invoices(self):
        try:
            rows = logic.search_orders(self.inv_q.get())
        except Exception as e:
            self.err(e)
            return
        self.order_tree.delete(*self.order_tree.get_children())
        for o in rows:
            self.order_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"], self.fmt_dt(o["created_at"]), o["customer"] or "", o["username"] or "",
                f"{o['total']:.2f}", f"{o['paid']:.2f}", self.t("pm_" + (o["payment_method"] or "cash"))))

    def open_order_selected(self):
        oid = self.sel_id(self.order_tree)
        if oid:
            self.open_order(oid)

    def reprint_selected(self):
        oid = self.sel_id(self.order_tree)
        if oid:
            try:
                logic.print_receipt(oid, self.receipt_labels())
            except Exception as e:
                self.err(e)

    def invoice_text(self, o, items):
        lines = [f"{logic.settings()['shop_name']} - {self.t('invoice')} #{o['id']}", self.fmt_dt(o["created_at"])]
        for i in items:
            lines.append(f"{i['name']} × {i['quantity']} = {i['unit_price'] * i['quantity'] - i['discount']:.2f}")
        lines.append(f"{self.t('total')}: {o['total']:.2f}")
        return "\n".join(lines)

    def send_whatsapp(self, phone, text):
        try:
            webbrowser.open(logic.whatsapp_url(phone, text))
        except Exception as e:
            self.err(e)

    def open_order(self, oid):
        win = self.popup("order_details", 820, 600)
        try:
            o, items = logic.order_details(oid)
        except Exception as e:
            self.err(e)
            return
        head = ctk.CTkLabel(win, text="", font=FONT_B)
        head.pack(pady=8)
        cols = [("name", "name", 250), ("qty", "qty", 70), ("ret", "returned", 80), ("price", "price", 90),
                ("disc", "discount", 90)]
        wrap, tree = self.make_tree(win, cols, 9)
        wrap.pack(fill="both", expand=True, padx=10)
        ctrl = ctk.CTkFrame(win, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=8)
        qty = self.entry(ctrl, self.t("qty"), width=90)
        qty.pack(side=self.side(), padx=4)
        refund_method = self.method_combo(ctrl, 150)
        refund_method.pack(side=self.side(), padx=4)

        def reload():
            nonlocal o, items
            o, items = logic.order_details(oid)
            head.configure(text=f"#{oid} • {self.fmt_dt(o['created_at'])} • {o['customer_name'] or self.t('no_customer')}"
                                f" • {self.t('total')}: {o['total']:.2f}")
            tree.delete(*tree.get_children())
            for i in items:
                tree.insert("", "end", iid=str(i["id"]), values=(
                    i["name"], i["quantity"], i["returned"], f"{i['unit_price']:.2f}", f"{i['discount']:.2f}"))

        def do_return():
            iid = self.sel_id(tree)
            if iid is None:
                return
            try:
                _, amount = logic.process_return(self.user, oid, {iid: logic.parse_int(qty.get() or "1")},
                                                 self.method_of(refund_method))
                reload()
            except Exception as e:
                self.err(e)
                return
            messagebox.showinfo(self.t("info"), f"{self.t('refunded')}: {amount:.2f}")
            self.refresh_alerts()

        self.btn(ctrl, "do_return", do_return, 150, fg_color="#b8651b").pack(side=self.side(), padx=4)
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))
        self.btn(row, "print_receipt", lambda: logic.print_receipt(oid, self.receipt_labels()), 150).pack(
            side=self.side(), padx=4)
        self.btn(row, "whatsapp", lambda: self.send_whatsapp(o["customer_phone"], self.invoice_text(o, items)), 120,
                 fg_color="#25a244").pack(side=self.side(), padx=4)
        reload()

    # ============================================================== الديون
    def build_debts(self, tab):
        top = ctk.CTkFrame(tab)
        top.pack(fill="x", padx=6, pady=(0, 6))
        self.debts_total_lbl = ctk.CTkLabel(top, text="", font=("Segoe UI", 18, "bold"), text_color="#e0b040")
        self.debts_total_lbl.pack(side=self.side(), padx=14, pady=8)
        self.btn(top, "new_customer", self.new_customer, 90).pack(side=self.side(False), padx=4)
        self.btn(top, "statement", self.statement_from_combo, 110).pack(side=self.side(False), padx=4)
        self.debt_cust_box = ctk.CTkComboBox(top, values=[""], height=40, width=220, font=FONT, state="readonly")
        self.debt_cust_box.pack(side=self.side(False), padx=4)
        self.fill_debt_customers()

        cols = [("customer", "customer", 200), ("phone", "phone", 130), ("amount", "debt_amount", 100),
                ("paid", "paid_so_far", 100), ("rem", "remaining", 100), ("date", "date", 120)]
        wrap, self.debt_tree = self.make_tree(tab, cols, 6)
        wrap.pack(fill="both", expand=True, padx=6)
        self.debt_tree.bind("<Double-1>", lambda e: self.statement_from_debt())
        self.debts_data = {}

        bot = ctk.CTkFrame(tab, fg_color="transparent")
        bot.pack(fill="x", padx=6, pady=8)
        self.btn(bot, "pay", self.pay_selected_debt, 110, fg_color="#2e8b57", hover_color="#3aa76d").pack(
            side=self.side(), padx=4)
        self.pay_method = self.method_combo(bot, 150)
        self.pay_method.pack(side=self.side(), padx=4)
        self.pay_entry = self.entry(bot, self.t("pay_amount"), width=210)
        self.pay_entry.pack(side=self.side(), padx=4)
        self.btn(bot, "reminder", self.remind_selected, 170, fg_color="#25a244").pack(side=self.side(False), padx=4)
        self.btn(bot, "statement", self.statement_from_debt, 110).pack(side=self.side(False), padx=4)

    def fill_debt_customers(self):
        try:
            custs = logic.list_customers()
        except Exception:
            custs = []
        self.debt_cust_map = {f"{c['name']} #{c['id']}": c["id"] for c in custs}
        self.debt_cust_box.configure(values=list(self.debt_cust_map) or [""])
        self.debt_cust_box.set(self.t("pick_customer"))

    def refresh_debts(self):
        try:
            rows = logic.open_debts()
        except Exception as e:
            self.err(e)
            return
        self.debt_tree.delete(*self.debt_tree.get_children())
        self.debts_data, total = {}, 0
        for d in rows:
            self.debts_data[d["id"]] = d
            total += d["remaining"]
            self.debt_tree.insert("", "end", iid=str(d["id"]), values=(
                d["customer"], d["phone"] or "", f"{d['amount']:.2f}", f"{d['paid_amount']:.2f}",
                f"{d['remaining']:.2f}", self.fmt_dt(d["created_at"])[:10]))
        self.debts_total_lbl.configure(text=f"{self.t('total_debts')}: {total:.2f}")

    def pay_selected_debt(self):
        did = self.sel_id(self.debt_tree)
        if did is None:
            return
        try:
            logic.pay_debt(self.user, did, self.pay_entry.get(), self.debts_data[did]["remaining"],
                           self.method_of(self.pay_method))
        except Exception as e:
            self.err(e)
            return
        self.pay_entry.delete(0, "end")
        self.refresh_debts()
        self.info("pay_ok")

    def wa_debt_text(self, name, amount):
        return self.t("wa_debt").format(name=name, shop=logic.settings()["shop_name"], amount=f"{amount:.2f}")

    def remind_selected(self):
        did = self.sel_id(self.debt_tree)
        if did is not None:
            d = self.debts_data[did]
            self.send_whatsapp(d["phone"], self.wa_debt_text(d["customer"], d["remaining"]))

    def statement_from_combo(self):
        cid = self.debt_cust_map.get(self.debt_cust_box.get())
        self.open_statement(cid) if cid else self.info("pick_customer")

    def statement_from_debt(self):
        did = self.sel_id(self.debt_tree)
        if did is not None:
            self.open_statement(self.debts_data[did]["customer_id"])

    def open_statement(self, cid):
        try:
            st = logic.customer_statement(cid)
        except Exception as e:
            self.err(e)
            return
        c = st["customer"]
        win = self.popup("statement", 860, 560)
        ctk.CTkLabel(win, text=f"{c['name']}  {c['phone'] or ''}", font=("Segoe UI", 18, "bold")).pack(pady=(10, 2))
        ctk.CTkLabel(win, font=FONT, text=f"{self.t('total_bought')}: {st['total_bought']:.2f}   |   "
                                          f"{self.t('remaining')}: {st['total_remaining']:.2f}").pack()
        sub = ctk.CTkTabview(win)
        sub.pack(fill="both", expand=True, padx=10, pady=8)
        specs = [("invoices", [("id", "invoice", 70), ("date", "date", 150), ("total", "total", 100),
                               ("paid", "paid_short", 100), ("m", "method", 110)],
                  [(o["id"], self.fmt_dt(o["created_at"]), f"{o['total']:.2f}", f"{o['paid']:.2f}",
                    self.t("pm_" + (o["payment_method"] or "cash"))) for o in st["orders"]]),
                 ("debts", [("date", "date", 150), ("a", "debt_amount", 100), ("p", "paid_so_far", 100),
                            ("r", "remaining", 100)],
                  [(self.fmt_dt(d["created_at"]), f"{d['amount']:.2f}", f"{d['paid_amount']:.2f}",
                    f"{d['remaining']:.2f}") for d in st["debts"]]),
                 ("payments", [("date", "date", 150), ("a", "paid_so_far", 100), ("m", "method", 110)],
                  [(self.fmt_dt(p["created_at"]), f"{p['amount']:.2f}", self.t("pm_" + (p["method"] or "cash")))
                   for p in st["payments"]])]
        for key, cols, rows in specs:
            wrap, tree = self.make_tree(sub.add(self.t(key)), cols, 10)
            wrap.pack(fill="both", expand=True)
            for r in rows:
                tree.insert("", "end", values=r)
        if st["total_remaining"] > 0:
            self.btn(win, "reminder", lambda: self.send_whatsapp(
                c["phone"], self.wa_debt_text(c["name"], st["total_remaining"])), 180, fg_color="#25a244").pack(pady=8)

    # ============================================================ الوردية
    def build_shift(self, tab):
        self.shift_lbl = ctk.CTkLabel(tab, text="", font=("Segoe UI", 15), justify=self.just, anchor=self.anc)
        self.shift_lbl.pack(fill="x", padx=24, pady=12)
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=24)
        self.counted_entry = self.entry(row, self.t("counted_cash"), width=220)
        self.counted_entry.pack(side=self.side(), padx=4)
        self.shift_note = self.entry(row, self.t("note"), width=320)
        self.shift_note.pack(side=self.side(), padx=4)
        self.btn(row, "close_shift", self.do_close_shift, 160, font=FONT_B).pack(side=self.side(), padx=4)
        self.shift_result = ctk.CTkLabel(tab, text="", font=("Segoe UI", 18, "bold"))
        self.shift_result.pack(pady=14)

    def refresh_shift(self):
        try:
            i = logic.shift_info(self.user)
        except Exception as e:
            self.err(e)
            return
        lines = [f"{self.t('shift_since')}: {self.fmt_dt(i['since'])}", ""]
        for title, data in (("sales_by", i["sales"]), ("debt_collected", i["debt_payments"]),
                            ("refunds", i["refunds"])):
            for m, v in data.items():
                lines.append(f"{self.t(title)} - {self.t('pm_' + m)}: {v:.2f}")
        lines += ["", f"{self.t('expected_cash')}: {i['expected_cash']:.2f}"]
        self.shift_lbl.configure(text="\n".join(lines))

    def do_close_shift(self):
        try:
            expected, diff = logic.close_shift(self.user, self.counted_entry.get(), self.shift_note.get())
        except Exception as e:
            self.err(e)
            return
        color = "#4cc38a" if diff == 0 else "#ff6b6b"
        self.shift_result.configure(text=f"{self.t('shift_closed')} — {self.t('difference')}: {diff:+.2f}",
                                    text_color=color)
        self.counted_entry.delete(0, "end")
        self.shift_note.delete(0, "end")
        self.refresh_shift()

    # ============================================================ الموردين
    def build_suppliers(self, tab):
        sub = ctk.CTkTabview(tab)
        sub.pack(fill="both", expand=True)
        self.build_sup_list(sub.add(self.t("suppliers")))
        self.build_purchases(sub.add(self.t("purchases")))
        self.build_cats(sub.add(self.t("categories")))

    def refresh_suppliers_all(self):
        self.refresh_sup_list()
        self.refresh_purchases()
        self.refresh_cats()

    # --- قائمة الموردين
    def build_sup_list(self, tab):
        cols = [("name", "name", 220), ("phone", "phone", 140), ("tp", "total_purchased", 120),
                ("paid", "paid_so_far", 110), ("owed", "owed", 110)]
        wrap, self.sup_tree = self.make_tree(tab, cols, 10)
        wrap.pack(fill="both", expand=True, padx=6, pady=6)
        self.sup_tree.bind("<<TreeviewSelect>>", self.on_sup_select)
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=6)
        self.sup_name = self.entry(row, self.t("name"), width=220)
        self.sup_name.pack(side=self.side(), padx=4)
        self.sup_phone = self.entry(row, self.t("phone"), width=180)
        self.sup_phone.pack(side=self.side(), padx=4)
        self.btn(row, "save", self.save_supplier, 90).pack(side=self.side(), padx=4)
        self.btn(row, "new", self.clear_sup_form, 80).pack(side=self.side(), padx=4)
        self.btn(row, "delete", self.delete_supplier, 90, fg_color="#8b2e2e", hover_color="#a33").pack(
            side=self.side(), padx=4)
        self.sup_id = None

    def refresh_sup_list(self):
        try:
            rows = logic.list_suppliers(self.user)
        except Exception as e:
            self.err(e)
            return
        self.sup_tree.delete(*self.sup_tree.get_children())
        self.suppliers = {s["id"]: s for s in rows}
        for s in rows:
            self.sup_tree.insert("", "end", iid=str(s["id"]), values=(
                s["name"], s["phone"] or "", f"{s['total_purchased']:.2f}", f"{s['paid']:.2f}", f"{s['owed']:.2f}"))
        names = {s["name"]: s["id"] for s in rows}
        if hasattr(self, "pur_supplier"):
            self.pur_sup_map = names
            self.pur_supplier.configure(values=list(names) or [""])

    def on_sup_select(self, _=None):
        sid = self.sel_id(self.sup_tree, True)
        if sid:
            self.sup_id = sid
            self._set(self.sup_name, self.suppliers[sid]["name"])
            self._set(self.sup_phone, self.suppliers[sid]["phone"] or "")

    def clear_sup_form(self):
        self.sup_id = None
        self._set(self.sup_name, "")
        self._set(self.sup_phone, "")

    def save_supplier(self):
        try:
            logic.save_supplier(self.user, self.sup_id, self.sup_name.get(), self.sup_phone.get())
        except Exception as e:
            self.err(e)
            return
        self.clear_sup_form()
        self.refresh_sup_list()

    def delete_supplier(self):
        sid = self.sel_id(self.sup_tree)
        if sid and messagebox.askyesno(self.t("info"), self.t("confirm_delete")):
            try:
                logic.delete_supplier(self.user, sid)
            except Exception as e:
                self.err(e)
            self.clear_sup_form()
            self.refresh_sup_list()

    # --- فواتير الشراء
    def build_purchases(self, tab):
        self.draft = logic.PurchaseDraft()
        left = ctk.CTkFrame(tab, fg_color="transparent")
        left.pack(side=self.side(), fill="both", expand=True, padx=6)
        right = ctk.CTkFrame(tab, fg_color="transparent", width=420)
        right.pack(side=self.side(False), fill="both", padx=6)

        self.pur_sup_map = {}
        self.pur_supplier = self.combo(left, [""], 260)
        self.pur_supplier.configure(state="readonly")
        self.pur_supplier.set("")
        self.pur_supplier.pack(fill="x", pady=(6, 4))
        row = ctk.CTkFrame(left, fg_color="transparent")
        row.pack(fill="x")
        self.pur_code = self.entry(row, self.t("scan"), width=240)
        self.pur_code.pack(side=self.side(), fill="x", expand=True, padx=2)
        self.pur_qty = self.entry(row, self.t("qty"), width=70)
        self.pur_qty.pack(side=self.side(), padx=2)
        self.pur_cost = self.entry(row, self.t("cost"), width=90)
        self.pur_cost.pack(side=self.side(), padx=2)
        self.btn(row, "add", self.pur_add, 70).pack(side=self.side(), padx=2)
        self.pur_code.bind("<Return>", lambda e: self.pur_add())

        cols = [("name", "name", 220), ("qty", "qty", 60), ("cost", "cost", 80), ("sub", "subtotal", 90)]
        wrap, self.pur_tree = self.make_tree(left, cols, 8)
        wrap.pack(fill="both", expand=True, pady=6)
        foot = ctk.CTkFrame(left, fg_color="transparent")
        foot.pack(fill="x")
        self.pur_total = ctk.CTkLabel(foot, text="0.00", font=("Segoe UI", 22, "bold"), text_color="#4cc38a")
        self.pur_total.pack(side=self.side(), padx=8)
        self.pur_paid = self.entry(foot, self.t("pay_supplier"), width=230)
        self.pur_paid.pack(side=self.side(), padx=4)
        self.btn(foot, "remove", self.pur_remove, 80).pack(side=self.side(), padx=4)
        self.btn(foot, "save_purchase", self.pur_save, 170, fg_color="#2e8b57", hover_color="#3aa76d").pack(
            side=self.side(), padx=4)

        wrap2, self.pur_hist = self.make_tree(right, [("id", "invoice", 50), ("date", "date", 120),
                                                      ("sup", "supplier", 110), ("total", "total", 80)], 12)
        wrap2.pack(fill="both", expand=True, pady=6)

    def pur_add(self):
        try:
            self.draft.add(self.pur_code.get(), self.pur_qty.get(), self.pur_cost.get())
        except Exception as e:
            self.err(e)
            return
        for w in (self.pur_code, self.pur_qty, self.pur_cost):
            w.delete(0, "end")
        self.refresh_draft()
        self.pur_code.focus()

    def pur_remove(self):
        pid = self.sel_id(self.pur_tree)
        if pid:
            self.draft.remove(pid)
            self.refresh_draft()

    def refresh_draft(self):
        self.pur_tree.delete(*self.pur_tree.get_children())
        for l in self.draft.lines():
            self.pur_tree.insert("", "end", iid=str(l["product_id"]), values=(
                l["name"], l["qty"], f"{l['cost']:.2f}", f"{l['cost'] * l['qty']:.2f}"))
        self.pur_total.configure(text=f"{self.draft.total():.2f}")

    def pur_save(self):
        try:
            self.draft.save(self.user, self.pur_sup_map.get(self.pur_supplier.get()), self.pur_paid.get())
        except Exception as e:
            self.err(e)
            return
        self.pur_paid.delete(0, "end")
        self.refresh_draft()
        self.refresh_purchases()
        self.refresh_sup_list()
        self.refresh_alerts()
        self.info("purchase_saved")

    def refresh_purchases(self):
        try:
            rows = logic.list_purchases(self.user)
        except Exception as e:
            self.err(e)
            return
        self.pur_hist.delete(*self.pur_hist.get_children())
        for p in rows:
            self.pur_hist.insert("", "end", values=(p["id"], self.fmt_dt(p["created_at"]),
                                                     p["supplier"] or "", f"{p['total']:.2f}"))

    # --- التصنيفات
    def build_cats(self, tab):
        wrap, self.cat_tree = self.make_tree(tab, [("name", "name", 260), ("n", "products_count", 120)], 10)
        wrap.pack(fill="both", expand=True, padx=6, pady=6)
        self.cat_tree.bind("<<TreeviewSelect>>", self.on_cat_select)
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=6)
        self.cat_name = self.entry(row, self.t("name"), width=240)
        self.cat_name.pack(side=self.side(), padx=4)
        self.btn(row, "save", self.save_cat, 90).pack(side=self.side(), padx=4)
        self.btn(row, "new", self.clear_cat, 80).pack(side=self.side(), padx=4)
        self.btn(row, "delete", self.delete_cat, 90, fg_color="#8b2e2e", hover_color="#a33").pack(side=self.side(), padx=4)
        self.cat_id = None

    def refresh_cats(self):
        try:
            rows = logic.list_categories(self.user)
        except Exception as e:
            self.err(e)
            return
        self.cat_tree.delete(*self.cat_tree.get_children())
        self.cats = {c["id"]: c for c in rows}
        for c in rows:
            self.cat_tree.insert("", "end", iid=str(c["id"]), values=(c["name"], c["products"]))

    def on_cat_select(self, _=None):
        cid = self.sel_id(self.cat_tree, True)
        if cid:
            self.cat_id = cid
            self._set(self.cat_name, self.cats[cid]["name"])

    def clear_cat(self):
        self.cat_id = None
        self._set(self.cat_name, "")

    def save_cat(self):
        try:
            logic.save_category(self.user, self.cat_id, self.cat_name.get())
        except Exception as e:
            self.err(e)
            return
        self.clear_cat()
        self.refresh_cats()

    def delete_cat(self):
        cid = self.sel_id(self.cat_tree)
        if cid and messagebox.askyesno(self.t("info"), self.t("confirm_delete")):
            try:
                logic.delete_category(self.user, cid)
            except Exception as e:
                self.err(e)
            self.clear_cat()
            self.refresh_cats()

    # ============================================================ التقارير
    PERIODS = ("today", "7d", "30d", "all")

    def build_reports(self, tab):
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(0, 6))
        labels = [self.t("period_" + k) for k in self.PERIODS]
        self.period_map = dict(zip(labels, self.PERIODS))
        self.period_btn = ctk.CTkSegmentedButton(bar, values=labels, font=FONT, command=lambda _v: self.refresh_report())
        self.period_btn.pack(side=self.side())
        self.period_btn.set(labels[0])
        self.btn(bar, "export", self.export_csv, 190).pack(side=self.side(False))

        body = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        body.pack(fill="both", expand=True)
        cards = ctk.CTkFrame(body, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 6))
        self.cards = {}
        for key, color in (("orders_count", "#4a90d9"), ("sales", "#4cc38a"), ("returns", "#ff6b6b"),
                           ("profit", "#e0b040"), ("collected", "#4cc38a"), ("outstanding", "#ff9f43")):
            card = ctk.CTkFrame(cards)
            card.pack(side=self.side(), fill="x", expand=True, padx=3)
            ctk.CTkLabel(card, text=self.t(key), font=("Segoe UI", 12)).pack(pady=(8, 0))
            lbl = ctk.CTkLabel(card, text="0", font=("Segoe UI", 22, "bold"), text_color=color)
            lbl.pack(pady=(0, 8))
            self.cards[key] = lbl

        charts = ctk.CTkFrame(body, fg_color="transparent")
        charts.pack(fill="x")
        for i, (title, attr, color, horiz) in enumerate((("daily_sales", "chart_daily", "#4a90d9", False),
                                                          ("top_products", "chart_top", "#4cc38a", True))):
            charts.grid_columnconfigure(i, weight=1, uniform="ch")
            box = ctk.CTkFrame(charts)
            box.grid(row=0, column=i, sticky="nsew", padx=3)
            ctk.CTkLabel(box, text=self.t(title), font=FONT_B).pack(pady=4)
            ch = BarChart(box, color, horiz, 220)
            ch.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            setattr(self, attr, ch)

        tables = ctk.CTkFrame(body, fg_color="transparent")
        tables.pack(fill="x", pady=6)
        for i, (title, attr, cols) in enumerate((
                ("by_method", "method_tree", [("a", "method", 120), ("b", "orders_count", 90), ("c", "collected", 100)]),
                ("by_employee", "user_tree_r", [("a", "cashier_col", 120), ("b", "orders_count", 90), ("c", "revenue", 100)]))):
            tables.grid_columnconfigure(i, weight=1, uniform="tb")
            box = ctk.CTkFrame(tables, fg_color="transparent")
            box.grid(row=0, column=i, sticky="nsew", padx=3)
            ctk.CTkLabel(box, text=self.t(title), font=FONT_B).pack(pady=4)
            wrap, tree = self.make_tree(box, cols, 5)
            wrap.pack(fill="both", expand=True)
            setattr(self, attr, tree)

    def refresh_report(self):
        try:
            r = logic.sales_report(self.user, self.period_map[self.period_btn.get()])
        except Exception as e:
            self.err(e)
            return
        s = r["summary"]
        for key in self.cards:
            src = "orders" if key == "orders_count" else key
            v = s[src]
            self.cards[key].configure(text=str(v) if key == "orders_count" else f"{v:.2f}")
        daily = r["daily"][:14][::-1]
        self.chart_daily.set_data([d["day"].strftime("%m-%d") for d in daily], [d["revenue"] for d in daily])
        top = r["top"][:8]
        self.chart_top.set_data([p["name"][:16] for p in top], [p["qty"] for p in top])
        self.method_tree.delete(*self.method_tree.get_children())
        for m in r["by_method"]:
            self.method_tree.insert("", "end", values=(self.t("pm_" + (m["method"] or "cash")), m["orders"],
                                                       f"{m['collected']:.2f}"))
        self.user_tree_r.delete(*self.user_tree_r.get_children())
        for u in r["by_user"]:
            self.user_tree_r.insert("", "end", values=(u["username"], u["orders"], f"{u['revenue']:.2f}"))

    def export_csv(self):
        try:
            path = logic.export_all(self.user)
        except Exception as e:
            self.err(e)
            return
        messagebox.showinfo(self.t("info"), f"{self.t('exported')}:\n{path}")
        webbrowser.open(Path(path).as_uri())

    # =============================================================== السجل
    def build_activity(self, tab):
        self.act_q = self.entry(tab, self.t("act_search"))
        self.act_q.pack(fill="x", padx=6, pady=(0, 6))
        self.act_q.bind("<KeyRelease>", lambda e: self.refresh_activity())
        cols = [("t", "time", 150), ("u", "username", 110), ("a", "action", 150), ("d", "details_col", 520)]
        wrap, self.act_tree = self.make_tree(tab, cols, 8)
        wrap.pack(fill="both", expand=True, padx=6)
        self.act_tree.column("d", anchor="w")

    def refresh_activity(self):
        try:
            rows = logic.activity(self.user, self.act_q.get())
        except Exception as e:
            self.err(e)
            return
        self.act_tree.delete(*self.act_tree.get_children())
        for r in rows:
            self.act_tree.insert("", "end", values=(self.fmt_dt(r["created_at"]), r["username"] or "",
                                                     T.get("act_" + r["action"], (r["action"],) * 2)[0 if self.lang == "en" else 1],
                                                     r["details"] or ""))

    # ============================================================ الإعدادات
    def build_settings(self, tab):
        left = ctk.CTkFrame(tab, fg_color="transparent")
        left.pack(side=self.side(), fill="both", expand=True, padx=6)
        right = ctk.CTkScrollableFrame(tab, width=420)
        right.pack(side=self.side(False), fill="y", padx=6)

        wrap, self.user_tree = self.make_tree(left, [("u", "username", 220), ("r", "role", 140)], 12)
        wrap.pack(fill="both", expand=True)
        ubar = ctk.CTkFrame(left, fg_color="transparent")
        ubar.pack(fill="x", pady=8)
        self.btn(ubar, "delete_selected", self.delete_user, 150, fg_color="#8b2e2e", hover_color="#a33").pack(
            side=self.side(), padx=3)
        self.btn(ubar, "promote", lambda: self.change_role("admin"), 150, fg_color="#2e8b57",
                 hover_color="#3aa76d").pack(side=self.side(), padx=3)
        self.btn(ubar, "demote", lambda: self.change_role("employee"), 160, fg_color="#b8651b").pack(
            side=self.side(), padx=3)

        def section(key):
            ctk.CTkLabel(right, text=self.t(key), font=FONT_B).pack(pady=(16, 4))

        section("change_password")
        self.new_pw = self.entry(right, self.t("new_password"), show="•")
        self.new_pw.pack(fill="x", padx=10)
        self.btn(right, "change_password", self.change_pw).pack(fill="x", padx=10, pady=6)

        section("add_employee")
        self.emp_name = self.entry(right, self.t("username"))
        self.emp_name.pack(fill="x", padx=10, pady=2)
        self.emp_pw = self.entry(right, self.t("password"), show="•")
        self.emp_pw.pack(fill="x", padx=10, pady=2)
        self.btn(right, "add_employee", self.add_emp).pack(fill="x", padx=10, pady=6)

        section("shop_settings")
        s = logic.settings(refresh=True)
        self.sf = {}
        for key in ("shop_name", "shop_address", "shop_phone", "vat_rate", "country_code", "logo", "backup_dir"):
            self.label(right, key).pack(fill="x", padx=10)
            row = ctk.CTkFrame(right, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=(0, 4))
            w = self.entry(row, width=200)
            w.pack(side="left", fill="x", expand=True)
            if key in ("logo", "backup_dir"):
                cmd = (lambda w=w: self._browse_file(w)) if key == "logo" else (lambda w=w: self._browse_dir(w))
                ctk.CTkButton(row, text="…", width=40, height=40, command=cmd).pack(side="left", padx=(4, 0))
            self._set(w, s.get(key, ""))
            self.sf[key] = w
        self.auto_print_var = ctk.BooleanVar(value=s.get("auto_print") == "1")
        ctk.CTkSwitch(right, text=self.t("auto_print"), variable=self.auto_print_var, font=FONT).pack(
            padx=10, pady=8, anchor=self.anc)
        self.btn(right, "save", self.save_shop_settings).pack(fill="x", padx=10, pady=4)
        self.btn(right, "backup_now", self.backup_now, fg_color="#6b4fa0").pack(fill="x", padx=10, pady=4)
        self.btn(right, "export", self.export_csv, fg_color="#6b4fa0").pack(fill="x", padx=10, pady=(4, 16))
        self.refresh_users()

    def _browse_dir(self, widget):
        path = filedialog.askdirectory()
        if path:
            self._set(widget, path)

    def save_shop_settings(self):
        values = {k: w.get().strip() for k, w in self.sf.items()}
        values["auto_print"] = "1" if self.auto_print_var.get() else "0"
        try:
            logic.save_settings(self.user, values)
        except Exception as e:
            self.err(e)
            return
        self.print_var.set(self.auto_print_var.get())
        self.info("settings_saved")

    def backup_now(self):
        try:
            path = logic.backup_now(self.user)
        except Exception as e:
            self.err(e)
            return
        messagebox.showinfo(self.t("info"), f"{self.t('backup_done')}:\n{path}")

    def refresh_users(self):
        try:
            users = logic.list_users(self.user)
        except Exception as e:
            self.err(e)
            return
        self.user_tree.delete(*self.user_tree.get_children())
        for u in users:
            role = self.t("admin") if u["role"] == "admin" else self.t("employee")
            self.user_tree.insert("", "end", iid=u["username"], values=(u["username"], role))

    def _sel_user(self):
        sel = self.user_tree.selection()
        if not sel:
            self.info("select_row")
            return None
        return sel[0]

    def change_pw(self):
        name = self._sel_user()
        if not name:
            return
        try:
            logic.change_password(self.user, name, self.new_pw.get())
        except Exception as e:
            self.err(e)
            return
        self.new_pw.delete(0, "end")
        self.info("pw_changed")

    def add_emp(self):
        try:
            logic.add_employee(self.user, self.emp_name.get(), self.emp_pw.get())
        except Exception as e:
            self.err(e)
            return
        self.emp_name.delete(0, "end")
        self.emp_pw.delete(0, "end")
        self.refresh_users()
        self.info("emp_added")

    def change_role(self, role):
        name = self._sel_user()
        if not name:
            return
        try:
            logic.set_role(self.user, name, role)
        except Exception as e:
            self.err(e)
            return
        self.refresh_users()
        self.info("role_changed")

    def delete_user(self):
        name = self._sel_user()
        if not name:
            return
        try:
            logic.delete_employee(self.user, name)
        except Exception as e:
            self.err(e)
            return
        self.refresh_users()
        self.info("emp_deleted")


if __name__ == "__main__":
    App().mainloop()
