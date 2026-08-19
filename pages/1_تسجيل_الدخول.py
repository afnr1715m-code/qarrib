"""
1_تسجيل_الدخول.py
--------------------
تسجيل دخول بإيميل/باسورد لحساب موجود مسبقاً.

بعد نجاح الدخول، ندوّر على صف بجدول sellers أول، وبعدين couriers، وبعدين
customers، عشان نعرف "دور" هذا المستخدم ونحفظه بـ session_state — باقي
الصفحات المحمية تعتمد على هذا الدور بالضبط.
"""

import streamlit as st
from db import get_client
from auth_helpers import sign_in, store_session, is_logged_in, current_role, render_logout_button
from gotrue.errors import AuthApiError
from ui_helpers import apply_rtl, render_language_switcher, render_page_title, t

st.set_page_config(page_title=f"{t('app_name')} | {t('login_title')}", page_icon=":material/login:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("login", t('login_title'))
st.caption(t("login_caption"))

supabase = get_client()

if is_logged_in():
    # بدل ما نعرض شاشة وسيطة ("أنتِ مسجلة دخول حالياً...") وننتظر ضغطة
    # على رابط، ننقل المستخدمة مباشرة لصفحتها الرئيسية حسب دورها —
    # st.switch_page() آمن هنا لأن هذا الجزء يشتغل بعد إعادة تحميل الصفحة
    # (rerun)، يعني app.py يكون خلاص بنى قائمة التنقل الصحيحة لهذا الدور.
    role = current_role()
    if role == "seller":
        st.switch_page("pages/5_طلبات_الأسرة.py")
    elif role == "courier":
        st.switch_page("pages/4_لوحة_المندوب.py")
    elif role == "customer":
        # الزبون يروح للصفحة الرئيسية (يتصفح الأسر) بدل صفحة طلباته مباشرة
        st.switch_page("pages/0_الرئيسية.py")

    st.stop()

with st.form("login_form"):
    email = st.text_input(t("field_email"))
    password = st.text_input(t("field_password"), type="password")

    submitted = st.form_submit_button(t("btn_login"))

if submitted:
    if not email or not password:
        st.error(t("login_err_empty"))
    else:
        try:
            auth_response = sign_in(supabase, email, password)
            user_id = auth_response.user.id

            # نحدد الدور: هل هذا المستخدم مسجل بجدول sellers، وإلا couriers، وإلا customers؟
            # مهم: بعد store_session() نسوي st.rerun() فوري بدل ما نعرض
            # رابط الصفحة مباشرة بنفس هذي الدورة — app.py يبني قائمة
            # التنقل حسب الدور بأول كل تشغيلة، فلو حاولنا نعرض رابط
            # لصفحة الدور الجديد بنفس اللحظة اللي غيّرنا فيها الدور،
            # الصفحة تلقى نفسها لسا مب مسجلة بـ st.navigation() ويصير خطأ.
            seller_row = supabase.table("sellers").select("id").eq("user_id", user_id).execute().data
            if seller_row:
                store_session(auth_response.session, role="seller")
                st.rerun()
            else:
                courier_row = supabase.table("couriers").select("id").eq("user_id", user_id).execute().data
                if courier_row:
                    store_session(auth_response.session, role="courier")
                    st.rerun()
                else:
                    customer_row = supabase.table("customers").select("id").eq("user_id", user_id).execute().data
                    if customer_row:
                        store_session(auth_response.session, role="customer")
                        st.rerun()
                    else:
                        st.error(t("login_err_no_profile"))
        except AuthApiError:
            st.error(t("login_err_bad_credentials"))
        except Exception as e:
            st.error(t("login_err_generic").format(e=e))
