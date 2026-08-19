"""
location_helpers.py
--------------------
مكوّن مشترك لاختيار موقع على خريطة تفاعلية (أسرة/زبونة/مندوب)، وحساب
المسافة التقريبية بين موقعين (لاختيار أقرب مندوب متاح).

نستخدم streamlit-folium (تغليف لـ Folium/Leaflet.js) لأن st.map() الأصلية
بـ Streamlit للعرض بس — ماله خاصية "اضغطي على الخريطة لتحديد موقعك".
streamlit-folium هي المكتبة القياسية والأشهر لهذا الغرض بالذات.

ملاحظة صدق مهمة (نفس روح باقي التطبيق — ما نتظاهر بدقة أكثر من الواقع):
- هذا "موقع محفوظ" تحدده الأسرة/المندوب/الزبونة يدوياً بالضغط على الخريطة
  (مرة وحدة، أو تعدّله من الإعدادات لاحقاً) — مو تتبّع GPS حي مستمر.
  Streamlit ما فيها آلية لتحديث الموقع تلقائياً بالخلفية.
- حساب المسافة بين نقطتين خط مستقيم تقريبي (صيغة Haversine)، مو مسافة
  قيادة فعلية عبر الشوارع (يحتاج خدمة خرائط مدفوعة زي Google Directions).
"""

import math

import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from ui_helpers import t

# مركز افتراضي للخريطة لو ما فيه موقع محفوظ بعد — الرياض
DEFAULT_CENTER = (24.7136, 46.6753)


def render_location_picker(lat=None, lon=None, key="location_picker", height=350):
    """
    تعرض زر "استخدام موقعي الحالي" (يطلب إذن الموقع من المتصفح — يشتغل
    محلياً على localhost وأي رابط https) + خريطة تفاعلية يقدر المستخدم
    يضغط عليها يدوياً لو ما بغى يعطي إذن GPS أو بغى يعدّل نقطة قريبة.

    ترجع (lat, lon)، أو None لو ما فيه ولا نقطة محفوظة ولا مختارة بعد.

    ملاحظة تصميم مهمة: أي نقطة تُختار (GPS أو ضغطة خريطة) تُحفظ فوراً
    بـ st.session_state (مفتاح خاص بـ key الممرّر). لولا هذا الحفظ، أول
    rerun يصير بعدها (حتى مجرد الضغط على زر "حفظ الموقع" بالصفحة اللي
    تستدعي هذا المكوّن) كان يفقد النقطة المختارة ويرجع لقيمة قاعدة
    البيانات القديمة (lat/lon الممرّرين للدالة) — بالضبط العلة اللي كانت
    تخلي الموقع "يتحدد وبعدين يُلغى" لما تضغطين حفظ.
    """
    value_key = f"{key}_value"
    if value_key in st.session_state:
        lat, lon = st.session_state[value_key]

    # طلب GPS من المتصفح غير متزامن (async) — المتصفح يسأل المستخدم إذن،
    # وردّه يوصل بعد rerun تلقائي منفصل عن ضغطة الزر نفسها. فنحفظ "طلبنا
    # GPS" بـ session_state (يضل قائم عبر إعادة التشغيل التلقائية، بخلاف
    # نتيجة st.button() اللي تصير False فوراً بأول rerun بعد الضغطة).
    requested_flag = f"{key}_gps_requested"
    if st.button(t("btn_use_my_location"), key=f"{key}_gps_btn"):
        st.session_state[requested_flag] = True

    if st.session_state.get(requested_flag):
        location = get_geolocation(component_key=f"{key}_gps")
        if location and "coords" in location:
            lat = location["coords"]["latitude"]
            lon = location["coords"]["longitude"]
            st.session_state[value_key] = (lat, lon)
            st.session_state[requested_flag] = False
        elif location and "error" in location:
            st.error(t("location_gps_error"))
            st.session_state[requested_flag] = False
        # location None يعني الطلب لسا معلّق بانتظار رد المتصفح — نضل
        # منتظرين (الكومبوننت نفسه بيعمل rerun تلقائي وقت يجاوب المتصفح)

    center = (lat, lon) if lat and lon else DEFAULT_CENTER
    m = folium.Map(location=center, zoom_start=14 if lat and lon else 6)

    if lat and lon:
        folium.Marker([lat, lon], icon=folium.Icon(color="green")).add_to(m)

    map_data = st_folium(m, height=height, use_container_width=True, key=key)

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state[value_key] = (lat, lon)
        return lat, lon

    if lat and lon:
        return lat, lon

    return None


def haversine_km(lat1, lon1, lat2, lon2):
    """المسافة التقريبية (كم) بين نقطتين على سطح الأرض — خط مستقيم، مو مسار قيادة فعلي."""
    earth_radius_km = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(a))
