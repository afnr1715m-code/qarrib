"""
7_تسجيل_أسرة.py
------------------
تسجيل أسرة منتجة جديدة: إنشاء حساب دخول (إيميل + باسورد) + بيانات العمل.

مهم: sign_up() وعملية إدراج صف sellers لازم يستخدمون نفس كائن `supabase`
(نفس المتغير)، عشان الجلسة اللي تنعمل وقت sign_up تكون فعالة وقت الإدراج.
لو سوينا get_client() مرة ثانية بينها، بيكون عميل "زائر" عادي بدون صلاحية
الإدراج (لأن سياسة الحماية RLS تتطلب مستخدم مسجل دخول).
"""

import streamlit as st
from db import get_client
from auth_helpers import sign_up, store_session, render_logout_button
from gotrue.errors import AuthApiError
from ui_helpers import apply_rtl, category_label, render_language_switcher, render_page_title, t, PRODUCT_CATEGORIES

st.set_page_config(page_title=f"{t('app_name')} | {t('seller_reg_title')}", page_icon=":material/storefront:")
apply_rtl()
render_language_switcher()
render_logout_button()

render_page_title("storefront", t('seller_reg_title'), role="seller")
st.caption(t("seller_reg_caption"))

# لو جاية توّها من تسجيل ناجح (بعد rerun)، نعرض رسالة النجاح والرابط هنا
# بدل الفورم — بهذي اللحظة app.py يكون خلاص بنى قائمة تنقل الأسرة، فالرابط
# يشتغل بدون خطأ "Could not find page"
just_registered_name = st.session_state.pop("just_registered_seller_name", None)
if just_registered_name:
    st.success(t("seller_reg_success").format(name=just_registered_name))
    st.page_link("pages/5_طلبات_الأسرة.py", label=t("login_go_to_orders"), icon=":material/receipt_long:")
    st.stop()

with st.form("seller_registration_form", clear_on_submit=True):
    st.subheader(t("section_login_info"))
    email = st.text_input(t("field_email"))
    password = st.text_input(t("field_password"), type="password", help=t("field_password_help"))

    st.subheader(t("section_seller_info"))
    name = st.text_input(t("field_seller_name"))
    # قائمة تصنيفات ثابتة بدل نص حر — عشان فرز الصفحة الرئيسية حسب النوع
    # يشتغل صح ومتسق بين كل الأسر (بدل ما توصف كل أسرة منتجها بصياغة مختلفة)
    product_type = st.selectbox(t("field_product_type"), PRODUCT_CATEGORIES, format_func=category_label)
    prep_time_minutes = st.number_input(t("field_prep_time"), min_value=1, max_value=600, step=5)
    whatsapp_number = st.text_input(t("field_whatsapp"), placeholder=t("field_whatsapp_placeholder"))

    submitted = st.form_submit_button(t("btn_register"))

if submitted:
    if not email or not password or not name or not product_type or not whatsapp_number:
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
                store_session(auth_response.session, role="seller")

                # نفس كائن supabase (فيه جلسة المستخدم الجديد الحين)
                supabase.table("sellers").insert(
                    {
                        "user_id": auth_response.user.id,
                        "name": name,
                        "product_type": product_type,
                        "prep_time_minutes": int(prep_time_minutes),
                        "whatsapp_number": whatsapp_number,
                    }
                ).execute()

                st.session_state["just_registered_seller_name"] = name
                st.rerun()
        except AuthApiError as e:
            if "already registered" in str(e).lower():
                st.error(t("err_email_taken_f"))
            else:
                st.error(t("err_signup_generic").format(e=e))
        except Exception as e:
            st.error(t("err_save_generic").format(e=e))
