"""
15_إعدادات_الأسرة.py
-----------------------
إعدادات الأسرة: الشعار، وقت التجهيز وأيام التجهيز المسبق، وموقع الاستلام.

كانت هذي الأقسام كلها بصفحة "قائمة المنتجات" (pages/10) — فصلناها لصفحة
مستقلة عشان "قائمة المنتجات" تختص بالمنتجات بس، بنفس فكرة صفحات إعدادات
المندوب/الزبون المنفصلة عن صفحاتهم الرئيسية.
"""

import uuid
from pathlib import Path

import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from location_helpers import render_location_picker
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t
from storage3.utils import StorageException

st.set_page_config(page_title=f"{t('app_name')} | {t('nav_settings')}", page_icon=":material/settings:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("settings", t("nav_settings"), role="seller")

require_login("seller")

supabase = get_client()

seller_response = (
    supabase.table("sellers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
seller = seller_response.data[0]

LOGO_BUCKET = "seller-logos"

# شعار الأسرة — bucket منفصل عن صور المنتجات عشان نفصل صلاحيات الحذف/الرفع
# بسياسات RLS مستقلة
st.subheader(t("section_seller_logo"))
if seller.get("logo_url"):
    st.image(seller["logo_url"], width=140)

logo_file = st.file_uploader(t("field_seller_logo_upload"), type=["png", "jpg", "jpeg", "webp"], key="logo_uploader")
if logo_file is not None and st.button(t("btn_save_logo"), icon=":material/photo_camera:"):
    try:
        ext = Path(logo_file.name).suffix.lower() or ".jpg"
        storage_path = f"{seller['id']}/{uuid.uuid4()}{ext}"
        supabase.storage.from_(LOGO_BUCKET).upload(
            storage_path,
            logo_file.getvalue(),
            file_options={"content-type": logo_file.type or "image/jpeg"},
        )
        new_logo_url = supabase.storage.from_(LOGO_BUCKET).get_public_url(storage_path)
        supabase.table("sellers").update({"logo_url": new_logo_url}).eq("id", seller["id"]).execute()
        st.success(t("logo_updated_success"))
        st.rerun()
    except StorageException as e:
        st.error(t("err_save_generic").format(e=e))
    except Exception as e:
        st.error(t("err_save_generic").format(e=e))

st.divider()

# وقت التجهيز وأيام التجهيز المسبق. .get() احترازي لعمود advance_days لو
# لسا ما نفّذت الأسرة هجرة SQL الجديدة
st.subheader(t("section_seller_prep_time"))
new_prep_time = st.number_input(
    t("field_prep_time"), min_value=1, max_value=600, step=5, value=seller["prep_time_minutes"]
)
new_advance_days = st.number_input(
    t("field_advance_days"), min_value=0, max_value=30, step=1, value=seller.get("advance_days", 0)
)
if st.button(t("btn_save_prep_time"), icon=":material/schedule:"):
    supabase.table("sellers").update(
        {"prep_time_minutes": int(new_prep_time), "advance_days": int(new_advance_days)}
    ).eq("id", seller["id"]).execute()
    st.success(t("prep_time_updated_success"))
    st.rerun()

st.divider()

# موقع الاستلام — يُستخدم لاختيار أقرب مندوب متاح عند تأكيد الطلب
# (courier_assignment.py). .get() احترازي لعمود latitude/longitude لو لسا
# ما نفّذت الأسرة هجرة SQL الجديدة
st.subheader(t("section_location"))
st.caption(t("location_hint"))
picked = render_location_picker(seller.get("latitude"), seller.get("longitude"), key="seller_location_picker")

if picked:
    st.caption(t("location_set_display").format(lat=round(picked[0], 5), lon=round(picked[1], 5)))
    if st.button(t("btn_save_location"), icon=":material/location_on:"):
        supabase.table("sellers").update({"latitude": picked[0], "longitude": picked[1]}).eq("id", seller["id"]).execute()
        st.success(t("location_updated_success"))
        st.rerun()
else:
    st.caption(t("location_not_set"))
