"""
auth_helpers.py
----------------
دوال مساعدة لتسجيل الدخول/الخروج، وحماية الصفحات اللي لازم تسجيل دخول.

الفكرة العامة:
- بعد نجاح تسجيل الدخول أو إنشاء حساب، نحفظ التوكنات + دور المستخدم
  (seller أو courier) بـ st.session_state. db.py يقرأ هذي التوكنات
  ويربطها بأي عميل Supabase جديد يتسوى (راجع db.py لتفاصيل أكثر).
- كل صفحة "خاصة" (زي حالة المندوب، أو طلبات الأسرة) تستدعي require_login()
  بأول سطر لها، وتتوقف تلقائياً لو المستخدم مب مسجل دخول بالدور الصحيح.
"""

import streamlit as st
from ui_helpers import t

ROLE_KEYS = {"seller": "role_seller", "courier": "role_courier", "customer": "role_customer"}


def role_label(role: str) -> str:
    """ترجع اسم الدور المترجم حسب اللغة الحالية (مثلاً "أسرة منتجة" أو "Home business")."""
    return t(ROLE_KEYS.get(role, role))


def sign_up(supabase, email: str, password: str):
    """تسجيل حساب جديد بإيميل وباسورد. ترجع كائن AuthResponse من supabase."""
    return supabase.auth.sign_up({"email": email, "password": password})


def sign_in(supabase, email: str, password: str):
    """تسجيل دخول بإيميل وباسورد موجودين مسبقاً."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def sign_out(supabase):
    """تسجيل خروج، وتنظيف كل بيانات الجلسة المحفوظة."""
    supabase.auth.sign_out()
    for key in ("access_token", "refresh_token", "expires_at", "user_id", "role"):
        st.session_state.pop(key, None)


def store_session(session, role: str):
    """
    تحفظ توكنات الجلسة + دور المستخدم (seller/courier) بـ st.session_state.
    تُستدعى بعد نجاح sign_up أو sign_in.
    """
    st.session_state["access_token"] = session.access_token
    st.session_state["refresh_token"] = session.refresh_token
    st.session_state["expires_at"] = session.expires_at
    st.session_state["user_id"] = session.user.id
    st.session_state["role"] = role


def is_logged_in() -> bool:
    return "access_token" in st.session_state


def current_role():
    return st.session_state.get("role")


def require_login(role: str):
    """
    توقف تنفيذ الصفحة (st.stop) لو المستخدم مب مسجل دخول بالدور المطلوب.
    role: "seller" أو "courier" أو "customer"

    المندوب بالسياق العادي يكون رجّال (زي كل موك-أبات المندوب اللي بعثتها
    المستخدمة)، فنستخدم صيغة مذكّرة للنص هنا بدل الصيغة المؤنثة الافتراضية
    المستخدمة بباقي التطبيق (الأسرة/الزبون).
    """
    if st.session_state.get("role") != role:
        warning_key = "require_login_warning_m" if role == "courier" else "require_login_warning"
        st.warning(t(warning_key).format(role=role_label(role)))
        st.page_link("pages/1_تسجيل_الدخول.py", label=t("go_to_login"), icon=":material/login:")
        st.stop()


def render_logout_button():
    """
    زر تسجيل خروج يظهر بالقائمة الجانبية بكل صفحة (لو المستخدم مسجل دخول)،
    عشان ما يحتاج يروح لصفحة "تسجيل الدخول" خصيصاً بس عشان يسجل خروج.
    تستدعيه كل صفحة بنفسها، بنفس أسلوب apply_rtl()/render_language_switcher().
    """
    if is_logged_in():
        from db import get_client  # استيراد هنا عشان نتفادى استيراد دائري بأعلى الملف

        role = current_role()
        caption_key = "login_already_in_m" if role == "courier" else "login_already_in"
        st.sidebar.divider()
        st.sidebar.caption(t(caption_key).format(role=role_label(role)))
        if st.sidebar.button(t("btn_logout"), icon=":material/logout:", key="sidebar_logout_btn"):
            sign_out(get_client())
            st.rerun()


def render_inline_logout_button():
    """
    نسخة من زر تسجيل الخروج بدون قائمة جانبية — أيقونة بخلفية دائرية خفيفة
    (كانت شفافة تمامًا بدون خلفية، بس صارت غير واضحة فوق نقش الخلفية،
    فرجّعنا لها خلفية بسيطة تخليها تبين كزر). تُستخدم بصفحات الزبون
    الأربعة (القائمة الجانبية مخفية عنها كلياً — position="hidden" بـ
    app.py — فما نقدر نحط الزر بالسايدبار زي باقي الصفحات).
    """
    if is_logged_in():
        from db import get_client

        st.markdown(
            """
            <style>
            .st-key-inline_logout_btn button {
                background: #FFFFFF; border: 1px solid #E8E2D2; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                color: #6B7A5C; padding: 6px; border-radius: 12px;
            }
            .st-key-inline_logout_btn button:hover {
                background: #FDF0E4; border-color: #F3DCC4; color: #C05A3E;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        col_spacer, col_btn = st.columns([8, 1])
        with col_btn:
            with st.container(key="inline_logout_btn"):
                if st.button(" ", icon=":material/power_settings_new:", key="inline_logout_click", help=t("btn_logout")):
                    sign_out(get_client())
                    st.rerun()
