"""
8_تسجيل_زبون.py
------------------
تسجيل حساب زبون جديد: إنشاء حساب دخول (إيميل + باسورد) + بيانات بسيطة
(اسم ورقم واتساب) تستخدم لاحقاً لتعبئة فورم الطلب تلقائياً.

مهم: sign_up() وعملية إدراج صف customers لازم يستخدمون نفس كائن `supabase`
(نفس المتغير)، عشان الجلسة اللي تنعمل وقت sign_up تكون فعالة وقت الإدراج.
"""

import streamlit as st
from db import get_client
from auth_helpers import sign_up, store_session, render_logout_button
from gotrue.errors import AuthApiError
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t

st.set_page_config(page_title=f"{t('app_name')} | {t('customer_reg_title')}", page_icon=":material/person_add:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("person_add", t('customer_reg_title'), role="customer")
st.caption(t("customer_reg_caption"))

just_registered_name = st.session_state.pop("just_registered_customer_name", None)
if just_registered_name:
    st.success(t("customer_reg_success").format(name=just_registered_name))
    st.page_link("pages/11_السلة.py", label=t("customer_reg_go_order"), icon=":material/shopping_cart:")
    st.stop()

with st.form("customer_registration_form", clear_on_submit=True):
    st.subheader(t("section_login_info"))
    email = st.text_input(t("field_email"))
    password = st.text_input(t("field_password"), type="password", help=t("field_password_help"))

    st.subheader(t("section_customer_info"))
    name = st.text_input(t("field_your_name"))
    whatsapp_number = st.text_input(t("field_whatsapp"), placeholder=t("field_whatsapp_placeholder"))

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
                st.error(t("err_unexpected_signup_f"))
            else:
                store_session(auth_response.session, role="customer")

                supabase.table("customers").insert(
                    {
                        "user_id": auth_response.user.id,
                        "name": name,
                        "whatsapp_number": whatsapp_number,
                    }
                ).execute()

                st.session_state["just_registered_customer_name"] = name
                st.rerun()
        except AuthApiError as e:
            if "already registered" in str(e).lower():
                st.error(t("err_email_taken_f"))
            else:
                st.error(t("err_signup_generic").format(e=e))
        except Exception as e:
            st.error(t("err_save_generic").format(e=e))
