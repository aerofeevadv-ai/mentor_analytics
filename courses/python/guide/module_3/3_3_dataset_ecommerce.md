# 🎯 3.3 Датасет: E-commerce

Интернет-магазин. Основной датасет курса — на нём же работает ежедневный практикум.

## Схема

**orders.csv** — заказы (~5 000 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| order_id | int | есть дубли — «задвоенные» заказы |
| user_id | float | есть пропуски |
| order_date | str | приводить к datetime |
| city | str | грязь: регистр, пробелы |
| category | str | есть пропуски |
| price | float | есть отрицательные (возвраты? ошибки?) |
| quantity | int | есть нули |
| promo_code | str | много пропусков (= заказ без промо) |
| status | str | completed / cancelled / pending |

**users.csv** — пользователи (~1 200 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| user_id | int | ключ |
| signup_date | str | дата регистрации |
| segment | str | new / regular / vip, есть пропуски |
| channel | str | канал привлечения |

## Задачи

1. Проведи первичный анализ обеих таблиц «порядком профи». Запиши 3 наблюдения о качестве данных.
2. Какая доля заказов отменяется? А по городам — где доля отмен максимальна?
3. Посчитай выручку магазина (только completed, price > 0). Сравни с «наивной» суммой по всем строкам — насколько грязь искажает цифру?
4. Топ-3 категории по выручке в каждом городе.
5. Средний чек по сегментам пользователей. У какого сегмента он выше и насколько?
6. Сколько пользователей сделали больше одного заказа? Какая доля выручки приходится на них?
7. Динамика выручки по месяцам (подсказка: `pd.to_datetime` + `dt.to_period("M")`).
8. Заказы с промокодом против заказов без: сравни средний чек и долю отмен. Сформулируй вывод одним предложением.
9. Найди города, где средний чек выше общего по магазину.
10. Собери одну таблицу-витрину по пользователям: число заказов, выручка, дата первого и последнего заказа, любимая категория (mode). Сохрани в CSV.

<details>
<summary>✅ Решения</summary>

```python
import pandas as pd

orders = pd.read_csv("orders.csv")
users = pd.read_csv("users.csv")
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["revenue"] = orders["price"] * orders["quantity"]

# 1
orders.info(); orders.describe(); orders.isna().sum()
users["signup_date"] = pd.to_datetime(users["signup_date"])
# возможные наблюдения: 60 полных дублей строк; 25 отрицательных цен;
# 103 заказа без user_id; 155 без категории; city в 19 вариантах вместо 5.
# и находка посерьёзнее — заказы РАНЬШЕ регистрации пользователя:
chk = orders.merge(users[["user_id", "signup_date"]], on="user_id", how="left")
(chk["order_date"] < chk["signup_date"]).sum()
# 📌 Проверь себя: 1773 заказа из 5100 сделаны до signup_date — это не баг твоего
# кода, а свойство данных (так бывает: гостевые заказы, миграция CRM). На работе
# такое наблюдение несут владельцу данных, а не молча чинят.

# 2
# чистим city один раз прямо в колонке — все задачи ниже работают с чистым city
orders["city"] = orders["city"].str.strip().str.lower()
orders["status"].value_counts(normalize=True)
(orders.assign(is_cancelled=orders["status"] == "cancelled")
       .groupby("city")["is_cancelled"]
       .mean().sort_values(ascending=False))
# 📌 Проверь себя: отменяется 12.5% заказов; максимум отмен — kazan (13.3%)

# 3
# .copy() — иначе создание колонок в задаче 8 даст SettingWithCopyWarning
clean = orders[(orders["status"] == "completed") & (orders["price"] > 0)].copy()
clean["revenue"].sum(), orders["revenue"].sum()
# 📌 Проверь себя: 33 379 878 против «наивных» 42 639 987 — грязь завышает на 27.7%

# 4
# city уже чистый — почистили в задаче 2; иначе тут было бы 19 «городов»
(clean.groupby(["city", "category"])["revenue"].sum()
      .reset_index()
      .sort_values(["city", "revenue"], ascending=[True, False])
      .groupby("city").head(3))
# 📌 Проверь себя: топ-1 в moscow — electronics, 6 734 562

# 5
m = clean.merge(users[["user_id", "segment"]], on="user_id", how="left")
m.groupby("segment", dropna=False)["revenue"].mean()
# 📌 Проверь себя: выше всех new ≈ 8 730, у regular ≈ 8 213 (разница ~6%)

# 6
cnt = clean.groupby("user_id")["order_id"].count()
repeat_ids = cnt[cnt > 1].index
len(repeat_ids)
clean[clean["user_id"].isin(repeat_ids)]["revenue"].sum() / clean["revenue"].sum()
# 📌 Проверь себя: 572 пользователя, на них 95.5% выручки

# 7
clean.groupby(clean["order_date"].dt.to_period("M"))["revenue"].sum()
# 📌 Проверь себя: 12 месяцев, пик 2025-09 ≈ 3 291 023

# 8
clean["has_promo"] = clean["promo_code"].notna()
clean.groupby("has_promo")["revenue"].mean()
(orders.assign(has_promo=orders["promo_code"].notna(),
               is_cancelled=orders["status"] == "cancelled")
       .groupby("has_promo")["is_cancelled"].mean())
# 📌 Проверь себя: чек с промо ≈ 8 782 против 8 327; отмены 12.9% против 12.3%

# 9
# снова работаем с чистым city из задачи 2
avg_total = clean["revenue"].mean()
city_avg = clean.groupby("city")["revenue"].mean()
city_avg[city_avg > avg_total]
# 📌 Проверь себя: общий средний чек ≈ 8 487, выше него 3 города — kazan,
# novosibirsk, spb

# 10
profile = clean.groupby("user_id").agg(
    orders_cnt=("order_id", "count"),
    revenue=("revenue", "sum"),
    first_order=("order_date", "min"),
    last_order=("order_date", "max"),
    fav_category=("category", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
)
profile.to_csv("user_profile.csv")
# 📌 Проверь себя: 686 строк в витрине
```

</details>

➡️ Дальше: [3.4 Маркетплейс](3_4_dataset_marketplace.md)
