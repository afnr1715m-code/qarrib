"""
db.py
-----
هذا الملف مسؤول عن شيء واحد فقط: الاتصال بقاعدة بيانات Supabase.
كل الصفحات (app.py وملفات pages/) بتستورد منه دالة get_client() بدل ما كل صفحة
تسوي اتصال منفصل بنفسها.

بما إن التطبيق فيه تسجيل دخول (Supabase Auth)، get_client() كمان مسؤولة عن
"إرجاع" جلسة المستخدم المسجل دخوله (لو فيه) لكل عميل جديد تسويه، عشان
سياسات الحماية (RLS) بقاعدة البيانات تعرف مين المستخدم الحالي.
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv
from gotrue.errors import AuthApiError, AuthSessionMissingError
from supabase import create_client, Client

# load_dotenv() تقرأ ملف .env وتحط قيمه كمتغيرات بيئة (environment variables)
# هذا يخلينا نفصل المفاتيح السرية عن الكود نفسه
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# نطفي التوكن قبل انتهائه الفعلي بدقيقة، عشان ما نستخدم توكن أوشك ينتهي
TOKEN_REFRESH_MARGIN_SECONDS = 60


def get_client() -> Client:
    """
    ترجع كائن (client) جاهز للتواصل مع Supabase.

    لو المستخدم مسجل دخول (يعني فيه توكنات محفوظة بـ st.session_state من صفحة
    تسجيل الدخول/التسجيل)، نربط هذي الجلسة بالعميل الجديد عشان الطلبات
    اللي يسويها (select/insert/update) تُحتسب كطلبات "مستخدم مسجل دخول"
    بنظر قاعدة البيانات، مو "زائر مجهول".
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_URL أو SUPABASE_KEY غير موجودين. "
            "تأكد إنك أنشأت ملف .env بناءً على .env.example وعبّيت القيم الصحيحة."
        )

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    expires_at = st.session_state.get("expires_at")

    if access_token and refresh_token:
        needs_refresh = expires_at is None or time.time() >= expires_at - TOKEN_REFRESH_MARGIN_SECONDS

        if not needs_refresh:
            # مسار رخيص: بس نحط التوكن بالهيدر، بدون أي اتصال بالإنترنت
            client.postgrest.auth(access_token)
            # عميل التخزين (storage) نسخة منفصلة تماماً بهيدرز خاصة فيها،
            # postgrest.auth() ما يوصلها — لازم نربط التوكن فيها يدوياً وإلا
            # رفع/حذف صور المنتجات يفشل بخطأ صلاحيات غامض
            client.storage.session.headers["Authorization"] = f"Bearer {access_token}"
        else:
            # التوكن قارب ينتهي، لازم نجدده فعلياً
            try:
                auth_response = client.auth.set_session(access_token, refresh_token)
                new_session = auth_response.session
                # مهم: Supabase يبدّل refresh_token بكل تجديد، لازم نحفظ النسخة
                # الجديدة وإلا بيصير خطأ "Already Used" بالمرة الجاية
                st.session_state["access_token"] = new_session.access_token
                st.session_state["refresh_token"] = new_session.refresh_token
                st.session_state["expires_at"] = new_session.expires_at
                client.storage.session.headers["Authorization"] = f"Bearer {new_session.access_token}"
            except (AuthApiError, AuthSessionMissingError):
                # الجلسة صارت غير صالحة (منتهية فعلاً أو ملغاة) - ننظف الجلسة
                # المحفوظة بصمت. كل صفحة محمية تتحقق بنفسها من وجود الجلسة
                # وتوجّه المستخدم لصفحة تسجيل الدخول لو ما لقتها.
                for key in ("access_token", "refresh_token", "expires_at", "user_id", "role"):
                    st.session_state.pop(key, None)

    return client
