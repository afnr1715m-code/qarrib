"""
10_قائمة_المنتجات.py
-----------------------
الأسرة المسجلة دخولها تدير قائمة منتجاتها: تضيف منتج جديد (اسم + سعر + وصف
اختياري + صورة اختيارية)، وتشوف قائمة منتجاتها الحالية مع خيار حذف أي منتج.

هذي القائمة هي اللي تظهر للزبون بصفحة "طلب جديد" لما يختار هذي الأسرة.

الصور تُخزّن بـ Supabase Storage (bucket اسمه "product-images"، عام
القراءة). كل صورة تُحفظ بمسار "{seller_id}/{اسم عشوائي}.{امتداد}" —
هذا المسار هو أساس التحقق من الملكية بسياسات storage.objects.
"""

import uuid
from pathlib import Path

import streamlit as st
from db import get_client, SUPABASE_URL
from auth_helpers import require_login, render_logout_button
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t, format_price
from storage3.utils import StorageException

st.set_page_config(page_title=f"{t('app_name')} | {t('menu_title')}", page_icon=":material/restaurant_menu:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("restaurant_menu", t('menu_title'), role="seller")
st.caption(t("menu_caption"))

require_login("seller")

supabase = get_client()

BUCKET = "product-images"

seller_response = (
    supabase.table("sellers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
seller = seller_response.data[0]

with st.form("add_product_form", clear_on_submit=True):
    name = st.text_input(t("field_product_name"))
    price = st.number_input(t("field_product_price"), min_value=0.0, step=0.5, format="%.2f")
    description = st.text_input(t("field_product_description"), placeholder=t("field_product_description_placeholder"))
    image_file = st.file_uploader(t("field_product_image"), type=["png", "jpg", "jpeg", "webp"])

    submitted = st.form_submit_button(t("btn_add_product"), icon=":material/add_business:")

if submitted:
    if not name or price <= 0:
        st.error(t("err_fill_required"))
    else:
        try:
            image_url = None
            if image_file is not None:
                ext = Path(image_file.name).suffix.lower() or ".jpg"
                storage_path = f"{seller['id']}/{uuid.uuid4()}{ext}"
                supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    image_file.getvalue(),
                    file_options={"content-type": image_file.type or "image/jpeg"},
                )
                image_url = supabase.storage.from_(BUCKET).get_public_url(storage_path)

            supabase.table("products").insert(
                {
                    "seller_id": seller["id"],
                    "name": name,
                    "price": price,
                    "description": description or None,
                    "image_url": image_url,
                }
            ).execute()
            st.success(t("product_added_success").format(name=name))
        except StorageException as e:
            st.error(t("err_save_generic").format(e=e))
        except Exception as e:
            st.error(t("err_save_generic").format(e=e))

st.divider()
st.subheader(t("section_current_products"))

products_response = (
    supabase.table("products").select("*").eq("seller_id", seller["id"]).order("created_at").execute()
)
products = products_response.data

if not products:
    st.info(t("no_products_yet"))
else:
    for product in products:
        with st.container(border=True):
            if product.get("image_url"):
                st.image(product["image_url"], width=200)
            st.write(f"**{product['name']}** — {format_price(product['price'])}")
            if product["description"]:
                st.caption(product["description"])
            if st.button(t("btn_delete_product"), icon=":material/delete:", key=f"delete_{product['id']}"):
                if product.get("image_url"):
                    prefix = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/"
                    if product["image_url"].startswith(prefix):
                        try:
                            supabase.storage.from_(BUCKET).remove([product["image_url"][len(prefix):]])
                        except StorageException:
                            pass  # تنظيف التخزين مو حرج، ما نوقف حذف المنتج لو فشل
                supabase.table("products").delete().eq("id", product["id"]).execute()
                st.success(t("product_deleted_success"))
                st.rerun()
