"""
5_طلبات_الأسرة.py
--------------------
الأسرة المسجلة دخولها تشوف طلباتها الحالية (تحتاج تجهيز أو بانتظار
المندوب) بتبويب، وسجل طلباتها المسلّمة بتبويب ثاني — وتقدر تعلّم الطلب
"تم التجهيز" لما تخلص تحضيره.

دورة حياة الطلب (status):
pending   → لسا الأسرة ما جهزت
ready     → الأسرة خلصت التجهيز، بانتظار المندوب
delivered → المندوب سلّم الطلب (يتحدث من صفحة المندوب)
"""

import html
import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from ui_helpers import apply_rtl, apply_orders_theme, render_language_switcher, render_page_title, t, format_price

st.set_page_config(page_title=f"{t('app_name')} | {t('seller_orders_title')}", page_icon=":material/receipt_long:")
apply_rtl()
apply_orders_theme()
render_language_switcher()
render_logout_button()

render_page_title("receipt_long", t("seller_orders_title"), role="seller")
st.caption(t("seller_orders_caption"))

require_login("seller")

supabase = get_client()

# نجيب صف الأسرة الخاص بالمستخدمة المسجلة دخولها بس
seller_response = (
    supabase.table("sellers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
seller = seller_response.data[0]

st.write(t("welcome_name").format(name=seller["name"]))

orders_response = (
    supabase.table("orders")
    .select("*")
    .eq("seller_id", seller["id"])
    .order("created_at", desc=True)
    .execute()
)
orders = orders_response.data

active_orders = [o for o in orders if o["status"] != "delivered"]
past_orders = [o for o in orders if o["status"] == "delivered"]
# مبيعات "مكتملة" بمعنى الطلبات اللي فعلاً وصلت — الطلبات الحالية لسا ما
# اكتمل تحصيلها فعلياً (الدفع عند الاستلام)
total_sales = sum(float(o["total_price"]) for o in past_orders)

# شريط إحصائيات — أرقام حقيقية من بيانات الأسرة، بدون أي فلترة بالتاريخ
# (ما عندنا "هذا الشهر" فعلياً، فنعرض الإجمالي الكلي بدل ما نخترع رقم).
# ملاحظة مهمة: نبني كل HTML هنا كسطر واحد متواصل بدون مسافات بادئة —
# لو تركنا مسافات البادئة (indentation) الطبيعية لبايثون داخل الـ f-string،
# Markdown يفسّر أي سطر يبدأ بـ 4 مسافات فأكثر كـ "code block" ويطلع HTML
# خام كنص بدل ما يترسم كصفحة — بالذات لما نركّب أجزاء HTML من دوال ثانية
# بمستويات مسافات بادئة مختلفة (dedent التلقائي بـ Streamlit ما يقدر
# يوحّدها كلها بهذي الحالة).
stat_card = lambda val, lbl: f'<div class="qarrib-stat-card"><div class="val">{val}</div><div class="lbl">{html.escape(lbl)}</div></div>'
st.markdown(
    '<div class="qarrib-stats-row">'
    + stat_card(len(active_orders), t("seller_stat_current"))
    + stat_card(len(orders), t("seller_stat_total"))
    + stat_card(html.escape(format_price(total_sales)), t("seller_stat_sales"))
    + stat_card(f"{seller['prep_time_minutes']} د", t("seller_stat_prep_time"))
    + "</div>",
    unsafe_allow_html=True,
)

status_priority = {"pending": 0, "ready": 1}
active_orders_sorted = sorted(active_orders, key=lambda o: status_priority.get(o["status"], 99))

tab_current, tab_past = st.tabs([
    f"{t('seller_orders_current_tab')} ({len(active_orders)})",
    t("seller_orders_past_tab"),
])

with tab_current:
    if not active_orders_sorted:
        st.markdown(
            f'<div class="qarrib-empty-state"><h3>{html.escape(t("seller_no_current_orders"))}</h3></div>',
            unsafe_allow_html=True,
        )
    else:
        for order in active_orders_sorted:
            stage_class = "pending" if order["status"] == "pending" else "ready"
            stage_label = t("badge_pending") if order["status"] == "pending" else t("badge_ready")
            order_ref = order["id"][:8]

            items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute().data
            items_html = "".join(
                f'<div class="qarrib-oi-row"><span>{html.escape(item["product_name"])} × {item["quantity"]}</span>'
                f'<span class="price">{html.escape(format_price(item["quantity"] * float(item["unit_price"])))}</span></div>'
                for item in items
            )

            note_html = ""
            if order.get("order_details"):
                note_html = f'<div class="qarrib-oc-note">{html.escape(order["order_details"])}</div>'

            card_class = "qarrib-order-card new" if order["status"] == "pending" else "qarrib-order-card"
            total_line = html.escape(t("order_total_label").format(total=format_price(order["total_price"])))
            st.markdown(
                f'<div class="{card_class}">'
                f'<div class="qarrib-oc-head">'
                f'<span class="qarrib-oc-stage {stage_class}">{html.escape(stage_label)}</span>'
                f'<span class="qarrib-oc-id">#{html.escape(order_ref)}</span>'
                f'</div>'
                f'<div class="qarrib-oc-body">'
                f'<div class="qarrib-oc-customer">'
                f'<div class="name">{html.escape(order["customer_name"])}</div>'
                f'<div class="sub">{html.escape(order["customer_whatsapp"])}</div>'
                f'</div>'
                f'{items_html}'
                f'<div class="qarrib-oi-row"><span class="qarrib-oi-total">{total_line}</span></div>'
                f'{note_html}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if order["status"] == "pending":
                if st.button(t("btn_mark_ready"), icon=":material/task_alt:", key=f"ready_{order['id']}"):
                    supabase.table("orders").update({"status": "ready"}).eq("id", order["id"]).execute()
                    st.rerun()
            else:
                st.caption(t("seller_waiting_courier"))

with tab_past:
    if not past_orders:
        st.markdown(
            f'<div class="qarrib-empty-state"><h3>{html.escape(t("seller_no_past_orders"))}</h3></div>',
            unsafe_allow_html=True,
        )
    else:
        for order in past_orders:
            summary = f"✅ {order['customer_name']} · {format_price(order['total_price'])}"
            with st.expander(summary):
                st.write(t("order_customer_line").format(name=order["customer_name"], whatsapp=order["customer_whatsapp"]))
                items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute().data
                for item in items:
                    line_total = item["quantity"] * float(item["unit_price"])
                    st.write(t("order_item_line").format(qty=item["quantity"], name=item["product_name"], line_total=format_price(line_total)))
                st.write(t("order_total_display").format(total=format_price(order["total_price"])))
                if order.get("order_details"):
                    st.write(t("order_notes_display").format(notes=order["order_details"]))
