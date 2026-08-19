"""
14_إعدادات_المندوب.py
------------------------
المندوب يعدّل بياناته (الاسم، رقم واتساب، المدينة، نوع المركبة، رقم
اللوحة، البريد الإلكتروني) وكلمة المرور.

نفس ملاحظة الجلسة الموجودة بـ 13_الملف_الشخصي.py (صفحة الزبون المشابهة):
تحديث البريد/الباسورد يحتاج جلسة auth حقيقية مفعّلة بـ set_session()
صراحة، مو بس ربط postgrest.
"""

import streamlit as st
from db import get_client
from auth_helpers import require_login, render_logout_button
from location_helpers import render_location_picker
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t
from gotrue.errors import AuthApiError

st.set_page_config(page_title=f"{t('app_name')} | {t('settings_title')}", page_icon=":material/settings:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("settings", t("settings_title"), role="courier")
st.caption(t("settings_caption"))

require_login("courier")

supabase = get_client()

courier_response = (
    supabase.table("couriers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
courier = courier_response.data[0]


def _activate_auth_session():
    """تفعّل جلسة auth حقيقية وتحفظ التوكنات المجدّدة — لازمة قبل أي
    استدعاء لـ supabase.auth.update_user()."""
    auth_response = supabase.auth.set_session(
        st.session_state["access_token"], st.session_state["refresh_token"]
    )
    new_session = auth_response.session
    st.session_state["access_token"] = new_session.access_token
    st.session_state["refresh_token"] = new_session.refresh_token
    st.session_state["expires_at"] = new_session.expires_at
    return new_session.user.email


try:
    current_email = _activate_auth_session()
except Exception:
    current_email = ""

VEHICLE_TYPES = ["car", "motorcycle", "bicycle"]

st.subheader(t("section_profile_info"))

with st.form("courier_settings_form"):
    name = st.text_input(t("field_courier_name"), value=courier["name"])
    whatsapp = st.text_input(t("field_whatsapp"), value=courier["whatsapp_number"])
    city = st.text_input(t("field_courier_city"), value=courier.get("city") or "")
    current_vehicle = courier.get("vehicle_type") or "car"
    vehicle_index = VEHICLE_TYPES.index(current_vehicle) if current_vehicle in VEHICLE_TYPES else 0
    vehicle_type = st.selectbox(t("field_vehicle_type"), VEHICLE_TYPES, index=vehicle_index, format_func=lambda v: t(f"vehicle_{v}"))
    plate_number = st.text_input(t("field_plate_number"), value=courier.get("plate_number") or "")
    st.text_input(t("field_current_email"), value=current_email, disabled=True)
    new_email = st.text_input(t("field_new_email"), placeholder=current_email)

    submitted_info = st.form_submit_button(t("btn_save_profile"), icon=":material/save:")

if submitted_info:
    try:
        supabase.table("couriers").update(
            {
                "name": name,
                "whatsapp_number": whatsapp,
                "city": city or None,
                "vehicle_type": vehicle_type,
                "plate_number": plate_number or None,
            }
        ).eq("id", courier["id"]).execute()

        if new_email and new_email != current_email:
            supabase.auth.update_user({"email": new_email})
            st.success(t("profile_info_updated_success"))
            st.info(t("profile_email_change_notice"))
        else:
            st.success(t("profile_info_updated_success"))
    except AuthApiError as e:
        st.error(t("err_save_generic").format(e=e))
    except Exception as e:
        st.error(t("err_save_generic").format(e=e))

st.divider()

# موقعك الحالي — يُستخدم لاختيار أقرب مندوب متاح لموقع الأسرة عند تأكيد
# طلب جديد (courier_assignment.py). ملاحظة صدق: هذا موقع تحدده يدوياً
# بالضغط على الخريطة (تقدر تحدّثه من هنا وقت ما تبغى)، مو تتبع GPS حي
# مستمر — Streamlit ما فيها آلية لتحديث الموقع تلقائياً بالخلفية.
st.subheader(t("section_location"))
st.caption(t("location_hint_m"))
picked = render_location_picker(courier.get("latitude"), courier.get("longitude"), key="courier_location_picker")

if picked:
    st.caption(t("location_set_display").format(lat=round(picked[0], 5), lon=round(picked[1], 5)))
    if st.button(t("btn_save_location"), icon=":material/location_on:"):
        supabase.table("couriers").update({"latitude": picked[0], "longitude": picked[1]}).eq("id", courier["id"]).execute()
        st.success(t("location_updated_success"))
        st.rerun()
else:
    st.caption(t("location_not_set_m"))

st.divider()
st.subheader(t("section_change_password"))

with st.form("change_password_form", clear_on_submit=True):
    new_password = st.text_input(t("field_new_password"), type="password", help=t("field_password_help"))
    confirm_password = st.text_input(t("field_confirm_password"), type="password")

    submitted_password = st.form_submit_button(t("btn_save_password"), icon=":material/lock_reset:")

if submitted_password:
    if not new_password or not confirm_password:
        st.error(t("err_fill_required"))
    elif len(new_password) < 6:
        st.error(t("err_password_short"))
    elif new_password != confirm_password:
        st.error(t("err_passwords_dont_match"))
    else:
        try:
            supabase.auth.update_user({"password": new_password})
            st.success(t("password_updated_success"))
        except AuthApiError as e:
            st.error(t("err_save_generic").format(e=e))
        except Exception as e:
            st.error(t("err_save_generic").format(e=e))
