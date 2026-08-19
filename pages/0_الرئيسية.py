"""
0_الرئيسية.py
----------------
الصفحة الرئيسية: تصفح الأسر المنتجة، فرز/ترتيب، وأيقونة حساب مضغوطة.

كانت هذي الصفحة دالة (home_page) جوا app.py نفسها (مسجّلة عبر
st.Page(home_page, ...))، بس هذا كان يمنع st.switch_page() من الرجوع
لها بسهولة (st.switch_page ما يقبل إلا مسار ملف حقيقي، مو دالة) — فصلناها
لملف مستقل زي باقي الصفحات، ونرجّع لها الحين بـ:
    st.switch_page("pages/0_الرئيسية.py")
"""

import html
from collections import Counter
import streamlit as st
from db import get_client
from auth_helpers import current_role, role_label, render_logout_button, render_inline_logout_button
from ui_helpers import apply_rtl, apply_home_theme, category_label, render_customer_bottom_nav, render_language_switcher, t, PRODUCT_CATEGORIES

st.set_page_config(page_title=t("app_name"), page_icon=":material/home:")
apply_rtl()
apply_home_theme()

role = current_role()

# الزبون ما عنده قائمة جانبية أصلاً (مخفية بـ app.py)، فنعرض له زر خروج
# مضغوط بالمتن + شريط الأيقونات السفلي بدلاً من عناصر السايدبار العادية
if role == "customer":
    render_inline_logout_button()
    render_customer_bottom_nav(active="home")
else:
    render_language_switcher()
    render_logout_button()

supabase = get_client()
sellers = supabase.table("sellers").select("*").execute().data
product_types = sorted({s["product_type"] for s in sellers}) if sellers else []

# صف الترحيب ("أهلاً" + سؤال) + أيقونة حساب مضغوطة (popover) يمين —
# بالضبط ترتيب الموك-أب: تحية شخصية بدل شعار التطبيق، وأيقونة حساب
# صغيرة بجنبها مو عمود جانبي كامل. الزبون ما يحتاج هذي الأيقونة أصلاً —
# شريط التنقل السفلي عنده فيه تبويب "حسابي" مخصص لنفس الغرض بالضبط، فتكرارها
# هنا زيادة بلا داعي (render_customer_bottom_nav تحت)
if role == "customer":
    st.caption(t("home_greeting_hello"))
    st.subheader(t("home_greeting_question"))
    st.caption(t("home_welcome_role").format(role=role_label(role)))
else:
    greet_col, account_col = st.columns([5, 1])

    with greet_col:
        st.caption(t("home_greeting_hello"))
        st.subheader(t("home_greeting_question"))
        if role is not None:
            st.caption(t("home_welcome_role").format(role=role_label(role)))

    with account_col:
        # بدون تسمية نصية وبدون تمديد العرض — يطلع زر دائري مضغوط فيه
        # الأيقونة بس، أقرب لشكل أيقونة الحساب الصغيرة بأعلى يمين الموك-أب
        with st.popover(" ", icon=":material/account_circle:", help=t("home_account_menu")):
            if role is None:
                st.page_link("pages/1_تسجيل_الدخول.py", label=t("nav_login"), icon=":material/login:")
                st.caption(t("home_new_account"))
                st.page_link("pages/7_تسجيل_أسرة.py", label=t("home_register_seller_link"), icon=":material/storefront:")
                st.page_link("pages/3_تسجيل_مندوب.py", label=t("home_register_courier_link"), icon=":material/moped:")
                st.page_link("pages/8_تسجيل_زبون.py", label=t("home_register_customer_link"), icon=":material/person_add:")
            elif role == "seller":
                st.page_link("pages/5_طلبات_الأسرة.py", label=t("nav_my_orders"), icon=":material/receipt_long:")
                st.page_link("pages/10_قائمة_المنتجات.py", label=t("nav_product_menu"), icon=":material/restaurant_menu:")
                st.page_link("pages/15_إعدادات_الأسرة.py", label=t("nav_settings"), icon=":material/settings:")
            elif role == "courier":
                st.page_link("pages/4_لوحة_المندوب.py", label=t("courier_dashboard_title"), icon=":material/local_shipping:")

# شريط بحث + رقاقات فرز — يجيان مباشرة تحت الترحية زي الموك-أب، قبل
# البانر مو بعده
search_query = ""
selected_type = t("filter_all")
if sellers:
    search_query = st.text_input(
        t("home_search_placeholder"),
        label_visibility="collapsed",
        placeholder=t("home_search_placeholder"),
    )
    # نستخدم قائمة التصنيفات الثابتة PRODUCT_CATEGORIES هنا (مو
    # product_types المشتقة من بيانات الأسر الفعلية) — عشان كل
    # التصنيفات الستة تظهر كخيارات فرز دايماً، حتى لو ما فيه أسرة
    # مسجلة بتصنيف معين بعد
    chip_options = [t("filter_all")] + PRODUCT_CATEGORIES
    # أيقونة Material لكل رقاقة (مو إيموجي الجوال العادية) — st.pills
    # يدعم أيقونات حقيقية لو format_func رجّع نص يبدأ بـ ":material/x:"
    # (يفصلها ويرسلها للواجهة كأيقونة منفصلة، بنفس طريقة icon= بالأزرار)
    CATEGORY_ICON = {
        "sweets": "cake",
        "baked": "bakery_dining",
        "savory": "tapas",
        "beverages": "local_cafe",
        "main_dishes": "lunch_dining",
        "other": "category",
    }

    # نلف الرقاقات بـ container له key ثابت — Streamlit يضيف كلاس
    # "st-key-<الاسم>" على الحاوية تلقائياً، فنقدر نصمم شكل الرقاقات
    # بالضبط بـ CSS (apply_home_theme) بدون ما نأثر على أي زر ثاني
    # بالتطبيق (خلاف تحديد `.stApp button` عام كان يغيّر شكل كل الأزرار)
    with st.container(key="home_category_chips"):
        selected_type = st.pills(
            t("home_filter_by_type"),
            chip_options,
            default=t("filter_all"),
            format_func=lambda opt: f":material/apps: {opt}" if opt == t("filter_all") else f":material/{CATEGORY_ICON.get(opt, 'restaurant')}: {category_label(opt)}",
        )

    # خيارات الترتيب — الأربعة اللي ممكنة بالبيانات الموجودة حالياً
    # ("الأقرب لي" يحتاج مواقع، و"الأعلى تقييماً" يحتاج نظام تقييمات —
    # مو موجودين بعد)
    SORT_ICON = {
        "default": "tune",
        "newest": "fiber_new",
        "fastest_prep": "bolt",
        "most_ordered": "local_fire_department",
        "lowest_price": "sell",
    }
    sort_options = ["default", "newest", "fastest_prep", "most_ordered", "lowest_price"]
    with st.container(key="home_sort_chips"):
        sort_by = st.pills(
            t("home_sort_by"),
            sort_options,
            default="default",
            format_func=lambda opt: f":material/{SORT_ICON.get(opt, 'tune')}: {t(f'sort_{opt}')}",
        )

# بانر ترحيبي زخرفي (زي بانر الموك-أب) — بس عرض، مالوش وظيفة تفاعلية
st.markdown(
    f"""
    <div class="qarrib-banner">
        <h3>{html.escape(t('home_banner_title'))}</h3>
        <p>{html.escape(t('home_banner_subtitle'))}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not sellers:
    st.info(t("home_no_sellers_found"))
else:
    # شريط إحصائيات صغير (عدد الأسر + عدد الأنواع) — يملي الفراغ اللي
    # كان تحت البانر مباشرة ويعطي إحساس إن فيه نشاط فعلي بالتطبيق
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        st.markdown(
            f"""
            <div class="qarrib-stat">
                <span class="qarrib-stat-num">{len(sellers)}</span>
                <span class="qarrib-stat-label">{html.escape(t('home_browse_sellers'))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_col2:
        st.markdown(
            f"""
            <div class="qarrib-stat">
                <span class="qarrib-stat-num">{len(product_types)}</span>
                <span class="qarrib-stat-label">{html.escape(t('home_filter_by_type'))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    filtered = sellers
    if selected_type and selected_type != t("filter_all"):
        filtered = [s for s in filtered if s["product_type"] == selected_type]
    if search_query:
        q = search_query.strip().lower()
        filtered = [s for s in filtered if q in s["name"].lower() or q in s["product_type"].lower()]

    if sort_by == "newest":
        filtered = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
    elif sort_by == "fastest_prep":
        filtered = sorted(filtered, key=lambda s: s["prep_time_minutes"])
    elif sort_by == "most_ordered":
        # نعد عدد الطلبات لكل أسرة من جدول orders — ما فيه عمود جاهز
        # لهذا، فنجيب seller_id لكل الطلبات ونعدها يدوياً بايثون
        order_rows = supabase.table("orders").select("seller_id").execute().data
        order_counts = Counter(row["seller_id"] for row in order_rows)
        filtered = sorted(filtered, key=lambda s: order_counts.get(s["id"], 0), reverse=True)
    elif sort_by == "lowest_price":
        # أرخص سعر منتج لكل أسرة — الأسر اللي ما عندها منتجات بعد تروح
        # آخر الترتيب (float("inf")) بدل ما تختفي من القائمة
        product_rows = supabase.table("products").select("seller_id, price").execute().data
        min_price_by_seller = {}
        for row in product_rows:
            sid, price = row["seller_id"], float(row["price"])
            if sid not in min_price_by_seller or price < min_price_by_seller[sid]:
                min_price_by_seller[sid] = price
        filtered = sorted(filtered, key=lambda s: min_price_by_seller.get(s["id"], float("inf")))

    st.markdown(
        f"""
        <div class="qarrib-section-head">
            <span class="qarrib-dot"></span>
            <span>{html.escape(t('home_browse_sellers'))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not filtered:
        st.info(t("home_no_sellers_found"))
    else:
        # شبكة بطاقات بثلاث أعمدة (زي شبكة الأسر بالموك-أب) بدل قائمة
        # طويلة رأسية — كل بطاقة فيها دائرة حرف أول الاسم + الاسم +
        # نوع المنتج + شارة وقت التجهيز
        cols = st.columns(3)
        for i, seller in enumerate(filtered):
            with cols[i % 3]:
                name = seller["name"].strip() or "؟"
                # الأسر اللي رفعت شعار تعرض صورته بدل دائرة الحرف الأولى
                if seller.get("logo_url"):
                    thumb_html = f'<img src="{html.escape(seller["logo_url"])}" class="qarrib-seller-thumb" style="object-fit:cover;" alt="">'
                else:
                    thumb_html = f'<div class="qarrib-seller-thumb">{html.escape(name[0])}</div>'
                st.markdown(
                    f"""
                    <div class="qarrib-seller-card">
                        {thumb_html}
                        <h4>{html.escape(seller['name'])}</h4>
                        <p>{html.escape(category_label(seller['product_type']))}</p>
                        <span class="qarrib-seller-badge">{html.escape(t('home_seller_prep_short').format(prep_time=seller['prep_time_minutes']))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # زر "تصفحي المنتجات" — يودّي مباشرة لصفحة السلة بهذي الأسرة
                # محددة، بدل ما تكون هناك قائمة اختيار أسرة بصفحة السلة نفسها
                if role in (None, "customer") and st.button(
                    t("home_view_products"), key=f"view_products_{seller['id']}",
                    icon=":material/storefront:", use_container_width=True,
                ):
                    if st.session_state.get("cart_seller_id") != seller["id"]:
                        st.session_state["cart"] = {}
                    st.session_state["cart_seller_id"] = seller["id"]
                    st.switch_page("pages/11_السلة.py")

# صندوق دعوة لتسجيل أسرة جديدة (زي "عندك مطبخ؟" بالموك-أب) — نعرضه
# لغير المسجلين دخول بس. صفحة "تسجيل أسرة" مسجّلة بـ st.navigation() بس
# لما role is None (راجع app.py) — لو عرضنا الرابط لمندوب أو زبون مسجل
# دخول، الصفحة تكون غير مسجّلة بنفس هذي الدورة وتنكسر بخطأ
# "Could not find page"
if role is None:
    st.markdown(
        f"""
        <div class="qarrib-cta">
            <b>{html.escape(t('home_cta_title'))}</b><br>
            <span style="font-size:12.5px; color:#7A7768;">{html.escape(t('home_cta_subtitle'))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/7_تسجيل_أسرة.py", label=t("home_cta_button"), icon=":material/storefront:")
