"""
tools.py - أدوات مساعدة: الباركود (EAN-13)، الفواتير والملصقات (HTML للطباعة)،
واتساب، النسخ الاحتياطي، وتصدير CSV/Excel.
"""
import base64
import csv
import glob
import html
import os
import random
import re
import shutil
import sys
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import database as db

# عند التشغيل كـ exe نستخدم مجلد الـ exe (وليس المجلد المؤقت) لحفظ الفواتير والنسخ والصور
BASE_DIR = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))


def folder(name):
    path = name if os.path.isabs(name) else os.path.join(BASE_DIR, name)
    os.makedirs(path, exist_ok=True)
    return path


def store_file(src, subdir):
    """ينسخ ملف (صورة منتج / لوجو) داخل مجلد البرنامج ويرجع اسمه."""
    name = f"{uuid.uuid4().hex[:10]}{os.path.splitext(src)[1].lower()}"
    shutil.copy(src, os.path.join(folder(subdir), name))
    return name


def open_html(content, filename, subdir):
    path = os.path.join(folder(subdir), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        if os.name == "nt":
            os.startfile(path)  # أضمن على ويندوز من رابط file:// (بيفتح إيدج بصفحة فاضية أحيانًا)
        else:
            webbrowser.open(Path(path).as_uri())
    except Exception:
        webbrowser.open(Path(path).as_uri())
    return path


# ----------------------------------------------------------------------
# الباركود EAN-13
# ----------------------------------------------------------------------
_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
_PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]
_INV = str.maketrans("01", "10")


def ean13_check_digit(d12):
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d12))
    return str((10 - s % 10) % 10)


def is_ean13(code):
    return len(code) == 13 and code.isdigit() and ean13_check_digit(code[:12]) == code[12]


def random_ean13():
    d = "20" + "".join(random.choice("0123456789") for _ in range(10))  # بادئة 2 = استخدام داخلي
    return d + ean13_check_digit(d)


def _ean13_bits(code):
    parity = _PARITY[int(code[0])]
    bits = "101"
    for i, ch in enumerate(code[1:7]):
        left = _L[int(ch)]
        bits += left if parity[i] == "L" else left.translate(_INV)[::-1]  # G = معكوس R
    bits += "01010"
    for ch in code[7:]:
        bits += _L[int(ch)].translate(_INV)  # R
    return bits + "101"


def barcode_svg(code, height=46, module=1.6):
    if not is_ean13(code):
        return ""
    bits, rects, i = _ean13_bits(code), [], 0
    while i < len(bits):
        if bits[i] == "1":
            j = i
            while j < len(bits) and bits[j] == "1":
                j += 1
            rects.append(f'<rect x="{i * module:.2f}" y="0" width="{(j - i) * module:.2f}" height="{height}"/>')
            i = j
        else:
            i += 1
    w = len(bits) * module
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{height}" '
            f'viewBox="0 0 {w:.2f} {height}" fill="#000">{"".join(rects)}</svg>')


# ----------------------------------------------------------------------
# الفاتورة الحرارية / PDF (تُفتح في المتصفح وتُطبع تلقائيًا: اختار الطابعة أو Save as PDF)
# ----------------------------------------------------------------------
def _logo_tag(settings):
    name = settings.get("logo", "")
    path = os.path.join(folder("assets"), name) if name else ""
    if not name or not os.path.isfile(path):
        return ""
    ext = os.path.splitext(path)[1].lower().strip(".")
    mime = {"jpg": "jpeg", "svg": "svg+xml"}.get(ext, ext)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f'<img class="logo" src="data:image/{mime};base64,{data}">'


def receipt_html(order, items, settings, L, change=None, auto_print=True):
    e = html.escape
    rows = ""
    for i in items:
        net = i["unit_price"] * i["quantity"] - i["discount"]
        disc = f" − {i['discount']:.2f}" if i["discount"] > 0 else ""
        rows += (f"<tr><td>{e(i['name'])}<br><small>{i['quantity']} × {i['unit_price']:.2f}{disc}</small></td>"
                 f"<td class='r'>{net:.2f}</td></tr>")

    def line(label, value, cls=""):
        return f"<tr class='{cls}'><td>{e(label)}</td><td class='r'>{value}</td></tr>"

    t = line(L["subtotal"], f"{order['subtotal']:.2f}")
    if order["discount"] > 0:
        t += line(L["discount"], f"− {order['discount']:.2f}")
    if order["vat"] > 0:
        t += line(L["vat"], f"{order['vat']:.2f}")
    t += line(L["total"], f"{order['total']:.2f}", "big")
    t += line(L["paid"], f"{order['paid']:.2f}")
    if order["total"] > order["paid"]:
        t += line(L["remaining"], f"{order['total'] - order['paid']:.2f}")
    if change:
        t += line(L["change"], f"{change:.2f}")
    when = order["created_at"].astimezone().strftime("%Y-%m-%d %H:%M")
    meta = (f"<div>{e(L['invoice'])} #{order['id']} &nbsp; {when}</div>"
            f"<div>{e(L['cashier'])}: {e(order['username'] or '')}</div>")
    if order["customer_name"]:
        meta += f"<div>{e(L['customer'])}: {e(order['customer_name'])}</div>"
    script = "<script>window.onload=()=>setTimeout(()=>window.print(),800)</script>" if auto_print else ""
    pbtn = '<div class="noprint c" style="margin:8px"><button style="font-size:16px;padding:6px 18px" onclick="window.print()">🖨 Print / طباعة</button></div>'
    return f"""<!doctype html><html dir="{L['dir']}"><head><meta charset="utf-8">
<title>{e(L['invoice'])} {order['id']}</title><style>
@page{{margin:2mm}} @media print{{.noprint{{display:none}}}} body{{width:72mm;margin:0 auto;font:12px Tahoma,Arial,sans-serif;color:#000}}
.c{{text-align:center}} .logo{{max-width:60mm;max-height:24mm}} table{{width:100%;border-collapse:collapse}}
td{{padding:2px 0;vertical-align:top}} .r{{text-align:end;white-space:nowrap}} hr{{border:0;border-top:1px dashed #000}}
.big td{{font-size:15px;font-weight:bold;border-top:1px solid #000}} small{{color:#333}}
</style></head><body>
<div class="c">{_logo_tag(settings)}<h3 style="margin:4px 0">{e(settings.get('shop_name',''))}</h3>
<div>{e(settings.get('shop_address',''))}</div><div>{e(settings.get('shop_phone',''))}</div></div><hr>
{meta}<hr><table>{rows}</table><hr><table>{t}</table><hr>
<div class="c">{e(L['thanks'])}</div>{pbtn}{script}</body></html>"""


def labels_html(products, copies, settings):
    """ملصقات باركود 48×28 مم (EAN-13)."""
    e = html.escape
    cells = ""
    for p in products:
        svg = barcode_svg(p["barcode"])
        for _ in range(copies):
            cells += (f"<div class='lb'><div class='sh'>{e(settings.get('shop_name', ''))}</div>"
                      f"<div class='nm'>{e(p['name'])}</div>{svg}<div class='bc'>{e(p['barcode'])}</div>"
                      f"<div class='pr'>{p['price']:.2f}</div></div>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Labels</title><style>
@page{{margin:5mm}} @media print{{.noprint{{display:none}}}} body{{margin:0;font:11px Tahoma,Arial,sans-serif}}
.wrap{{display:flex;flex-wrap:wrap;gap:2mm}}
.lb{{width:48mm;height:28mm;border:1px dashed #999;text-align:center;overflow:hidden;box-sizing:border-box;padding:1mm}}
.sh{{font-size:8px;color:#444}} .nm{{font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
svg{{width:90%;height:9mm}} .bc{{font-size:9px;letter-spacing:1px}} .pr{{font-size:13px;font-weight:bold}}
</style></head><body><div class="wrap">{cells}</div>
<div class="noprint" style="margin:8px"><button style="font-size:16px;padding:6px 18px" onclick="window.print()">🖨 Print / طباعة</button></div></body></html>"""


# ----------------------------------------------------------------------
# واتساب
# ----------------------------------------------------------------------
def whatsapp_link(phone, text, country_code="20"):
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return None
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = country_code + digits[1:]
    elif not digits.startswith(country_code) and len(digits) <= 10:
        digits = country_code + digits
    return f"https://wa.me/{digits}?text={quote(text)}"


# ----------------------------------------------------------------------
# النسخ الاحتياطي والتصدير
# ----------------------------------------------------------------------
def backup_sql(dest_dir):
    path = os.path.join(folder(dest_dir), f"goshop_backup_{datetime.now():%Y%m%d_%H%M%S}.sql")
    with open(path, "w", encoding="utf-8") as f:
        f.write("-- Go Shop backup (data only). Restore: run the app once, then execute this file.\n")
        db.dump_sql(f)
    return path


def backup_due(dest_dir, hours=24):
    files = glob.glob(os.path.join(folder(dest_dir), "goshop_backup_*.sql"))
    return not files or (time.time() - max(os.path.getmtime(f) for f in files)) > hours * 3600


def prune_backups(dest_dir, keep=30):
    files = sorted(glob.glob(os.path.join(folder(dest_dir), "goshop_backup_*.sql")))
    for f in files[:-keep]:
        os.remove(f)


def export_csv(dest_dir):
    """ملفات CSV (UTF-8) تُفتح مباشرة في Excel."""
    out = folder(os.path.join(dest_dir, f"export_{datetime.now():%Y%m%d_%H%M%S}"))
    for name, cols, rows in db.export_queries():
        with open(os.path.join(out, f"{name}.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
    return out