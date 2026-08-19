"""
4_لوحة_المندوب.py
--------------------
لوحة المندوب الموحّدة: تبديل حالة التوفّر، إحصائيات حقيقية (توصيلات
حالية + إجمالي)، تبويب للتوصيلات الحالية (بمسار استلام/تسليم)، وتبويب
لسجل التوصيلات المكتملة.

دمجنا هذي مع صفحة "طلبات المندوب" القديمة (كانت pages/6) بصفحة وحدة —
نفس فكرة دمج صفحات الأسرة والزبون.

ملاحظة صدق بيانات: ما عندنا عمود "delivered_at" (وقت التسليم الفعلي)
ولا نظام أرباح/تقييم — فالإحصائيات هنا أرقام حقيقية بس (عدد حالي +
إجمالي)، بدون "أرباح اليوم" أو "تقييم" مختلقة.
"""

import html
import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from ui_helpers import apply_rtl, apply_orders_theme, render_language_switcher, render_page_title, t, format_price

st.set_page_config(page_title=f"{t('app_name')} | {t('courier_dashboard_title')}", page_icon=":material/local_shipping:")
apply_rtl()
apply_orders_theme()
render_language_switcher()
render_logout_button()

render_page_title("local_shipping", t("courier_dashboard_title"), role="courier")
st.caption(t("courier_dashboard_caption"))

require_login("courier")

supabase = get_client()

courier_response = (
    supabase.table("couriers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
courier = courier_response.data[0]

# صف تبديل حالة التوفّر — نفس منطق الصفحة القديمة، بس بأعلى اللوحة
current_status = t("status_available") if courier["is_available"] else t("status_busy")
st.write(t("courier_status_welcome").format(name=courier["name"], status=current_status))

status_col1, status_col2 = st.columns(2)
with status_col1:
    if st.button(t("btn_become_available"), use_container_width=True):
        supabase.table("couriers").update({"is_available": True}).eq("id", courier["id"]).execute()
        st.success(t("status_updated_available"))
        st.rerun()
with status_col2:
    if st.button(t("btn_become_busy"), use_container_width=True):
        supabase.table("couriers").update({"is_available": False}).eq("id", courier["id"]).execute()
        st.success(t("status_updated_busy"))
        st.rerun()

st.divider()

orders = (
    supabase.table("orders")
    .select("*")
    .eq("courier_id", courier["id"])
    .order("created_at", desc=True)
    .execute()
    .data
)
current_deliveries = [o for o in orders if o["status"] == "ready"]
past_deliveries = [o for o in orders if o["status"] == "delivered"]

# نجيب الأسر مرة وحدة لعرض اسمها بنقطة "الاستلام من" (الطلب ما يخزن اسم
# الأسرة، بس seller_id)
sellers_by_id = {s["id"]: s for s in supabase.table("sellers").select("*").execute().data}

sell_col1, sell_col2 = st.columns(2)
with sell_col1:
    st.markdown(
        f'<div class="qarrib-stat-card"><div class="val">{len(current_deliveries)}</div>'
        f'<div class="lbl">{html.escape(t("courier_stat_current"))}</div></div>',
        unsafe_allow_html=True,
    )
with sell_col2:
    st.markdown(
        f'<div class="qarrib-stat-card"><div class="val">{len(past_deliveries)}</div>'
        f'<div class="lbl">{html.escape(t("courier_stat_total"))}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

tab_current, tab_history = st.tabs([
    f"{t('courier_tab_current')} ({len(current_deliveries)})",
    t("courier_tab_history"),
])

with tab_current:
    if not current_deliveries:
        st.markdown(
            f'<div class="qarrib-empty-state">'
            f'<h3>{html.escape(t("courier_no_current"))}</h3>'
            f'<p>{html.escape(t("courier_no_current_sub"))}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        for order in current_deliveries:
            seller = sellers_by_id.get(order["seller_id"], {})
            order_ref = order["id"][:8]

            items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute().data
            items_html = "".join(
                f'<div class="qarrib-oi-row"><span>{html.escape(item["product_name"])} × {item["quantity"]}</span></div>'
                for item in items
            )

            st.markdown(
                f'<div class="qarrib-order-card">'
                f'<div class="qarrib-oc-head">'
                f'<span class="qarrib-oc-stage ready">{html.escape(t("status_ready_courier"))}</span>'
                f'<span class="qarrib-oc-id">#{html.escape(order_ref)}</span>'
                f'</div>'
                f'<div class="qarrib-route">'
                f'<div class="qarrib-route-point">'
                f'<div class="qarrib-route-marker pickup">1</div>'
                f'<div class="qarrib-route-info">'
                f'<div class="tag">{html.escape(t("route_pickup_label"))}</div>'
                f'<div class="name">{html.escape(seller.get("name", "؟"))}</div>'
                f'<div class="sub">{html.escape(seller.get("whatsapp_number", ""))}</div>'
                f'</div></div>'
                f'<div class="qarrib-route-point">'
                f'<div class="qarrib-route-marker dropoff">2</div>'
                f'<div class="qarrib-route-info">'
                f'<div class="tag">{html.escape(t("route_dropoff_label"))}</div>'
                f'<div class="name">{html.escape(order["customer_name"])}</div>'
                f'<div class="sub">{html.escape(order["customer_whatsapp"])}</div>'
                f'</div></div>'
                f'</div>'
                f'<div class="qarrib-oc-body">{items_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if st.button(t("btn_mark_delivered"), icon=":material/task_alt:", key=f"delivered_{order['id']}"):
                supabase.table("orders").update({"status": "delivered"}).eq("id", order["id"]).execute()
                st.rerun()

with tab_history:
    if not past_deliveries:
        st.markdown(
            f'<div class="qarrib-empty-state"><h3>{html.escape(t("courier_no_history"))}</h3></div>',
            unsafe_allow_html=True,
        )
    else:
        for order in past_deliveries:
            seller = sellers_by_id.get(order["seller_id"], {})
            summary = f"✅ {seller.get('name', '؟')} ← {order['customer_name']} · {format_price(order['total_price'])}"
            with st.expander(summary):
                items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute().data
                for item in items:
                    line_total = item["quantity"] * float(item["unit_price"])
                    st.write(t("order_item_line").format(qty=item["quantity"], name=item["product_name"], line_total=format_price(line_total)))
                st.write(t("order_total_display").format(total=format_price(order["total_price"])))
