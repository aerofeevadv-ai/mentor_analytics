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

# 2
orders["status"].value_counts(normalize=True)
(orders.assign(is_cancelled=orders["status"] == "cancelled")
       .groupby(orders["city"].str.strip().str.lower())["is_cancelled"]
       .mean().sort_values(ascending=False))

# 3
clean = orders[(orders["status"] == "completed") & (orders["price"] > 0)]
clean["revenue"].sum(), orders["revenue"].sum()

# 4
(clean.groupby(["city", "category"])["revenue"].sum()
      .reset_index()
      .sort_values(["city", "revenue"], ascending=[True, False])
      .groupby("city").head(3))

# 5
m = clean.merge(users[["user_id", "segment"]], on="user_id", how="left")
m.groupby("segment", dropna=False)["revenue"].mean()

# 6
cnt = clean.groupby("user_id")["order_id"].count()
repeat_ids = cnt[cnt > 1].index
len(repeat_ids)
clean[clean["user_id"].isin(repeat_ids)]["revenue"].sum() / clean["revenue"].sum()

# 7
clean.groupby(clean["order_date"].dt.to_period("M"))["revenue"].sum()

# 8
clean["has_promo"] = clean["promo_code"].notna()
clean.groupby("has_promo")["revenue"].mean()
(orders.assign(has_promo=orders["promo_code"].notna(),
               is_cancelled=orders["status"] == "cancelled")
       .groupby("has_promo")["is_cancelled"].mean())

# 9
avg_total = clean["revenue"].mean()
city_avg = clean.groupby("city")["revenue"].mean()
city_avg[city_avg > avg_total]

# 10
profile = clean.groupby("user_id").agg(
    orders_cnt=("order_id", "count"),
    revenue=("revenue", "sum"),
    first_order=("order_date", "min"),
    last_order=("order_date", "max"),
    fav_category=("category", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
)
profile.to_csv("user_profile.csv")
```

</details>

➡️ Дальше: [3.4 Маркетплейс](3_4_dataset_marketplace.md)
