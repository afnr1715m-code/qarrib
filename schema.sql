-- ============================================
-- سكيما قاعدة بيانات مشروع "قرّب"
-- نفّذ هذا الملف كامل داخل Supabase → SQL Editor → New query → Run
-- ============================================

-- جدول الأسر المنتجة
create table if not exists sellers (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,  -- ربط بحساب تسجيل الدخول
    name text not null,                    -- اسم الأسرة المنتجة
    product_type text not null,            -- نوع المنتجات (رمز ثابت من PRODUCT_CATEGORIES بـ ui_helpers.py)
    prep_time_minutes int not null,        -- وقت التجهيز المتوقع بالدقائق
    whatsapp_number text not null,         -- رقم واتساب الأسرة
    logo_url text,                         -- شعار الأسرة (Supabase Storage، bucket seller-logos)
    advance_days int not null default 0,   -- أيام تجهيز مسبق مطلوبة (0 = بدون)
    latitude double precision,             -- موقع الاستلام (تحدده الأسرة من خريطة)
    longitude double precision,
    created_at timestamptz not null default now()
);

-- جدول المناديب
create table if not exists couriers (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,  -- ربط بحساب تسجيل الدخول
    name text not null,
    whatsapp_number text not null,
    city text,                                      -- مدينة المندوب (اختياري)
    vehicle_type text,                              -- car / motorcycle / bicycle
    plate_number text,                              -- رقم لوحة المركبة (اختياري)
    is_active boolean not null default true,      -- عشان نقدر نوقف مندوب مؤقتاً بدون حذفه (يتحكم فيه الأدمن)
    is_available boolean not null default true,    -- هل المندوب متاح يستلم طلب الحين؟ (يتحكم فيه المندوب نفسه)
    latitude double precision,             -- آخر موقع حدّده المندوب يدوياً (مو تتبع GPS حي)
    longitude double precision,
    created_at timestamptz not null default now()
);

-- جدول الزباين
create table if not exists customers (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,  -- ربط بحساب تسجيل الدخول
    name text not null,
    whatsapp_number text not null,
    latitude double precision,             -- موقع التسليم (تحدده الزبونة من خريطة)
    longitude double precision,
    created_at timestamptz not null default now()
);

-- قائمة منتجات كل أسرة
create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    seller_id uuid not null references sellers(id) on delete cascade,
    name text not null,
    price numeric(10,2) not null,
    description text,
    image_url text,
    created_at timestamptz not null default now()
);
alter table products add column if not exists image_url text;

-- جدول الطلبات
create table if not exists orders (
    id uuid primary key default gen_random_uuid(),
    seller_id uuid not null references sellers(id),
    courier_id uuid references couriers(id),   -- يتحدد لاحقاً بعد التوزيع بالتناوب
    customer_id uuid not null references customers(id),
    customer_name text not null,       -- منسوخة من حساب الزبون وقت الطلب (تسهيل عرض بدون join)
    customer_whatsapp text not null,   -- نفس الشي
    order_details text,                -- ملاحظات إضافية اختيارية (تفاصيل الطلب نفسها بجدول order_items)
    total_price numeric(10,2) not null default 0,
    status text not null default 'pending',    -- pending / ready / delivered
    created_at timestamptz not null default now()
);

-- محتويات كل طلب (منتج + كمية + سعر وقت الطلب)
-- نخزن product_name و unit_price كـ "لقطة" وقت الطلب، عشان لو الأسرة غيّرت
-- اسم/سعر المنتج بعدين، أو حذفته، الطلبات القديمة تضل تعرض صح.
create table if not exists order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references orders(id) on delete cascade,
    product_id uuid references products(id) on delete set null,
    product_name text not null,
    quantity int not null check (quantity > 0),
    unit_price numeric(10,2) not null,
    created_at timestamptz not null default now()
);

-- جدول بسيط لتتبع آخر مندوب استلم طلب (لتطبيق Round Robin)
-- صف واحد بس، نحدّثه بكل مرة. نخزن id المندوب نفسه (مو رقم ترتيبه)
-- عشان يضل صحيح حتى لو تغيرت قائمة "المتاحين" بين طلب وطلب
create table if not exists courier_rotation (
    id int primary key default 1,
    last_courier_id uuid references couriers(id),
    constraint single_row check (id = 1)
);

insert into courier_rotation (id, last_courier_id)
values (1, null)
on conflict (id) do nothing;

-- ============================================
-- حماية البيانات (Row Level Security)
-- ============================================
-- sellers و couriers و customers و orders محمية بسياسات دقيقة مبنية على تسجيل الدخول:
-- أي شخص (حتى زائر مب مسجل) يقدر يشوف قائمة الأسر/المناديب (محتاجينها
-- بصفحة الطلب العامة)، بس صاحب الحساب نفسه يقدر يعدّل بياناته أو يشوف/يحدّث طلباته.
-- customers استثناء: ما فيها select عام، لأنه محد يحتاج يتصفح قائمة الزباين.
-- إرسال طلب جديد لازم تسجيل دخول كزبون (orders_insert_own).
-- courier_rotation يضل بدون حماية RLS: ما فيه بيانات حساسة، مجرد عداد داخلي
-- يحدّثه أي زبون مسجل دخول وقت إرسال طلب جديد.

alter table sellers enable row level security;
alter table couriers enable row level security;
alter table customers enable row level security;
alter table products enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;

create policy "sellers_select_public" on sellers
    for select to anon, authenticated using (true);

create policy "sellers_insert_own" on sellers
    for insert to authenticated with check ((select auth.uid()) = user_id);

create policy "sellers_update_own" on sellers
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

create policy "couriers_select_public" on couriers
    for select to anon, authenticated using (true);

create policy "couriers_insert_own" on couriers
    for insert to authenticated with check ((select auth.uid()) = user_id);

create policy "couriers_update_own" on couriers
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

-- customers: ما فيها select عام (بعكس sellers/couriers) — محد يحتاج يتصفح
-- قائمة الزباين إلا الزبون نفسه
create policy "customers_select_own" on customers
    for select to authenticated using ((select auth.uid()) = user_id);

create policy "customers_insert_own" on customers
    for insert to authenticated with check ((select auth.uid()) = user_id);

-- الزبون لازم يكون مسجل دخول عشان يرسل طلب، ويكون الطلب مرتبط بحسابه هو بس
create policy "orders_insert_own" on orders
    for insert to authenticated with check (
        customer_id in (select id from customers where user_id = (select auth.uid()))
    );

create policy "orders_select_owner" on orders
    for select to authenticated using (
        seller_id in (select id from sellers where user_id = (select auth.uid()))
        or courier_id in (select id from couriers where user_id = (select auth.uid()))
        or customer_id in (select id from customers where user_id = (select auth.uid()))
    );

create policy "orders_update_owner" on orders
    for update to authenticated using (
        seller_id in (select id from sellers where user_id = (select auth.uid()))
        or courier_id in (select id from couriers where user_id = (select auth.uid()))
        or customer_id in (select id from customers where user_id = (select auth.uid()))
    )
    with check (
        seller_id in (select id from sellers where user_id = (select auth.uid()))
        or courier_id in (select id from couriers where user_id = (select auth.uid()))
        or customer_id in (select id from customers where user_id = (select auth.uid()))
    );

-- منتجات: أي شخص يشوف قائمة منتجات أي أسرة (محتاجينها بصفحة الطلب العامة)،
-- بس صاحبة الأسرة تقدر تضيف/تعدّل/تحذف منتجاتها هي بس
create policy "products_select_public" on products
    for select to anon, authenticated using (true);

create policy "products_insert_own" on products
    for insert to authenticated with check (
        seller_id in (select id from sellers where user_id = (select auth.uid()))
    );

create policy "products_update_own" on products
    for update to authenticated
    using (seller_id in (select id from sellers where user_id = (select auth.uid())))
    with check (seller_id in (select id from sellers where user_id = (select auth.uid())));

create policy "products_delete_own" on products
    for delete to authenticated
    using (seller_id in (select id from sellers where user_id = (select auth.uid())));

-- محتويات الطلب: تُنشأ وقت إرسال الطلب بس (بدون تعديل/حذف بعدها)، وتُقرأ
-- من نفس الأطراف اللي يقدرون يشوفون الطلب نفسه (أسرة/مندوب/زبون الطلب)
create policy "order_items_insert_own" on order_items
    for insert to authenticated with check (
        order_id in (
            select id from orders
            where customer_id in (select id from customers where user_id = (select auth.uid()))
        )
    );

create policy "order_items_select_owner" on order_items
    for select to authenticated using (
        order_id in (
            select id from orders where
                seller_id in (select id from sellers where user_id = (select auth.uid()))
                or courier_id in (select id from couriers where user_id = (select auth.uid()))
                or customer_id in (select id from customers where user_id = (select auth.uid()))
        )
    );

-- ============================================
-- تخزين صور المنتجات (Supabase Storage)
-- ============================================
insert into storage.buckets (id, name, public)
values ('product-images', 'product-images', true)
on conflict (id) do nothing;

update storage.buckets
set allowed_mime_types = array['image/png','image/jpeg','image/webp','image/gif'],
    file_size_limit = 5242880  -- 5 ميجابايت كحد أقصى
where id = 'product-images';

alter table storage.objects enable row level security;

-- الملفات تُخزّن بمسار "{seller_id}/{اسم عشوائي}.{امتداد}"، فنتحقق من
-- الملكية بأول جزء بالمسار (storage.foldername) — نفس منطق سياسات
-- products_insert_own/delete_own أعلاه. القراءة ما تحتاج سياسة لأن
-- الـ bucket عام (رابط /object/public/ يشتغل بدون تسجيل دخول).
create policy "product_images_insert_own" on storage.objects
    for insert to authenticated with check (
        bucket_id = 'product-images'
        and (storage.foldername(name))[1] in (
            select id::text from sellers where user_id = (select auth.uid())
        )
    );

create policy "product_images_delete_own" on storage.objects
    for delete to authenticated using (
        bucket_id = 'product-images'
        and (storage.foldername(name))[1] in (
            select id::text from sellers where user_id = (select auth.uid())
        )
    );
