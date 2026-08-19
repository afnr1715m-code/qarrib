"""
13_الملف_الشخصي.py
---------------------
الزبون يعدّل بياناته الشخصية (الاسم، رقم واتساب، البريد الإلكتروني)
وكلمة المرور.

ملاحظة تقنية مهمة: db.py (get_client) بالمسار "الرخيص" العادي بس يربط
التوكن بـ postgrest (لطلبات الجداول) و storage — ما يفعّل جلسة حقيقية
بوحدة auth نفسها. تحديث البريد/الباسورد عبر supabase.auth.update_user()
يحتاج جلسة auth فعلية مفعّلة، فنسويها هنا صراحة بـ set_session() قبل أي
عملية تعديل، ونحفظ التوكنات المجدّدة (Supabase يبدّلها بكل استدعاء)
بـ session_state زي بالضبط اللي يسويه db.py بمساره "المكلف".
"""

import streamlit as st
from db import get_client
from auth_helpers import require_login, render_inline_logout_button
from location_helpers import render_location_picker
from ui_helpers import apply_rtl, render_customer_bottom_nav, render_language_switcher, render_page_title, t
from gotrue.errors import AuthApiError

st.set_page_config(page_title=f"{t('app_name')} | {t('profile_title')}", page_icon=":material/person:")
apply_rtl()
render_inline_logout_button()

render_page_title("person", t("profile_title"), role="customer")
st.caption(t("profile_caption"))

require_login("customer")
render_customer_bottom_nav(active="profile")

supabase = get_client()

customer_response = (
    supabase.table("customers").select("*").eq("user_id", st.session_state["user_id"]).execute()
)
customer = customer_response.data[0]


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

st.subheader(t("section_profile_info"))

with st.form("profile_info_form"):
    name = st.text_input(t("field_your_name"), value=customer["name"])
    whatsapp = st.text_input(t("field_whatsapp"), value=customer["whatsapp_number"])
    st.text_input(t("field_current_email"), value=current_email, disabled=True)
    new_email = st.text_input(t("field_new_email"), placeholder=current_email)

    submitted_info = st.form_submit_button(t("btn_save_profile"), icon=":material/save:")

if submitted_info:
    try:
        supabase.table("customers").update(
            {"name": name, "whatsapp_number": whatsapp}
        ).eq("id", customer["id"]).execute()

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

# موقع التسليم — نستخدمه مستقبلاً لتحسين تجربة التوصيل (زي عرض المسافة
# عن الأسرة). ما نربطه بمنطق التوزيع الحالي بعد (هذا يعتمد على موقع
# الأسرة بس)، بس نحفظه من الحين
st.subheader(t("section_location"))
st.caption(t("location_hint"))
picked = render_location_picker(customer.get("latitude"), customer.get("longitude"), key="customer_location_picker")

if picked:
    st.caption(t("location_set_display").format(lat=round(picked[0], 5), lon=round(picked[1], 5)))
    if st.button(t("btn_save_location"), icon=":material/location_on:"):
        supabase.table("customers").update({"latitude": picked[0], "longitude": picked[1]}).eq("id", customer["id"]).execute()
        st.success(t("location_updated_success"))
        st.rerun()
else:
    st.caption(t("location_not_set"))

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

st.divider()

# مبدّل اللغة نقله هنا (بدل القائمة الجانبية) — الزبون ما عنده قائمة
# جانبية أصلاً، وهذي الصفحة أقرب صفحة لمفهوم "الإعدادات" عنده
render_language_switcher(location="inline")
