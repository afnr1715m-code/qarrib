"""
9_طلبات_الزبون.py
--------------------
الزبون المسجل دخوله يتابع طلباته الحالية (لسا ما وصلت) بمتتبع خطوات لكل
طلب، وله تبويب ثاني لسجل الطلبات المسلّمة (قابل للطي، بدون أزرار تحديث —
تحديث الحالة من صلاحية الأسرة والمندوب فقط).
"""

import html
import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from ui_helpers import apply_rtl, apply_orders_theme, render_customer_bottom_nav, render_language_switcher, render_page_title, t, format_price

st.set_page_config(page_title=f"{t('app_name')} | {t('customer_orders_title')}", page_icon=":material/receipt_long:")
apply_rtl()
apply_orders_theme()
render_language_switcher()
render_logout_button()

render_page_title("receipt_long", t("customer_orders_title"), role="customer")
st.caption(t("customer_orders_caption"))

require_login("customer")
render_customer_bottom_nav(active="orders")

supabase = get_client()

customer_response = (
    supabase.table("customers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
customer = customer_response.data[0]

st.write(t("welcome_name").format(name=customer["name"]))

orders_response = (
    supabase.table("orders")
    .select("*")
    .eq("customer_id", customer["id"])
    .order("created_at", desc=True)
    .execute()
)
orders = orders_response.data

# الطلب ما يخزن اسم الأسرة، بس seller_id — نجيب كل الأسر مرة وحدة ونربطها
# بالـ id عشان نعرض اسم كل أسرة بكل طلب بدون استعلام منفصل لكل طلب
sellers_by_id = {s["id"]: s for s in supabase.table("sellers").select("*").execute().data}

active_orders = [o for o in orders if o["status"] != "delivered"]
past_orders = [o for o in orders if o["status"] == "delivered"]

STEP_LABELS = [t("step_received"), t("step_preparing"), t("step_ready"), t("step_delivered")]
# دورة الحياة الحقيقية عندنا 3 حالات بس (pending/ready/delivered) — نطابقها
# مع 4 خطوات بصرية: "تم الاستلام" دايماً محقق بمجرد إنشاء الطلب
STATUS_STEP_INDEX = {"pending": 1, "ready": 2, "delivered": 3}


# ملاحظة مهمة: كل HTML هنا يُبنى كسطر واحد متواصل بدون مسافات بادئة —
# Markdown يفسّر أي سطر يبدأ بـ 4 مسافات فأكثر كـ "code block" ويطلع HTML
# خام كنص بدل ما يترسم، بالذات لما نركّب أجزاء HTML من دوال بمستويات
# مسافات بادئة مختلفة (dedent التلقائي بـ Streamlit ما يقدر يوحّدها).


def render_order_items_html(order_id):
    items = supabase.table("order_items").select("*").eq("order_id", order_id).execute().data
    return "".join(
        f'<div class="qarrib-oi-row"><span>{html.escape(item["product_name"])} × {item["quantity"]}</span>'
        f'<span class="price">{html.escape(format_price(item["quantity"] * float(item["unit_price"])))}</span></div>'
        for item in items
    )


def render_current_order_card(order):
    seller = sellers_by_id.get(order["seller_id"], {})
    seller_name = (seller.get("name") or "؟").strip()
    step_index = STATUS_STEP_INDEX.get(order["status"], 1)
    fill_pct = (step_index / (len(STEP_LABELS) - 1)) * 100

    steps_html = ""
    for i, lbl in enumerate(STEP_LABELS):
        state = "done" if i < step_index else ("current" if i == step_index else "")
        circle = "✓" if i < step_index else ""
        steps_html += f'<div class="qarrib-step {state}"><div class="circle">{circle}</div><div class="lbl">{html.escape(lbl)}</div></div>'

    courier_html = ""
    if order["status"] == "ready" and order.get("courier_id"):
        courier_rows = supabase.table("couriers").select("*").eq("id", order["courier_id"]).execute().data
        if courier_rows:
            courier = courier_rows[0]
            courier_html = (
                '<div class="qarrib-courier-box">'
                f'<div class="avatar">{html.escape((courier["name"] or "؟")[0])}</div>'
                '<div class="info">'
                f'<b>{html.escape(courier["name"])}</b>'
                f'<span>{html.escape(t("courier_assigned_sub"))}</span>'
                '</div></div>'
            )

    note_html = ""
    if order.get("order_details"):
        note_html = f'<div class="qarrib-oc-note">{html.escape(order["order_details"])}</div>'

    prep_time = seller.get("prep_time_minutes")
    prep_line = t("customer_order_prep_estimate").format(prep_time=prep_time) if prep_time is not None else ""
    total_line = html.escape(t("order_total_label").format(total=format_price(order["total_price"])))

    st.markdown(
        f'<div class="qarrib-order-card">'
        f'<div class="qarrib-oc-head"><div>'
        f'<div style="font-weight:800; font-size:16px; color:var(--green-900);">{html.escape(seller_name)}</div>'
        f'<div style="font-size:12.5px; color:var(--muted); margin-top:2px;">{html.escape(prep_line)}</div>'
        f'</div></div>'
        f'<div class="qarrib-tracker"><div class="qarrib-steps">'
        f'<div class="qarrib-track-line"></div>'
        f'<div class="qarrib-track-fill" style="width:{fill_pct}%"></div>'
        f'{steps_html}'
        f'</div></div>'
        f'<div class="qarrib-oc-body">'
        f'{render_order_items_html(order["id"])}'
        f'<div class="qarrib-oi-row"><span class="qarrib-oi-total">{total_line}</span></div>'
        f'{note_html}'
        f'{courier_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


tab_current, tab_history = st.tabs([t("customer_orders_active_section"), t("customer_orders_past_section")])

with tab_current:
    if not active_orders:
        st.markdown(
            f'<div class="qarrib-empty-state">'
            f'<h3>{html.escape(t("customer_no_active_orders"))}</h3>'
            f'<p>{html.escape(t("customer_no_active_orders_sub"))}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/11_السلة.py", label=t("nav_cart"), icon=":material/shopping_cart:")
    else:
        for order in active_orders:
            render_current_order_card(order)

with tab_history:
    if not past_orders:
        st.markdown(
            f'<div class="qarrib-empty-state"><h3>{html.escape(t("customer_no_past_orders"))}</h3></div>',
            unsafe_allow_html=True,
        )
    else:
        for order in past_orders:
            seller = sellers_by_id.get(order["seller_id"], {})
            summary = f"✅ {seller.get('name', '؟')} · {format_price(order['total_price'])}"
            with st.expander(summary):
                items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute().data
                for item in items:
                    line_total = item["quantity"] * float(item["unit_price"])
                    st.write(t("order_item_line").format(qty=item["quantity"], name=item["product_name"], line_total=format_price(line_total)))
                st.write(t("order_total_display").format(total=format_price(order["total_price"])))
                if order.get("order_details"):
                    st.write(t("order_notes_display").format(notes=order["order_details"]))
