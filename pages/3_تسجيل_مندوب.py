"""
3_تسجيل_مندوب.py
-------------------
تسجيل مندوب توصيل جديد: إنشاء حساب دخول (إيميل + باسورد) + بيانات المندوب.

مهم: sign_up() وعملية إدراج صف couriers لازم يستخدمون نفس كائن `supabase`
(نفس المتغير)، عشان الجلسة اللي تنعمل وقت sign_up تكون فعالة وقت الإدراج.
"""

import streamlit as st
from db import get_client
from auth_helpers import sign_up, store_session, render_logout_button
from gotrue.errors import AuthApiError
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t

st.set_page_config(page_title=f"{t('app_name')} | {t('courier_reg_title')}", page_icon=":material/moped:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("moped", t('courier_reg_title'), role="courier")
st.caption(t("courier_reg_caption"))

just_registered_name = st.session_state.pop("just_registered_courier_name", None)
if just_registered_name:
    st.success(t("courier_reg_success").format(name=just_registered_name))
    st.page_link("pages/4_لوحة_المندوب.py", label=t("login_go_to_status"), icon=":material/local_shipping:")
    st.stop()

VEHICLE_TYPES = ["car", "motorcycle", "bicycle"]

with st.form("courier_registration_form", clear_on_submit=True):
    st.subheader(t("section_login_info"))
    email = st.text_input(t("field_email"))
    password = st.text_input(t("field_password"), type="password", help=t("field_password_help"))

    st.subheader(t("section_courier_info"))
    name = st.text_input(t("field_courier_name"))
    whatsapp_number = st.text_input(t("field_whatsapp"), placeholder=t("field_whatsapp_placeholder"))
    city = st.text_input(t("field_courier_city"))
    vehicle_type = st.selectbox(t("field_vehicle_type"), VEHICLE_TYPES, format_func=lambda v: t(f"vehicle_{v}"))
    plate_number = st.text_input(t("field_plate_number"))

    submitted = st.form_submit_button(t("btn_register"))

if submitted:
    if not email or not password or not name or not whatsapp_number:
        st.error(t("err_fill_required"))
    elif len(password) < 6:
        st.error(t("err_password_short"))
    else:
        try:
            supabase = get_client()
            auth_response = sign_up(supabase, email, password)

            if not auth_response.session:
                st.error(t("err_unexpected_signup_m"))
            else:
                store_session(auth_response.session, role="courier")

                # المندوب الجديد يبدأ "متاح" تلقائياً (is_available له قيمة افتراضية True)
                supabase.table("couriers").insert(
                    {
                        "user_id": auth_response.user.id,
                        "name": name,
                        "whatsapp_number": whatsapp_number,
                        "city": city or None,
                        "vehicle_type": vehicle_type,
                        "plate_number": plate_number or None,
                    }
                ).execute()

                st.session_state["just_registered_courier_name"] = name
                st.rerun()
        except AuthApiError as e:
            if "already registered" in str(e).lower():
                st.error(t("err_email_taken_m"))
            else:
                st.error(t("err_signup_generic").format(e=e))
        except Exception as e:
            st.error(t("err_save_generic").format(e=e))
