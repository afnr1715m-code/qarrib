"""
courier_assignment.py
----------------------
منطق اختيار "المندوب التالي" لما يوصل طلب جديد.

فيه أسلوبين حسب توفر بيانات الموقع:

1. حسب الموقع (لو مررنا seller_lat/seller_lon، وفيه مندوب متاح واحد على
   الأقل حدّد موقعه): نختار أقرب مندوب متاح فعلياً لموقع الأسرة (خط
   مستقيم تقريبي — Haversine، راجع location_helpers.py).

2. Round Robin (احتياطي، لما ما تتوفر بيانات موقع كافية):
   أ. نجيب كل المناديب اللي حالتهم "متاح" مرتبين بترتيب ثابت
   ب. نجيب آخر مندوب استلم طلب (محفوظ بجدول courier_rotation)
   ج. نختار "اللي بعده" بنفس القائمة — ولو ما لقيناه (مثلاً صار مشغول)
      نبدأ من أول القائمة من جديد
   د. نحدّث courier_rotation بمعرّف المندوب الجديد
"""

from supabase import Client

from location_helpers import haversine_km


def assign_next_courier(supabase: Client, seller_lat=None, seller_lon=None):
    """
    ترجع بيانات المندوب اللي حقه ياخذ الطلب الجاي، أو None لو ما فيه أي مندوب متاح.
    seller_lat/seller_lon اختياريين — لو موجودين ووفيه مندوب حدّد موقعه،
    نستخدم أقرب مندوب فعلياً بدل التناوب.
    """
    couriers_response = (
        supabase.table("couriers")
        .select("*")
        .eq("is_available", True)
        .order("created_at")
        .execute()
    )
    available_couriers = couriers_response.data

    if not available_couriers:
        return None

    if seller_lat is not None and seller_lon is not None:
        couriers_with_location = [
            c for c in available_couriers if c.get("latitude") is not None and c.get("longitude") is not None
        ]
        if couriers_with_location:
            return min(
                couriers_with_location,
                key=lambda c: haversine_km(seller_lat, seller_lon, c["latitude"], c["longitude"]),
            )
        # ما فيه ولا مندوب حدّد موقعه — نكمل بأسلوب التناوب تحت

    rotation_response = supabase.table("courier_rotation").select("*").eq("id", 1).execute()
    # لو الصف مفقود لأي سبب (مثلاً انحذف بالغلط)، نعتبره "ما فيه آخر مندوب"
    # بدل ما نكرش، ونعيد إنشاءه بالقيمة الافتراضية
    if rotation_response.data:
        last_courier_id = rotation_response.data[0]["last_courier_id"]
    else:
        supabase.table("courier_rotation").insert({"id": 1, "last_courier_id": None}).execute()
        last_courier_id = None

    # افتراضياً نبدأ من أول واحد بالقائمة
    next_index = 0

    # لو فيه "آخر مندوب" محفوظ، ندور مكانه بالقائمة ونختار اللي بعده
    if last_courier_id:
        for i, courier in enumerate(available_couriers):
            if courier["id"] == last_courier_id:
                next_index = (i + 1) % len(available_couriers)
                break

    next_courier = available_couriers[next_index]

    # نحدّث السجل عشان الطلب الجاي يعرف يبدأ من بعد هذا المندوب
    supabase.table("courier_rotation").update(
        {"last_courier_id": next_courier["id"]}
    ).eq("id", 1).execute()

    return next_courier
