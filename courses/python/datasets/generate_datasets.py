"""
Генератор синтетических датасетов для курса «Python + Pandas для аналитиков 20/80».

Создаёт 8 CSV в папке csv/:
  data.csv        — тренировочный (модуль 2): user_id, демография, segment,
                    signup_date; пропуски, грязные строки, дубли
  orders.csv      — E-commerce: заказы (модули 3.2, 3.3, 3.8)
  users.csv       — E-commerce: пользователи
  products.csv    — Маркетплейс: товары (3.4)
  sellers.csv     — Маркетплейс: продавцы (с дублями ключа)
  deliveries.csv  — Логистика (3.5)
  visits.csv      — Здоровье (3.6, самый грязный)
  campaigns.csv   — Маркетинг (3.7)

Вся «грязь» (пропуски, дубли, выбросы, кривые типы) добавляется намеренно
и управляется константами ниже. Seed фиксирован: датасеты воспроизводимы,
эталонные ответы задач не плывут.

Запуск:  python generate_datasets.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 2026
rng = np.random.default_rng(SEED)

OUT = Path(__file__).parent / "csv"
OUT.mkdir(exist_ok=True)

CITIES = ["Moscow", "SPB", "Kazan", "Ekaterinburg", "Novosibirsk"]
CATEGORIES = ["electronics", "books", "clothes", "home", "sport", "beauty"]


def dirty_strings(series: pd.Series, frac: float, modes=("space", "upper", "lower")) -> pd.Series:
    """Портит долю строк: пробелы по краям, регистр."""
    s = series.copy()
    idx = rng.choice(s.index, size=int(len(s) * frac), replace=False)
    for i in idx:
        mode = rng.choice(modes)
        if mode == "space":
            s.loc[i] = " " + str(s.loc[i]) + " "
        elif mode == "upper":
            s.loc[i] = str(s.loc[i]).upper()
        else:
            s.loc[i] = str(s.loc[i]).lower()
    return s


def punch_holes(series: pd.Series, frac: float) -> pd.Series:
    """Пробивает долю значений в NaN."""
    s = series.copy()
    idx = rng.choice(s.index, size=int(len(s) * frac), replace=False)
    s.loc[idx] = np.nan
    return s


# ---------------------------------------------------------------- data.csv
def gen_training(n=500):
    names = [f"user_{i:03d}" for i in range(n)]
    df = pd.DataFrame({
        "name": names,
        "age": rng.integers(16, 65, n).astype(float),
        "city": rng.choice(CITIES, n, p=[0.4, 0.25, 0.15, 0.1, 0.1]),
        "salary": (rng.lognormal(11.2, 0.4, n)).round(-2),
        "email": [f"user_{i:03d}@{rng.choice(['gmail.com', 'yandex.ru', 'mail.ru'])}" for i in range(n)],
    })
    df["age"] = punch_holes(df["age"], 0.05)
    df["salary"] = punch_holes(df["salary"], 0.12)
    df["email"] = punch_holes(df["email"], 0.08)
    df["city"] = dirty_strings(df["city"], 0.1)

    # --- Новые поля для практик модуля 2 (B3, B4, B6, B7) ---
    # ВАЖНО: отдельный независимый RNG. Глобальный rng выше уже потреблён
    # ровно так же, как в первой версии генератора, поэтому остальные
    # датасеты (orders, users, ...) остаются побайтово неизменными.
    rng_extra = np.random.default_rng(SEED + 777)
    df.insert(0, "user_id", np.arange(1, n + 1))
    df["segment"] = rng_extra.choice(["new", "active", "vip"], n, p=[0.5, 0.35, 0.15])
    df["signup_date"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng_extra.integers(0, 700, n), unit="D")
    # Немного пропусков в city (~4%) — практики B4 (groupby теряет NaN-ключи) и B6
    city_holes = rng_extra.choice(df.index, size=20, replace=False)
    df.loc[city_holes, "city"] = np.nan
    # 10 полных дублей строк (практика B7: duplicated / drop_duplicates)
    full_dups = df.sample(10, random_state=SEED)
    # 8 дублей user_id с более поздней signup_date
    # (практика B7: «оставь запись с максимальной датой»)
    key_dups = df.sample(8, random_state=SEED + 1).copy()
    key_dups["signup_date"] += pd.to_timedelta(rng_extra.integers(30, 300, 8), unit="D")
    df = pd.concat([df, full_dups, key_dups], ignore_index=True)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    df.to_csv(OUT / "data.csv", index=False)
    return df


# ------------------------------------------------------- orders + users
def gen_ecommerce(n_users=1200, n_orders=5000):
    user_ids = np.arange(1, n_users + 1)
    users = pd.DataFrame({
        "user_id": user_ids,
        "signup_date": pd.to_datetime("2025-01-01")
        + pd.to_timedelta(rng.integers(0, 500, n_users), unit="D"),
        "segment": rng.choice(["new", "regular", "vip"], n_users, p=[0.5, 0.4, 0.1]),
        "channel": rng.choice(["organic", "ads", "referral", "email"], n_users),
    })
    users["segment"] = punch_holes(users["segment"], 0.07)

    # У части пользователей много заказов (повторные покупки)
    buyer_pool = rng.choice(user_ids, size=int(n_users * 0.7), replace=False)
    weights = rng.exponential(1.0, len(buyer_pool))
    weights /= weights.sum()
    order_users = rng.choice(buyer_pool, n_orders, p=weights)

    base_price = {"electronics": 15000, "books": 600, "clothes": 3500,
                  "home": 4500, "sport": 5000, "beauty": 2000}
    cats = rng.choice(CATEGORIES, n_orders)
    prices = np.array([base_price[c] * rng.lognormal(0, 0.5) for c in cats]).round(0)

    orders = pd.DataFrame({
        "order_id": np.arange(10001, 10001 + n_orders),
        "user_id": order_users.astype(float),
        "order_date": pd.to_datetime("2025-06-01")
        + pd.to_timedelta(rng.integers(0, 365, n_orders), unit="D"),
        "city": rng.choice(CITIES, n_orders, p=[0.4, 0.25, 0.15, 0.1, 0.1]),
        "category": cats,
        "price": prices,
        "quantity": rng.choice([1, 1, 1, 2, 2, 3, 0], n_orders),
        "promo_code": rng.choice(["SALE10", "VIP20", "WELCOME"], n_orders),
        "status": rng.choice(["completed", "cancelled", "pending"], n_orders, p=[0.78, 0.12, 0.1]),
    })
    # Грязь
    orders["promo_code"] = punch_holes(orders["promo_code"], 0.65)
    orders["user_id"] = punch_holes(orders["user_id"], 0.02)
    orders["category"] = punch_holes(orders["category"], 0.03)
    orders["city"] = dirty_strings(orders["city"], 0.08)
    neg_idx = rng.choice(orders.index, 25, replace=False)
    orders.loc[neg_idx, "price"] *= -1                      # отрицательные цены
    dup_rows = orders.sample(60, random_state=SEED)          # полные дубли строк
    dup_orders = orders.sample(40, random_state=SEED + 1).copy()
    dup_orders["order_date"] += pd.Timedelta(days=1)         # дубли order_id с другой датой
    orders = pd.concat([orders, dup_rows, dup_orders], ignore_index=True)
    orders = orders.sample(frac=1, random_state=SEED).reset_index(drop=True)

    users.to_csv(OUT / "users.csv", index=False)
    orders.to_csv(OUT / "orders.csv", index=False)
    return orders, users


# --------------------------------------------------- products + sellers
def gen_marketplace(n_products=3000, n_sellers=400):
    sellers = pd.DataFrame({
        "seller_id": np.arange(1, n_sellers + 1),
        "seller_name": [f"seller_{i:03d}" for i in range(1, n_sellers + 1)],
        "rating": rng.uniform(2.5, 5.0, n_sellers).round(1),
        "city": rng.choice(CITIES, n_sellers),
        "is_verified": rng.choice([True, False], n_sellers, p=[0.6, 0.4]),
    })
    sellers["rating"] = punch_holes(sellers["rating"], 0.1)
    # Дубли seller_id с другим рейтингом (заведён дважды)
    dups = sellers.sample(30, random_state=SEED).copy()
    dups["rating"] = rng.uniform(2.5, 5.0, len(dups)).round(1)
    sellers = pd.concat([sellers, dups], ignore_index=True)

    prices = (rng.lognormal(7.5, 0.8, n_products)).round(2)
    price_str = []
    for p in prices:
        style = rng.choice(["clean", "comma", "space"], p=[0.7, 0.2, 0.1])
        if style == "comma":
            price_str.append(str(p).replace(".", ","))
        elif style == "space":
            price_str.append(f" {p} ")
        else:
            price_str.append(str(p))

    # Совсем битые цены — не распознаются и после чистки (~20 шт.)
    broken_idx = rng.choice(n_products, 20, replace=False)
    for i in broken_idx:
        price_str[i] = rng.choice(["н/д", "договорная", "", "1 200,50"])

    products = pd.DataFrame({
        "product_id": np.arange(1, n_products + 1),
        # ~3% битых seller_id (продавца нет в справочнике)
        "seller_id": rng.integers(1, int(n_sellers * 1.03), n_products),
        "category": rng.choice(CATEGORIES, n_products),
        "price": price_str,
        "in_stock": rng.choice([0, 1, 2, 5, 10, 50], n_products, p=[0.15, 0.2, 0.2, 0.2, 0.15, 0.1]),
        "sales_30d": rng.poisson(8, n_products),
    })
    products["category"] = punch_holes(products["category"], 0.04)

    sellers.to_csv(OUT / "sellers.csv", index=False)
    products.to_csv(OUT / "products.csv", index=False)
    return products, sellers


# ------------------------------------------------------------ deliveries
def gen_logistics(n=4000):
    created = pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 120, n), unit="D")
    days = rng.gamma(2.5, 1.5, n).round(0).astype(int) + 1
    delivered = created + pd.to_timedelta(days, unit="D")
    status_raw = rng.choice(["delivered", "in_transit", "lost"], n, p=[0.85, 0.13, 0.02])

    d = pd.DataFrame({
        "delivery_id": np.arange(1, n + 1),
        "order_id": rng.integers(10001, 15001, n),
        "created_at": created,
        "delivered_at": delivered,
        "status": status_raw,
        "warehouse": rng.choice(["WH-Moscow", "WH-SPB", "WH-Kazan"], n, p=[0.5, 0.3, 0.2]),
        "courier_company": rng.choice(["FastBox", "CDEK-like", "OwnCourier"], n),
        "distance_km": rng.lognormal(3, 0.8, n).round(1),
    })
    # Не доставлено → delivered_at пропуск
    d.loc[d["status"] != "delivered", "delivered_at"] = pd.NaT
    # Грязный регистр статусов
    d["status"] = dirty_strings(d["status"], 0.25, modes=("space", "upper"))
    d["courier_company"] = punch_holes(d["courier_company"], 0.08)
    # Выбросы дистанции
    out_idx = rng.choice(d.index, 15, replace=False)
    d.loc[out_idx, "distance_km"] = rng.uniform(3000, 9000, 15).round(1)
    d.to_csv(OUT / "deliveries.csv", index=False)
    return d


# ---------------------------------------------------------------- visits
def gen_health(n=3500):
    date1 = pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 150, n), unit="D")
    specs = rng.choice(["терапевт", "кардиолог", "невролог", "хирург", "эндокринолог"],
                       n, p=[0.4, 0.2, 0.15, 0.15, 0.1])
    v = pd.DataFrame({
        "visit_id": np.arange(1, n + 1),
        "patient_id": rng.integers(1, 1200, n),
        "visit_date": date1,
        "doctor_specialty": specs,
        "patient_age": rng.normal(45, 18, n).round(0),
        "height_cm": rng.normal(170, 10, n).round(0),
        "weight_kg": rng.normal(75, 15, n).round(1),
        "visit_price": rng.choice([0, 1500, 2500, 3500, 5000], n, p=[0.35, 0.2, 0.2, 0.15, 0.1]),
        "clinic": rng.choice(["Центр", "Север", "Юг"], n),
    })
    # Два формата дат вперемешку
    fmt_mask = rng.random(n) < 0.3
    dates = v["visit_date"].dt.strftime("%Y-%m-%d").where(
        ~fmt_mask, v["visit_date"].dt.strftime("%d.%m.%Y"))
    v["visit_date"] = dates
    # Выбросы возраста + пропуски
    bad_idx = rng.choice(v.index, 40, replace=False)
    v.loc[bad_idx, "patient_age"] = rng.choice([0, 150, 199, -1], 40)
    v["patient_age"] = punch_holes(v["patient_age"], 0.06)
    v["height_cm"] = punch_holes(v["height_cm"], 0.15)
    v["weight_kg"] = punch_holes(v["weight_kg"], 0.18)
    # Грязные специальности (регистр/пробелы + латинская подмена буквы)
    v["doctor_specialty"] = dirty_strings(v["doctor_specialty"], 0.2)
    typo_idx = rng.choice(v.index, 50, replace=False)
    v.loc[typo_idx, "doctor_specialty"] = (
        v.loc[typo_idx, "doctor_specialty"].str.strip().str.lower()
         .str.replace("т", "t", n=1))   # «tерапевт» — латинская t
    # Полные дубли
    v = pd.concat([v, v.sample(80, random_state=SEED)], ignore_index=True)
    v = v.sample(frac=1, random_state=SEED).reset_index(drop=True)
    v.to_csv(OUT / "visits.csv", index=False)
    return v


# ------------------------------------------------------------- campaigns
def gen_marketing(n_campaigns=60, n_days=60):
    channels = ["context", "social", "seo", "email", "blogger"]
    rows = []
    camp_channel = {cid: rng.choice(channels) for cid in range(1, n_campaigns + 1)}
    chan_quality = {"context": 1.0, "social": 0.8, "seo": 1.5, "email": 1.3, "blogger": 0.6}
    start = pd.to_datetime("2026-03-01")
    for cid, chan in camp_channel.items():
        is_dead = rng.random() < 0.08   # кампании, которые тратят и не конвертят
        for day in range(int(rng.integers(20, n_days))):
            imp = int(rng.lognormal(8, 1))
            clicks = int(imp * rng.uniform(0.005, 0.05))
            spend = 0.0 if chan == "seo" and rng.random() < 0.5 else round(clicks * rng.uniform(10, 60), 0)
            conv = 0 if is_dead else int(clicks * rng.uniform(0.01, 0.08) * chan_quality[chan])
            revenue = round(conv * rng.uniform(1500, 4000) * chan_quality[chan], 0)
            rows.append({
                "date": (start + pd.Timedelta(days=day)).date(),
                "campaign_id": cid,
                "channel": chan,
                "spend": spend,
                "impressions": imp,
                "clicks": clicks,
                "conversions": conv,
                "revenue": revenue,
            })
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "campaigns.csv", index=False)
    return c


if __name__ == "__main__":
    gen_training()
    gen_ecommerce()
    gen_marketplace()
    gen_logistics()
    gen_health()
    gen_marketing()
    for f in sorted(OUT.glob("*.csv")):
        df = pd.read_csv(f)
        print(f"{f.name:18} {df.shape[0]:>6} строк × {df.shape[1]} колонок")
