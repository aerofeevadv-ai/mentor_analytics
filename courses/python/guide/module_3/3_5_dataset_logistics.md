# 🎯 3.5 Датасет: Логистика

Доставки интернет-заказов. Главный фокус — **работа с датами**: to_datetime, разницы дат, группировка по периодам.

## Схема

**deliveries.csv** — доставки (~4 000 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| delivery_id | int | ключ |
| order_id | int | |
| created_at | str | дата создания, приводить к datetime |
| delivered_at | str | ⚠️ пропуск = ещё не доставлено |
| status | str | ⚠️ грязный регистр: Delivered / delivered / DELIVERED |
| warehouse | str | склад отправки |
| courier_company | str | есть пропуски |
| distance_km | float | есть выбросы |

## Минимум теории: даты в pandas

```python
df["created_at"] = pd.to_datetime(df["created_at"])

df["created_at"].dt.date       # дата без времени
df["created_at"].dt.month      # месяц
df["created_at"].dt.dayofweek  # день недели (0 = понедельник)
df["created_at"].dt.to_period("M")   # период-месяц для группировок

# Разница дат → timedelta
df["delivery_days"] = (df["delivered_at"] - df["created_at"]).dt.days
```

## Задачи

1. Приведи обе даты к datetime. Почисти `status` (strip + lower) и посчитай распределение статусов до и после чистки.
2. Сколько доставок ещё в пути (delivered_at пропущен)? Сходится ли это с числом статусов «в пути»?
3. Посчитай срок доставки в днях. Выведи среднее и медиану. Почему они различаются — посмотри максимум.
4. Средний срок доставки по складам. Какой склад медленнее всех?
5. Динамика числа доставок по неделям (`dt.to_period("W")`).
6. В какой день недели создаётся больше всего доставок?
7. Доля доставок дольше 7 дней по курьерским компаниям (пропуск компании — отдельная категория).
8. Найди аномалии в distance_km (describe → порог). Сколько их и что с ними делать: удалить, обрезать или разбираться?
9. Витрина по складам: доставок всего, доставлено, среднее время, средняя дистанция. Отсортируй по числу доставок.

<details>
<summary>✅ Решения</summary>

```python
import pandas as pd

d = pd.read_csv("deliveries.csv")

# 1
d["created_at"] = pd.to_datetime(d["created_at"])
d["delivered_at"] = pd.to_datetime(d["delivered_at"])
d["status"].value_counts()
d["status"] = d["status"].str.strip().str.lower()
d["status"].value_counts()

# 2
d["delivered_at"].isna().sum()
(d["status"] != "delivered").sum()

# 3
d["delivery_days"] = (d["delivered_at"] - d["created_at"]).dt.days
d["delivery_days"].mean(), d["delivery_days"].median(), d["delivery_days"].max()
# среднее тянут вверх редкие долгие доставки → для SLA смотри медиану и квантили

# 4
d.groupby("warehouse")["delivery_days"].mean().sort_values(ascending=False)

# 5
d.groupby(d["created_at"].dt.to_period("W"))["delivery_id"].count()

# 6
d["created_at"].dt.dayofweek.value_counts().sort_index()

# 7
(d.assign(long=d["delivery_days"] > 7)
  .groupby("courier_company", dropna=False)["long"].mean()
  .sort_values(ascending=False))

# 8
d["distance_km"].describe()
outliers = d[d["distance_km"] > d["distance_km"].quantile(0.99)]
len(outliers)
# решение зависит от задачи: для среднего времени доставки по городу — смотреть
# глазами и чинить источник; молча удалять — последний вариант

# 9
d.groupby("warehouse").agg(
    total=("delivery_id", "count"),
    delivered=("delivered_at", "count"),     # count не считает NaN — удобно
    avg_days=("delivery_days", "mean"),
    avg_km=("distance_km", "mean"),
).sort_values("total", ascending=False)
```

</details>

➡️ Дальше: [3.6 Здоровье](3_6_dataset_health.md)
