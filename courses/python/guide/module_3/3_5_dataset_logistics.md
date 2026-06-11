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
| status | str | delivered / in_transit / lost; ⚠️ грязные регистр и пробелы: DELIVERED, « delivered» |
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
2. Сколько доставок без даты доставки (delivered_at пропущен)? Разложи их по статусам: это только «в пути» или кто-то ещё?
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
# 📌 Проверь себя: 9 вариантов до чистки → 3 статуса после:
# delivered 3382, in_transit 526, lost 92

# 2
d["delivered_at"].isna().sum()
d.loc[d["delivered_at"].isna(), "status"].value_counts()
# без даты не только «в пути»: потерянные (lost) тоже никогда не доедут
# 📌 Проверь себя: 618 без даты = 526 in_transit + 92 lost

# 3
d["delivery_days"] = (d["delivered_at"] - d["created_at"]).dt.days
d["delivery_days"].mean(), d["delivery_days"].median(), d["delivery_days"].max()
# среднее тянут вверх редкие долгие доставки → для SLA смотри медиану и квантили
# 📌 Проверь себя: среднее ≈ 4.71, медиана 4, максимум 22 дня

# 4
d.groupby("warehouse")["delivery_days"].mean().sort_values(ascending=False)
# 📌 Проверь себя: медленнее всех WH-Kazan ≈ 4.78 дня

# 5
d.groupby(d["created_at"].dt.to_period("W"))["delivery_id"].count()
# 📌 Проверь себя: 18 недель

# 6
d["created_at"].dt.dayofweek.value_counts().sort_index()
# 📌 Проверь себя: четверг (dayofweek == 3), 617 доставок

# 7
(d.assign(long=d["delivery_days"] > 7)
  .groupby("courier_company", dropna=False)["long"].mean()
  .sort_values(ascending=False))
# 📌 Проверь себя: худшая CDEK-like ≈ 10.9%

# 8
d["distance_km"].describe()
outliers = d[d["distance_km"] > d["distance_km"].quantile(0.99)]
len(outliers)
# решение зависит от задачи: для среднего времени доставки по городу — смотреть
# глазами и чинить источник; молча удалять — последний вариант
# 📌 Проверь себя: порог q99 ≈ 139.5 км, за ним 40 строк, максимум 8607.6 км

# 9
d.groupby("warehouse").agg(
    total=("delivery_id", "count"),
    delivered=("delivered_at", "count"),     # count не считает NaN — удобно
    avg_days=("delivery_days", "mean"),
    avg_km=("distance_km", "mean"),
).sort_values("total", ascending=False)
# 📌 Проверь себя: лидер WH-Moscow — 2047 доставок, из них доставлено 1736
```

</details>

➡️ Дальше: [3.6 Здоровье](3_6_dataset_health.md)
