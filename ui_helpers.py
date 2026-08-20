"""
ui_helpers.py
--------------
تنسيقات ولغة مشتركة تُستخدم بكل صفحة.

get_lang() / t(): نظام الترجمة — يقرأ اللغة الحالية من session_state ويرجع
النص المناسب من translations.py.

render_language_switcher(): عنصر تبديل اللغة، يظهر بالقائمة الجانبية بكل
صفحة (تستدعيه كل صفحة بنفسها، زي apply_rtl()).

apply_rtl(): تحط اتجاه الصفحة حسب اللغة الحالية — RTL للعربي، LTR للإنجليزي.
Streamlit ما فيها إعداد جاهز لهذا بملف config.toml، فنستخدم CSS بسيط عبر
st.markdown.
"""

import html
import streamlit as st
from translations import TRANSLATIONS

# نظام الألوان الموحّد — نفس القيم بالضبط من موك-أبات المستخدمة (الرئيسية +
# الطلبات + لوحة الأسرة)، بدل ما يكون كل قسم بالتطبيق بلونه الخاص. نخزنها
# هنا مرة وحدة ونستخدمها بكل مكان (CSS وبايثون) عشان لو غيّرنا لون نغيّره
# بمكان وحيد.
PALETTE = {
    "green_900": "#2E4B12",
    "green_700": "#5A8F2A",
    "green_500": "#7CB342",
    "green_300": "#A9D477",
    "green_100": "#EAF3DE",
    "cream": "#FBF8F1",
    "card": "#FFFFFF",
    "ink": "#4E4B3B",
    "muted": "#7A7768",
    "line": "#E8E2D2",
    "honey": "#D9942F",
    "honey_light": "#FBEBD2",
    "red_light": "#FBE4DE",
    "red": "#C05A3E",
}

# عناوين الصفحات كلها بنفس اللون الأخضر الغامق (green-900) بغض النظر عن
# الدور — توحيد التصميم بدل ما يكون لكل دور لون عنوان مختلف (أخضر/برتقالي/
# أزرق زي قبل)؛ تمييز الدور الحين يصير عبر شارات الحالة والألوان السياقية
# بدل لون العنوان نفسه
ROLE_TITLE_COLORS = {
    "seller": PALETTE["green_900"],
    "courier": PALETTE["green_900"],
    "customer": PALETTE["green_900"],
}

# ملاحظة مهمة: جربنا أكثر من مرة عرض أيقونات Material Symbols كنص Unicode
# خام (codepoint) بمحتوى HTML مخصص (خارج معامل icon= الرسمي لعناصر
# st.button/page_link/popover/pills) — بعناوين الصفحات، وبعدها بصفحة
# الهبوط وشريط التنقل السفلي — وكل مرة طلعت النتيجة غير موثوقة (مربعات
# فاضية ☐ بدل الرمز). القاعدة صارت: أيقونات Material فقط عبر icon=
# بالعناصر الرسمية، ولأي عنصر HTML مخصص نستخدم إيموجي عادية بدلها.

# تصنيفات نوع المنتجات — قائمة ثابتة (رموز إنجليزية) نخزنها بعمود
# sellers.product_type بدل ما نخلي الأسرة تكتب نص حر عند التسجيل. الرمز
# نفسه ثابت بكل اللغات (عشان الفرز بالصفحة الرئيسية يشتغل صح حتى لو بدّلت
# المستخدمة اللغة)، والترجمة للعرض بس عبر category_label() تحت.
PRODUCT_CATEGORIES = ["sweets", "baked", "savory", "beverages", "main_dishes", "other"]


def category_label(product_type: str) -> str:
    """
    ترجع اسم التصنيف المترجم لو كان من PRODUCT_CATEGORIES الثابتة، ولو كان
    نص حر قديم (أسر سجّلت قبل ما نضيف هذي التصنيفات) ترجعه زي ما هو —
    عشان ما نكسر عرض بيانات أسر مسجلة من قبل.
    """
    key = f"category_{product_type}"
    label = t(key)
    return label if label != key else product_type


# اسم كل لغة بلغتها الأصلية (يظهر بمبدّل اللغة)
LANGUAGE_NAMES = {
    "ar": "العربية",
    "en": "English",
    "ur": "اردو",
    "fil": "Filipino",
    "hi": "हिन्दी",
}

# اللغات اللي تُكتب من اليمين لليسار
RTL_LANGUAGES = {"ar", "ur"}

# رمز العملة (الريال السعودي) — ثابت بكل اللغات، لأن العملة الفعلية
# ما تتغير حسب لغة الواجهة اللي يختارها المستخدم
CURRENCY_SYMBOL = "﷼"


def format_price(amount) -> str:
    return f"{float(amount):.2f} {CURRENCY_SYMBOL}"


def get_lang() -> str:
    return st.session_state.get("lang", "ar")


def t(key: str) -> str:
    """ترجع النص المناسب للغة الحالية. لو المفتاح ناقص، ترجع المفتاح نفسه
    (يسهّل اكتشاف أي نص نسينا نترجمه بدل ما يطلع خطأ)."""
    return TRANSLATIONS.get(get_lang(), TRANSLATIONS["ar"]).get(key, key)


def render_language_switcher(location: str = "sidebar"):
    """
    عنصر تبديل اللغة. ما نربطه مباشرة بـ session_state["lang"] عبر key=
    لأن صفحة app.py (اللي تبني قائمة التنقل بالقائمة الجانبية) تقرأ اللغة
    قبل ما هذا العنصر نفسه يترسم — لو اعتمدنا بس على الربط التلقائي، عناوين
    القائمة الجانبية تضل متأخرة "دورة واحدة" عن اللغة المختارة فعلياً.
    فبدالها: نقارن يدوياً، ولو تغيرت، نحفظ ونعمل st.rerun() فوري عشان كل
    شي (بما فيه القائمة الجانبية) يتحدث بنفس اللحظة.

    location: "sidebar" (افتراضي، لكل الصفحات) أو "inline" — للزبون، اللي
    ما عنده قائمة جانبية أصلاً (مخفية بـ app.py)، فنعرضه بالمتن العادي
    بصفحة "الملف الشخصي" بدل السايدبار.
    """
    codes = list(LANGUAGE_NAMES.keys())
    current = get_lang()
    target = st.sidebar if location == "sidebar" else st

    selected = target.selectbox(
        t("lang_switcher_label"),
        codes,
        index=codes.index(current),
        format_func=lambda code: LANGUAGE_NAMES[code],
        key=f"lang_switcher_{location}",
    )

    if selected != current:
        st.session_state["lang"] = selected
        st.rerun()


def render_page_title(icon_name: str, text: str, role=None):
    """
    عنوان صفحة (h1) ملوّن حسب الدور — بدون أيقونة عمداً. جربنا أكثر من
    طريقة لعرض أيقونة Material جوا العنوان (اختصار Markdown، ثم Unicode
    مباشر بالـ codepoint الصحيح المستخرج من ملف الخط نفسه)، وكلها طلعت
    نتائج غير موثوقة (نص حرفي أو مربع فارغ). بما إن الأيقونة هنا زخرفية
    بحتة (العنوان مفهوم بدونها)، قررنا نشيلها كلياً بدل ما نستمر نلاحق
    علة عرض مو مضمونة الحل — الاسم icon_name يضل موجود بالتوقيع لأنه
    غير مستخدم حالياً بس نتركه للمستقبل لو انحلت المشكلة بنسخة أحدث.
    """
    color = ROLE_TITLE_COLORS.get(role, "#3E4F3B")
    st.markdown(
        f"""
        <h1 style="color:{color}; font-weight:900; margin:0 0 4px 0;">
            {html.escape(text)}
        </h1>
        """,
        unsafe_allow_html=True,
    )


# شريط تنقّل سفلي بأيقونات (زي تطبيقات الجوال) بدل القائمة الجانبية
# الافتراضية — يُستخدم لصفحات الزبون الأربعة بس (الرئيسية/الطلبات/السلة/
# الملف الشخصي). كل عنصر: (مفتاح نشط، مسار الصفحة، مفتاح ترجمة التسمية،
# اسم أيقونة Material). العنصر النشط نعرضه كنص ملوّن ثابت (مو رابط) عشان
# نضمن لون تمييز واضح بدون الاعتماد على تلوين Streamlit الداخلي للصفحة
# الحالية (خافت وغير مضمون الشكل).
CUSTOMER_BOTTOM_NAV_ITEMS = [
    ("home", "pages/0_الرئيسية.py", "nav_home", "home"),
    ("orders", "pages/9_طلبات_الزبون.py", "nav_my_orders", "receipt_long"),
    ("cart", "pages/11_السلة.py", "nav_cart", "shopping_cart"),
    ("profile", "pages/13_الملف_الشخصي.py", "nav_profile", "account_circle"),
]

# العنصر النشط نعرضه كنص/HTML خام (مو st.page_link) عشان نلوّنه بلون واضح
# ثابت — بس رمز Material Symbols كـ Unicode codepoint بمحتوى HTML خام غير
# موثوق العرض (نفس العلة اللي واجهناها بعناوين الصفحات، تطلع مربعات فاضية)،
# فنستخدم إيموجي بسيطة بدلها هنا بس (العناصر غير النشطة تستمر تستخدم
# icon= الرسمية بـ st.page_link اللي مضمونة الشغل)
_BOTTOM_NAV_ACTIVE_EMOJI = {
    "home": "🏠",
    "receipt_long": "🧾",
    "shopping_cart": "🛒",
    "account_circle": "👤",
}


def render_customer_bottom_nav(active: str):
    st.markdown(
        f"""
        <style>
        .st-key-customer_bottom_nav {{
            position: fixed; left: 0; right: 0; bottom: 0; z-index: 999;
            background: {PALETTE["card"]}; border-top: 1px solid {PALETTE["line"]};
            padding: 6px 6px calc(6px + env(safe-area-inset-bottom));
            box-shadow: 0 -2px 10px rgba(0,0,0,0.06);
        }}
        .st-key-customer_bottom_nav [data-testid="stPageLink-NavLink"] {{
            display: flex; flex-direction: column; align-items: center; gap: 2px;
            padding: 4px 0; border-radius: 10px; width: 100%; background: transparent;
        }}
        .st-key-customer_bottom_nav [data-testid="stPageLink-NavLink"] p {{
            margin: 0; font-size: 11px; color: {PALETTE["muted"]};
        }}
        .st-key-customer_bottom_nav [data-testid="stIconMaterial"] {{
            color: {PALETTE["muted"]} !important;
        }}
        .qarrib-bottom-nav-active {{
            display: flex; flex-direction: column; align-items: center; gap: 2px;
            padding: 4px 0; color: {PALETTE["green_700"]};
        }}
        .qarrib-bottom-nav-active .qarrib-bn-icon {{
            font-size: 20px; line-height: 1;
        }}
        .qarrib-bottom-nav-active .qarrib-bn-label {{
            font-size: 11px; font-weight: 700;
        }}
        div[data-testid="stAppViewContainer"] .block-container {{
            padding-bottom: 76px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="customer_bottom_nav"):
        cols = st.columns(4)
        for col, (key, path, label_key, icon_name) in zip(cols, CUSTOMER_BOTTOM_NAV_ITEMS):
            with col:
                if key == active:
                    emoji = _BOTTOM_NAV_ACTIVE_EMOJI[icon_name]
                    st.markdown(
                        f'<div class="qarrib-bottom-nav-active">'
                        f'<span class="qarrib-bn-icon">{emoji}</span>'
                        f'<span class="qarrib-bn-label">{html.escape(t(label_key))}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.page_link(path, label=t(label_key), icon=f":material/{icon_name}:")


def apply_rtl():
    is_rtl = get_lang() in RTL_LANGUAGES
    direction = "rtl" if is_rtl else "ltr"
    align = "right" if is_rtl else "left"

    st.markdown(
        f"""
        <style>
        /* Tajawal لنص الجسم، Cairo للعناوين والأزرار — بالضبط زي موك-أبات
           المستخدمة (body: Tajawal / h1,h2,h3,.brand,.btn,.chip: Cairo) */
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&family=Tajawal:wght@400;500;700;900&display=swap');

        /* :not([data-testid="stIconMaterial"]) ضروري هنا — أيقونات
           Material Icons عنصرها الأساسي span، ولو دخلت بقائمة العناصر
           اللي نفرض عليها خط معيّن !important بيكسر خط الأيقونة (ligature
           font) ويطلع اسمها كنص حرفي بدل الرمز. استبعادها هنا يخلّي خط
           Streamlit الداخلي الخاص بالأيقونات يشتغل عادي. */
        .stApp,
        .stApp p:not([data-testid="stIconMaterial"]),
        .stApp div:not([data-testid="stIconMaterial"]),
        .stApp span:not([data-testid="stIconMaterial"]),
        .stApp label, .stApp input, .stApp textarea,
        .stApp li, .stApp a {{
            font-family: 'Tajawal', sans-serif !important;
        }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
        .stApp button {{
            font-family: 'Cairo', sans-serif !important;
        }}

        /* متغيرات الألوان الموحّدة — نفس أسماء وقيم متغيرات CSS بموك-أبات
           المستخدمة بالضبط، متاحة بكل صفحة (apply_rtl تتنفذ بكل صفحة) */
        :root {{
            --green-900: {PALETTE["green_900"]};
            --green-700: {PALETTE["green_700"]};
            --green-500: {PALETTE["green_500"]};
            --green-300: {PALETTE["green_300"]};
            --green-100: {PALETTE["green_100"]};
            --cream: {PALETTE["cream"]};
            --card: {PALETTE["card"]};
            --ink: {PALETTE["ink"]};
            --muted: {PALETTE["muted"]};
            --line: {PALETTE["line"]};
            --honey: {PALETTE["honey"]};
            --honey-light: {PALETTE["honey_light"]};
            --red-light: {PALETTE["red_light"]};
            --red: {PALETTE["red"]};
            --shadow: 0 10px 30px -12px rgba(46, 75, 18, 0.18);
        }}

        .stApp {{
            direction: {direction};
        }}
        [data-testid="stSidebar"] {{
            direction: {direction};
            text-align: {align};
        }}
        .stApp [data-testid="stMarkdownContainer"],
        .stApp label,
        .stApp p {{
            text-align: {align};
        }}
        /* أزرار Streamlit (أيقونة + نص) مبنية افتراضياً بترتيب LTR داخلي.
           فرض RTL على الصفحة كلها كان يكسر ترتيبها الداخلي (الأيقونة تطلع
           فوق النص بدل جنبه). الحل: نستثني الأزرار نفسها من انعكاس الاتجاه
           — نص الزر العربي يضل يقرأ صح حتى جوا حاوية LTR (خاصية يونيكود
           تلقائية)، بس ترتيب الأيقونة والنص جنب بعض يرجع طبيعي.
        */
        .stApp button {{
            direction: ltr !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_home_theme():
    """
    تنسيقات إضافية خاصة بالصفحة الرئيسية بس (البانر الترحيبي، بطاقات الأسر
    بشكل شبكة، صندوق دعوة التسجيل) — بألوان مستوحاة من تصميم موك-أب قدّمته
    المستخدمة (درجات أخضر عشبي دافئة فوق خلفية "ورقية" فاتحة)، بنفس روح
    الألوان المستخدمة أصلاً بـ .streamlit/config.toml.
    """
    st.markdown(
        """
        <style>
        .qarrib-banner {
            background: linear-gradient(135deg, #7CB342, #2E4B12);
            border-radius: 20px;
            padding: 26px 26px;
            color: #FBF8F1;
            margin-bottom: 22px;
            box-shadow: 0 10px 24px rgba(46, 75, 18, 0.25);
        }
        .qarrib-banner h3 { margin: 0 0 6px 0; font-size: 20px; font-weight: 900; }
        .qarrib-banner p { margin: 0; font-size: 13.5px; opacity: 0.95; }

        .qarrib-stat {
            display: flex; align-items: center; gap: 10px;
            background: #EAF3DE;
            border: 1px solid #E8E2D2;
            border-radius: 14px;
            padding: 10px 14px;
            margin-bottom: 18px;
        }
        .qarrib-stat .qarrib-stat-num { font-size: 18px; font-weight: 900; color: #5A8F2A; }
        .qarrib-stat .qarrib-stat-label { font-size: 11.5px; color: #7A7768; font-weight: 700; }

        .qarrib-section-head {
            display: flex; align-items: center; gap: 8px;
            margin: 6px 0 14px 0;
        }
        .qarrib-section-head .qarrib-dot {
            width: 8px; height: 8px; border-radius: 50%; background: #7CB342;
        }
        .qarrib-section-head span {
            font-size: 16px; font-weight: 900; color: #4E4B3B;
        }

        div[data-testid="stHorizontalBlock"] { gap: 14px; }

        .qarrib-seller-card {
            background: #FFFFFF;
            border: 1px solid #E8E2D2;
            border-radius: 16px;
            padding: 18px 12px;
            text-align: center;
            margin-bottom: 14px;
            box-shadow: 0 10px 30px -12px rgba(46, 75, 18, 0.18);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .qarrib-seller-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 22px rgba(46, 75, 18, 0.22);
        }
        .qarrib-seller-thumb {
            width: 46px; height: 46px; border-radius: 13px;
            background: linear-gradient(155deg, #7CB342, #4E7A20);
            color: #FFFFFF;
            display: flex; align-items: center; justify-content: center;
            font-weight: 900; font-size: 18px;
            margin: 0 auto 10px;
            box-shadow: 0 4px 10px rgba(46, 75, 18, 0.3);
        }
        .qarrib-seller-card h4 { font-size: 13.5px; font-weight: 700; margin: 0 0 3px 0; color: #4E4B3B; }
        .qarrib-seller-card p { font-size: 11.5px; margin: 0 0 10px 0; color: #7A7768; }
        .qarrib-seller-badge {
            display: inline-block; font-size: 10.5px; font-weight: 700;
            color: #5A8F2A; background: #EAF3DE; padding: 3px 12px; border-radius: 100px;
        }
        .qarrib-cta {
            border: 1.5px dashed #A9D477; border-radius: 16px;
            background: #EAF3DE;
            padding: 18px; text-align: center;
            margin-top: 6px;
        }

        /* صفحة الهبوط (للزوار غير المسجلين بس) — مبنية على موك-أب مفصّل
           بعثته المستخدمة (هيرو + بطاقة "رحلة الطلب" المتحركة + خطوات +
           بطاقات أدوار + عرض الأسر المسجلة + دعوة تسجيل). الألوان معاد
           ربطها بمتغيرات PALETTE الموحّدة بدل قيم الموك-أب الخام، عشان
           تبقى موحّدة مع باقي التطبيق */
        .qarrib-eyebrow {
            display: inline-flex; align-items: center; gap: 7px;
            background: #FBEBD2; color: #8A5A16;
            padding: 6px 15px; border-radius: 100px; font-size: 12.5px; font-weight: 800;
            margin-bottom: 16px;
        }
        .qarrib-hero {
            padding: 8px 0 20px 0;
        }
        .qarrib-hero h1 {
            font-size: 27px; font-weight: 900; line-height: 1.4; color: #2E4B12 !important;
            margin: 0 0 14px 0;
        }
        .qarrib-hero h1 .hl { color: #D9942F; }
        .qarrib-hero .lead {
            font-size: 14px; color: #7A7768; line-height: 1.75; margin-bottom: 6px; max-width: 440px;
        }
        .qarrib-hero-btn {
            display: inline-block; background: #7CB342; color: #FFFFFF !important;
            padding: 11px 26px; border-radius: 100px; font-weight: 800; font-size: 13.5px;
            margin-top: 16px; text-decoration: none !important;
            box-shadow: 0 5px 0 #2E4B12;
        }
        .qarrib-hero-btn:hover { transform: translateY(-2px); }

        .qarrib-route-card {
            background: #FFFFFF; border: 1px solid #E8E2D2; border-radius: 22px;
            padding: 22px 20px; box-shadow: 0 16px 36px -16px rgba(46, 75, 18, 0.3);
            overflow: hidden;
        }
        .qarrib-route-card .title {
            font-family: 'Cairo', sans-serif; font-weight: 800; color: #2E4B12; font-size: 14.5px;
            margin-bottom: 14px; display: block;
        }
        /* عرض/ارتفاع ثابتين (300×210) بالضبط نفس viewBox حق السي‌في‌جي —
           لازم يتطابقوا تمامًا، لأن إحداثيات offset-path حقت النقطة
           المتحركة تحت (M 270 30 C...) مكتوبة كأرقام بكسل ثابتة، مو نسبية
           لعرض العنصر. لو الحاوية أعرض من 300px (زي أعمدة Streamlit
           بالشاشات الكبيرة)، السي‌في‌جي كان يتمدد ليملى العرض بس النقطة
           تضل تتحرك بنفس الإحداثيات الأصغر — فتطلع النقطة خارج المسار
           المرسوم بصريًا. تثبيت العرض هنا يخلي الاثنين يتطابقوا دايمًا */
        .qarrib-route-path { position: relative; width: 300px; height: 210px; margin: 0 auto; max-width: 100%; overflow: hidden; }
        .qarrib-route-svg { position: absolute; inset: 0; }
        .qarrib-route-dot {
            position: absolute; width: 13px; height: 13px; border-radius: 50%;
            background: #D9942F; box-shadow: 0 0 0 5px #FBEBD2;
            offset-path: path('M 270 30 C 160 30, 110 175, 30 175');
            animation: qarrib-travel 3.2s linear infinite;
        }
        @keyframes qarrib-travel {
            0% { offset-distance: 0%; opacity: 0; }
            8% { opacity: 1; }
            92% { opacity: 1; }
            100% { offset-distance: 100%; opacity: 0; }
        }
        @media (prefers-reduced-motion: reduce) {
            .qarrib-route-dot { animation: none; offset-distance: 50%; }
        }
        .qarrib-route-card .qarrib-route-node {
            position: absolute; width: 56px; height: 56px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-family: 'Material Symbols Rounded' !important; font-size: 24px; color: #2E4B12;
        }
        .qarrib-route-node.kitchen { top: 0; right: 0; background: #EAF3DE; }
        .qarrib-route-node.home { bottom: 0; left: 0; background: #FBEBD2; }
        .qarrib-route-caption {
            position: absolute; font-size: 11px; font-weight: 700; color: #7A7768; white-space: nowrap;
        }
        .qarrib-route-caption.kitchen { top: 62px; right: 0; }
        .qarrib-route-caption.home { bottom: 62px; left: 0; }
        .qarrib-route-label {
            position: absolute; top: 42%; left: 50%; transform: translate(-50%, -50%);
            background: #FBF8F1; border: 1px solid #E8E2D2; border-radius: 100px;
            padding: 5px 14px; font-size: 11px; font-weight: 800; color: #2E4B12; white-space: nowrap;
        }

        .qarrib-how-title { text-align: center; font-size: 21px; font-weight: 900; color: #2E4B12; margin: 8px 0 6px 0; }
        .qarrib-how-subtitle { text-align: center; font-size: 13px; color: #7A7768; max-width: 480px; margin: 0 auto 26px auto; line-height: 1.7; }

        /* تساوي ارتفاع بطاقات الخطوات الثلاث — height:100% على .qarrib-step
           لحاله ما يكفي، لازم كل حاوية Streamlit وسيطة (العمود، ثم
           stVerticalBlock، ثم stElementContainer/stMarkdown) تكون display:flex
           بالطول عشان النسبة 100% تنتقل لحد آخر عنصر، وإلا كل بطاقة تاخذ
           طول محتواها بس (نص أطول = بطاقة أطول) */
        .st-key-landing_steps_row [data-testid="stColumn"] {
            display: flex;
        }
        .st-key-landing_steps_row [data-testid="stColumn"] > div,
        .st-key-landing_steps_row [data-testid="stVerticalBlock"],
        .st-key-landing_steps_row [data-testid="stElementContainer"],
        .st-key-landing_steps_row [data-testid="stMarkdown"],
        .st-key-landing_steps_row [data-testid="stMarkdownContainer"] {
            display: flex; flex-direction: column; flex: 1; width: 100%;
        }
        .qarrib-step {
            background: #FFFFFF; border: 1px solid #E8E2D2; border-radius: 18px;
            padding: 22px 18px; height: 100%; flex: 1;
        }
        .qarrib-step .num {
            font-family: 'Cairo', sans-serif; font-weight: 900; font-size: 30px;
            color: #EAF3DE; -webkit-text-stroke: 1.3px #7CB342; display: block; margin-bottom: 10px;
        }
        .qarrib-step h4 { font-size: 14.5px; font-weight: 800; margin: 0 0 6px 0; color: #2E4B12; }
        .qarrib-step p { font-size: 12px; color: #7A7768; margin: 0; line-height: 1.65; }

        /* تساوي ارتفاع بطاقات الأدوار الثلاث — شبيه بأسلوب بطاقات الخطوات،
           بس هنا كل عمود فيه عنصرين (البطاقة + زر التسجيل تحتها)، فنمدد
           العنصر الأول بس (:first-child، البطاقة) ونخلي الزر بحجمه
           الطبيعي تحتها بدل ما يتمدد هو الثاني */
        .st-key-landing_audience_row [data-testid="stColumn"] {
            display: flex;
        }
        .st-key-landing_audience_row [data-testid="stColumn"] > div {
            display: flex; flex-direction: column; width: 100%;
        }
        .st-key-landing_audience_row [data-testid="stVerticalBlock"] {
            display: flex; flex-direction: column; height: 100%; width: 100%;
        }
        .st-key-landing_audience_row [data-testid="stElementContainer"]:first-child {
            display: flex; flex-direction: column; flex: 1;
        }
        .st-key-landing_audience_row [data-testid="stElementContainer"]:first-child [data-testid="stMarkdown"],
        .st-key-landing_audience_row [data-testid="stElementContainer"]:first-child [data-testid="stMarkdownContainer"] {
            display: flex; flex-direction: column; flex: 1;
        }
        .qarrib-audience-card {
            border-radius: 20px; padding: 26px 22px; height: 100%; flex: 1;
        }
        /* بطاقة الأسرة كانت أخضر غامق صلب — خففناها وأدخلنا البرتقالي
           (الهوني) بتدرّج دافئ يمزج مع الأخضر والبيج الموجودين أصلاً
           بباقي التصميم، بدل كتلة خضراء وحيدة غامقة */
        .qarrib-audience-card.dark {
            background: linear-gradient(135deg, #EAF3DE, #FBEBD2);
            border: 1px solid #E8E2D2;
            color: #2E4B12;
        }
        .qarrib-audience-card.light { background: #FFFFFF; border: 1px solid #E8E2D2; }
        .qarrib-audience-card h3 { font-size: 17px; font-weight: 800; margin: 0 0 10px 0; }
        .qarrib-audience-card.dark h3 { color: #2E4B12 !important; }
        .qarrib-audience-card.light h3 { color: #2E4B12 !important; }
        .qarrib-audience-card .desc { font-size: 12.5px; margin-bottom: 16px; line-height: 1.7; }
        .qarrib-audience-card.dark .desc { color: #5A5644; }
        .qarrib-audience-card.light .desc { color: #7A7768; }
        .qarrib-audience-list { list-style: none; margin: 0 0 18px 0; padding: 0; }
        .qarrib-audience-list li { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 9px; font-size: 12px; line-height: 1.6; }
        .qarrib-audience-list li::before { content: "✓"; font-weight: 800; flex-shrink: 0; }
        .qarrib-audience-card.dark .qarrib-audience-list li::before { color: #D9942F; }
        .qarrib-audience-card.light .qarrib-audience-list li::before { color: #D9942F; }

        .qarrib-fam-scroll {
            display: flex; gap: 14px; overflow-x: auto; padding: 4px 2px 12px 2px;
        }
        .qarrib-fam-card {
            min-width: 190px; background: #FFFFFF; border: 1px solid #E8E2D2; border-radius: 16px;
            padding: 18px; flex-shrink: 0;
        }
        .qarrib-fam-card .thumb {
            width: 42px; height: 42px; border-radius: 12px;
            background: linear-gradient(155deg, #7CB342, #4E7A20); color: #FFFFFF;
            display: flex; align-items: center; justify-content: center;
            font-weight: 900; font-size: 16px; margin-bottom: 12px; object-fit: cover;
        }
        .qarrib-fam-card h5 { font-family: 'Cairo', sans-serif; font-weight: 700; font-size: 13.5px; margin: 0 0 4px 0; color: #2E4B12; }
        .qarrib-fam-card p { font-size: 11.5px; color: #7A7768; margin: 0; }
        .qarrib-fam-badge {
            display: inline-block; margin-top: 12px; background: #EAF3DE; color: #2E4B12;
            font-size: 10.5px; font-weight: 700; padding: 3px 11px; border-radius: 100px;
        }
        .qarrib-fam-card.more {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            text-align: center; background: #FBF8F1; border-style: dashed;
        }

        .qarrib-signup-panel {
            background: #2E4B12; border-radius: 24px; padding: 30px 24px; color: #FBF8F1;
            text-align: center; margin: 10px 0 6px 0;
        }
        .qarrib-signup-panel h2 { color: #FBF8F1 !important; font-size: 19px; font-weight: 900; margin: 0 0 8px 0; }
        .qarrib-signup-panel p { font-size: 12.5px; opacity: 0.88; margin: 0 auto; max-width: 400px; }
        .st-key-landing_signup_btns button {
            border-radius: 100px !important; font-weight: 800 !important;
        }

        .qarrib-footer-tagline {
            text-align: center; font-size: 11.5px; color: #7A7768; margin: 22px auto 4px auto; max-width: 420px; line-height: 1.7;
        }

        /* شكل رقاقات الفرز (تصنيف المنتج + الترتيب) — نستهدفها فقط عبر
           كلاس "st-key-..." اللي يضيفه Streamlit تلقائياً لأي
           st.container(key=...) (ميزة رسمية موثقة)، بدل استهداف كل زر
           بالتطبيق (.stApp button) — عشان ما نأثر على أزرار ثانية
           (تسجيل، إضافة للسلة، تسجيل خروج...) بالغلط */
        .st-key-home_category_chips button,
        .st-key-home_sort_chips button {
            border-radius: 999px !important;
            font-weight: 700 !important;
            padding: 7px 20px !important;
            background: #EAF3DE !important;
            border: 1.5px solid #E8E2D2 !important;
            color: #5A8F2A !important;
            box-shadow: none !important;
            transition: transform 0.12s ease, box-shadow 0.12s ease !important;
        }
        .st-key-home_category_chips button:hover,
        .st-key-home_sort_chips button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(124, 179, 66, 0.25) !important;
        }
        /* الرقاقة المختارة — Streamlit يعلّمها بـ aria-selected. لو الخاصية
           هذي مو مستخدمة فعلياً بمكوّن pills، هذي القاعدة ببساطة ما تنطبق
           على أي عنصر (بدون أي ضرر) */
        .st-key-home_category_chips button[aria-selected="true"],
        .st-key-home_sort_chips button[aria-selected="true"] {
            background: #7CB342 !important;
            border-color: #7CB342 !important;
            color: #FBF8F1 !important;
            animation: qarrib-chip-pulse 2.2s ease-in-out infinite !important;
        }
        /* نبضة خفيفة مستمرة حوالين الرقاقة المختارة — حركة بسيطة لطيفة
           تعطي إحساس "حيوية" للواجهة بدل ما تكون ساكنة تماماً */
        @keyframes qarrib-chip-pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(124, 179, 66, 0.45); }
            50% { box-shadow: 0 0 0 7px rgba(124, 179, 66, 0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_orders_theme():
    """
    تنسيقات مشتركة لصفحات الطلبات (طلبات الأسرة + طلبات الزبون) — بطاقات
    الطلب، شارات الحالة، متتبع الخطوات، صندوق المندوب، حالة "فاضي"،
    وتنسيق تبويبات st.tabs — كلها بنفس ألوان موك-أبات المستخدمة (قرّب —
    طلباتي / قرّب — لوحة الأسرة).
    """
    st.markdown(
        """
        <style>
        /* بطاقة الطلب الحالي (تُستخدم بصفحة الزبون للطلب النشط، وبصفحة
           الأسرة لكل طلب بقائمة الطلبات الحالية) */
        .qarrib-order-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-bottom: 16px;
        }
        .qarrib-order-card.new { border-color: var(--honey); }

        .qarrib-oc-head {
            padding: 16px 20px;
            display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
            border-bottom: 1px dashed var(--line);
        }
        .qarrib-oc-stage {
            font-size: 11.5px; font-weight: 700; padding: 5px 12px; border-radius: 999px;
        }
        .qarrib-oc-stage.pending { background: var(--honey-light); color: #9A5F14; }
        .qarrib-oc-stage.ready { background: var(--green-100); color: var(--green-700); }
        .qarrib-oc-stage.delivered { background: #DCEBEF; color: #2E6B7A; }
        .qarrib-oc-id {
            margin-inline-start: auto; font-size: 12px; color: var(--muted);
            font-family: 'Cairo', sans-serif;
        }

        .qarrib-oc-body { padding: 14px 20px; }
        .qarrib-oc-customer .name { font-weight: 700; font-size: 15px; color: var(--ink); }
        .qarrib-oc-customer .sub { font-size: 12.5px; color: var(--muted); margin-top: 2px; }

        .qarrib-oi-row {
            display: flex; justify-content: space-between;
            padding: 7px 0; font-size: 14px; border-bottom: 1px solid var(--line);
        }
        .qarrib-oi-row:last-child { border-bottom: none; }
        .qarrib-oi-row .price { color: var(--muted); font-size: 13px; }
        .qarrib-oi-total { font-weight: 800; color: var(--green-900); }

        .qarrib-oc-note {
            background: var(--green-100); color: var(--green-900);
            font-size: 12.5px; padding: 9px 12px; border-radius: 10px; margin-top: 10px;
        }

        /* متتبع خطوات الطلب (لصفحة الزبون بس) */
        .qarrib-tracker { padding: 22px 10px 4px; }
        .qarrib-steps { display: flex; align-items: flex-start; position: relative; }
        .qarrib-step { flex: 1; text-align: center; position: relative; z-index: 1; }
        .qarrib-step .circle {
            width: 32px; height: 32px; border-radius: 50%; margin: 0 auto 8px;
            display: flex; align-items: center; justify-content: center;
            background: var(--cream); border: 2px solid var(--line); font-size: 14px; color: var(--muted);
        }
        .qarrib-step.done .circle { background: var(--green-500); border-color: var(--green-500); color: #fff; }
        .qarrib-step.current .circle {
            background: #fff; border-color: var(--green-500); color: var(--green-700);
            box-shadow: 0 0 0 5px var(--green-100);
            animation: qarrib-step-pulse 1.8s ease-in-out infinite;
        }
        @keyframes qarrib-step-pulse {
            0%, 100% { box-shadow: 0 0 0 5px var(--green-100); }
            50% { box-shadow: 0 0 0 8px rgba(124, 179, 66, 0.18); }
        }
        .qarrib-step .lbl { font-size: 11.5px; font-weight: 700; color: var(--muted); }
        .qarrib-step.done .lbl, .qarrib-step.current .lbl { color: var(--green-900); }
        .qarrib-track-line {
            position: absolute; top: 16px; right: 0; left: 0; height: 2px; background: var(--line); z-index: 0;
        }
        .qarrib-track-fill {
            position: absolute; top: 16px; right: 0; height: 2px; background: var(--green-500); z-index: 0;
            transition: width 0.3s;
        }

        /* صندوق بيانات المندوب المسند للطلب */
        .qarrib-courier-box {
            display: flex; align-items: center; gap: 12px;
            background: var(--green-100); border-radius: 14px; padding: 12px 16px; margin-top: 14px;
        }
        .qarrib-courier-box .avatar {
            width: 38px; height: 38px; border-radius: 50%; background: var(--green-700); color: #fff;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-family: 'Cairo', sans-serif; flex-shrink: 0;
        }
        .qarrib-courier-box .info b { display: block; font-size: 13.5px; color: var(--green-900); }
        .qarrib-courier-box .info span { font-size: 12px; color: var(--muted); }

        /* مسار الاستلام/التسليم (صفحة المندوب) — نقطتين متصلتين بخط رأسي */
        .qarrib-route { padding: 18px 20px 4px; }
        .qarrib-route-point { display: flex; gap: 12px; position: relative; padding-bottom: 22px; }
        .qarrib-route-point:last-child { padding-bottom: 0; }
        .qarrib-route-point::before {
            content: ""; position: absolute; inset-inline-start: 15px; top: 32px; bottom: -2px;
            width: 2px; background: var(--line);
        }
        .qarrib-route-point:last-child::before { display: none; }
        .qarrib-route-marker {
            width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 13px; font-weight: 800; color: #fff; z-index: 1;
        }
        .qarrib-route-marker.pickup { background: var(--honey); }
        .qarrib-route-marker.dropoff { background: var(--green-500); }
        .qarrib-route-info { flex: 1; padding-top: 2px; }
        .qarrib-route-info .tag { font-size: 11px; color: var(--muted); font-weight: 700; margin-bottom: 2px; }
        .qarrib-route-info .name { font-weight: 700; font-size: 14.5px; color: var(--ink); }
        .qarrib-route-info .sub { font-size: 12.5px; color: var(--muted); margin-top: 2px; }

        .qarrib-stats-row.cols-2 { grid-template-columns: repeat(2, 1fr); }
        .qarrib-stats-row.cols-3 { grid-template-columns: repeat(3, 1fr); }

        /* شارة حالة صغيرة (تُستخدم بعناوين سجل الطلبات المطوي) */
        .qarrib-status-badge {
            font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 999px; white-space: nowrap;
        }
        .qarrib-status-badge.done { background: var(--green-100); color: var(--green-700); }
        .qarrib-status-badge.cancelled { background: var(--red-light); color: var(--red); }

        /* حالة "ما فيه طلبات" */
        .qarrib-empty-state {
            background: var(--card); border: 1px dashed var(--line); border-radius: 20px;
            padding: 44px 24px; text-align: center;
        }
        .qarrib-empty-state h3 { margin: 0 0 8px; color: var(--green-900); font-size: 16px; }
        .qarrib-empty-state p { margin: 0; color: var(--muted); font-size: 13.5px; }

        /* شريط إحصائيات صفحة الأسرة (4 بطاقات) */
        .qarrib-stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
        @media (max-width: 700px) { .qarrib-stats-row { grid-template-columns: 1fr 1fr; } }
        .qarrib-stat-card {
            background: var(--card); border: 1px solid var(--line); border-radius: 14px;
            padding: 14px 16px; box-shadow: var(--shadow);
        }
        .qarrib-stat-card .val { font-family: 'Cairo', sans-serif; font-weight: 800; font-size: 19px; color: var(--green-900); }
        .qarrib-stat-card .lbl { font-size: 11.5px; color: var(--muted); margin-top: 2px; }

        /* تحسين مظهر st.tabs الافتراضي (خط تحته لون) بدل استبداله كلياً —
           أخف خطورة من محاولة تحويله لتبويبات بيضاوية مقفولة عبر CSS مو
           مضمونة الاستهداف */
        [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 22px !important; }
        [data-testid="stTab"] p { font-weight: 700 !important; font-size: 14px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
