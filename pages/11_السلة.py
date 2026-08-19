"""
11_السلة.py
-------------
صفحة الزبون الموحّدة: تصفح منتجات أسرة معيّنة (وصلها بالضغط على بطاقتها
بالصفحة الرئيسية)، إضافة للسلة، مراجعة السلة، وتأكيد الطلب (دفع عند
الاستلام) — كل شي بصفحة وحدة.

ما فيه قائمة اختيار أسرة هنا عمداً — اختيار الأسرة يصير من الصفحة
الرئيسية (زر "تصفحي المنتجات" بكل بطاقة أسرة)، اللي يحفظ الأسرة المختارة
بـ st.session_state["cart_seller_id"] قبل ما يودّي لهذي الصفحة.

السلة نفسها مخزّنة بـ st.session_state["cart"] (قاموس product_id → الكمية)
— تُفضّى تلقائياً لو الزبون اختار أسرة ثانية من الصفحة الرئيسية، أو بعد
ما يأكد طلبه.
"""

import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from courier_assignment import assign_next_courier
from ui_helpers import apply_rtl, category_label, render_language_switcher, render_page_title, t, format_price

st.set_page_config(page_title=f"{t('app_name')} | {t('cart_page_title')}", page_icon=":material/shopping_cart:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("shopping_cart", t("cart_page_title"), role="customer")
st.caption(t("cart_page_caption"))

require_login("customer")

supabase = get_client()

seller_id = st.session_state.get("cart_seller_id")
cart = st.session_state.get("cart", {})

selected_seller = None
if seller_id:
    seller_rows = supabase.table("sellers").select("*").eq("id", seller_id).execute().data
    if seller_rows:
        selected_seller = seller_rows[0]
    else:
        # الأسرة انحذفت بعد ما اختارتها الزبونة — نفضي السلة المرتبطة فيها
        st.session_state["cart"] = {}
        st.session_state.pop("cart_seller_id", None)
        cart = {}

if not selected_seller:
    st.info(t("cart_empty"))
    st.page_link("pages/0_الرئيسية.py", label=t("nav_home"), icon=":material/home:")
    st.stop()

customer_response = (
    supabase.table("customers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
customer = customer_response.data[0]

st.info(
    t("order_seller_info").format(
        product_type=category_label(selected_seller["product_type"]),
        prep_time=selected_seller["prep_time_minutes"],
    )
)
if selected_seller.get("advance_days", 0) > 0:
    st.warning(t("order_seller_advance_notice").format(days=selected_seller["advance_days"]))

products = (
    supabase.table("products").select("*").eq("seller_id", selected_seller["id"]).order("created_at").execute().data
)

st.divider()
st.subheader(t("section_browse_products"))

if not products:
    st.warning(t("order_no_products"))
else:
    for product in products:
        with st.container(border=True):
            if product.get("image_url"):
                st.image(product["image_url"], width=200)
            st.write(f"**{product['name']}** — {format_price(product['price'])}")
            if product["description"]:
                st.caption(product["description"])
            if st.button(t("btn_add_to_cart"), icon=":material/add_shopping_cart:", key=f"add_{product['id']}"):
                cart[product["id"]] = cart.get(product["id"], 0) + 1
                st.session_state["cart"] = cart
                st.rerun()

cart_product_ids = [pid for pid, qty in cart.items() if qty > 0]

st.divider()
st.subheader(t("section_cart"))

if not cart_product_ids:
    st.info(t("cart_empty"))
    st.stop()

products_by_id = {p["id"]: p for p in products}
# لو المنتج ما كان بقائمة الأسرة الحالية (مثلاً تغيّرت المنتجات)، نجيبه بطلب منفصل
missing_ids = [pid for pid in cart_product_ids if pid not in products_by_id]
if missing_ids:
    extra = supabase.table("products").select("*").in_("id", missing_ids).execute().data
    products_by_id.update({p["id"]: p for p in extra})

for product_id in cart_product_ids:
    product = products_by_id.get(product_id)
    if not product:
        continue  # المنتج انحذف نهائياً بعد ما انضاف للسلة

    quantity = cart[product_id]
    line_total = quantity * float(product["price"])

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(t("order_item_line").format(qty=quantity, name=product["name"], line_total=format_price(line_total)))
        with col2:
            if st.button(t("btn_remove_from_cart"), icon=":material/delete:", key=f"remove_{product_id}"):
                cart.pop(product_id, None)
                st.session_state["cart"] = cart
                st.rerun()

total_price = sum(cart[pid] * float(products_by_id[pid]["price"]) for pid in cart_product_ids if pid in products_by_id)
st.write(t("order_total_label").format(total=format_price(total_price)))

st.divider()
st.subheader(t("checkout_title"))

customer_name = st.text_input(t("field_your_name"), value=customer["name"])
customer_whatsapp = st.text_input(t("field_whatsapp"), value=customer["whatsapp_number"])
notes = st.text_area(t("order_notes_field"), placeholder=t("order_notes_placeholder"))

st.info(t("checkout_cod_notice"))

if st.button(t("btn_confirm_order"), icon=":material/task_alt:"):
    if not customer_name or not customer_whatsapp:
        st.error(t("err_fill_required"))
    else:
        try:
            # أقرب مندوب متاح لموقع الأسرة (لو الطرفين حدّدوا موقعهم)، وإلا
            # بالتناوب بين المتاحين — راجع courier_assignment.py
            assigned_courier = assign_next_courier(
                supabase,
                seller_lat=selected_seller.get("latitude"),
                seller_lon=selected_seller.get("longitude"),
            )

            order_response = supabase.table("orders").insert(
                {
                    "seller_id": selected_seller["id"],
                    "courier_id": assigned_courier["id"] if assigned_courier else None,
                    "customer_id": customer["id"],
                    "customer_name": customer_name,
                    "customer_whatsapp": customer_whatsapp,
                    "order_details": notes or None,
                    "total_price": total_price,
                    "status": "pending",
                }
            ).execute()
            order = order_response.data[0]

            order_items = [
                {
                    "order_id": order["id"],
                    "product_id": pid,
                    "product_name": products_by_id[pid]["name"],
                    "quantity": cart[pid],
                    "unit_price": products_by_id[pid]["price"],
                }
                for pid in cart_product_ids
                if pid in products_by_id
            ]
            supabase.table("order_items").insert(order_items).execute()

            # نفضي السلة بعد نجاح الإرسال
            st.session_state["cart"] = {}
            st.session_state.pop("cart_seller_id", None)

            st.success(
                t("order_success").format(
                    seller_name=selected_seller["name"],
                    prep_time=selected_seller["prep_time_minutes"],
                )
            )
            if not assigned_courier:
                st.warning(t("order_no_courier_warning"))

            st.page_link("pages/9_طلبات_الزبون.py", label=t("nav_my_orders"), icon=":material/receipt_long:")
        except Exception as e:
            st.error(t("order_err_generic").format(e=e))
