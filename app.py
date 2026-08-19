"""
app.py
------
نقطة الدخول لتطبيق "قرّب". هذا الملف مسؤول عن "التنقل" (navigation) بس —
يقرر أي صفحات تظهر بالقائمة الجانبية حسب حالة تسجيل الدخول (st.navigation)،
عشان الزبون مثلاً ما يشوف صفحات خاصة بالمندوب أو الأسرة وبالعكس.

كل المنطق الفعلي لكل صفحة موجود بملفات pages/ — بما فيها الصفحة الرئيسية
نفسها (pages/0_الرئيسية.py). خليناها ملف مستقل زي باقي الصفحات (مو دالة
مسجّلة بـ st.Page(callable)) عشان st.switch_page() يقدر يرجع لها بسهولة
من أي صفحة ثانية (st.switch_page ما يقبل إلا مسار ملف حقيقي).

نشغّل التطبيق بالأمر:
    streamlit run app.py

الأيقونات كلها من نوع Material Icons (:material/xxx:) بدل الإيموجي —
شكل أبسط وأوحد بكل التطبيق. القائمة الكاملة للأسماء المتاحة موجودة بملف
streamlit/material_icon_names.py داخل مكتبة Streamlit نفسها.
"""

import streamlit as st
from db import get_client
from auth_helpers import current_role
from ui_helpers import t


# نبني قائمة الصفحات حسب حالة تسجيل الدخول الحالية — كل دور يشوف صفحاته بس
role = current_role()

pages = {}

# المندوب ما يحتاج يتصفح واجهة السوق الرئيسية (تصفح الأسر) — شغله كله
# بلوحته الخاصة، فما نعرض له قسم "الرئيسية/تسجيل الدخول" أصلاً
if role != "courier":
    pages[t("nav_section_main")] = [
        st.Page("pages/0_الرئيسية.py", title=t("nav_home"), icon=":material/home:", default=True),
        st.Page("pages/1_تسجيل_الدخول.py", title=t("nav_login"), icon=":material/login:"),
    ]

if role is None:
    pages[t("nav_section_new_account")] = [
        st.Page("pages/7_تسجيل_أسرة.py", title=t("nav_register_seller"), icon=":material/storefront:"),
        st.Page("pages/3_تسجيل_مندوب.py", title=t("nav_register_courier"), icon=":material/moped:"),
        st.Page("pages/8_تسجيل_زبون.py", title=t("nav_register_customer"), icon=":material/person_add:"),
    ]
elif role == "seller":
    pages[t("nav_section_seller")] = [
        st.Page("pages/5_طلبات_الأسرة.py", title=t("nav_my_orders"), icon=":material/receipt_long:"),
        st.Page("pages/10_قائمة_المنتجات.py", title=t("nav_product_menu"), icon=":material/restaurant_menu:"),
        st.Page("pages/15_إعدادات_الأسرة.py", title=t("nav_settings"), icon=":material/settings:"),
    ]
elif role == "courier":
    pages[t("nav_section_courier")] = [
        st.Page("pages/4_لوحة_المندوب.py", title=t("courier_dashboard_title"), icon=":material/local_shipping:", default=True),
        st.Page("pages/14_إعدادات_المندوب.py", title=t("nav_settings"), icon=":material/settings:"),
    ]
elif role == "customer":
    # عنوان القسم بالقائمة الجانبية يصير اسم الزبون نفسه بدل تسمية عامة
    # ("الزبون") — يعطي إحساس شخصي أكثر. القائمة الجانبية نفسها مخفية عن
    # الزبون (position="hidden" تحت) واستبدلناها بشريط تنقّل سفلي بأيقونات
    # (render_customer_bottom_nav بملف ui_helpers.py) — أقرب لتجربة تطبيقات
    # الجوال المطلوبة. الصفحات هنا لسا مسجّلة عادي عشان st.switch_page /
    # st.page_link يشتغلوا، بس بدون ما تظهر بالقائمة الجانبية.
    customer_rows = get_client().table("customers").select("name").eq("user_id", st.session_state["user_id"]).execute().data
    section_title = customer_rows[0]["name"] if customer_rows else t("nav_section_customer")
    pages[section_title] = [
        st.Page("pages/11_السلة.py", title=t("nav_cart"), icon=":material/shopping_cart:"),
        st.Page("pages/9_طلبات_الزبون.py", title=t("nav_my_orders"), icon=":material/receipt_long:"),
        st.Page("pages/13_الملف_الشخصي.py", title=t("nav_profile"), icon=":material/person:"),
    ]

nav_position = "hidden" if role == "customer" else "sidebar"
navigation = st.navigation(pages, position=nav_position)
navigation.run()
