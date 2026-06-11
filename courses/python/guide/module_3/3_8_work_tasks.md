# 🎯 3.8 Рабочие задачи аналитика

Четыре задачи уровня junior/middle в формате «как на работе»: продакт приходит с вопросом, ты отвечаешь данными и выводом. Все — на датасете E-commerce (orders.csv + users.csv).

За смыслом метрик (почему retention так важен, как читать когорты) — курс «Продуктовые метрики и кейсы». Здесь — техника расчёта в pandas.

---

## Задача 1. Retention по когортам

**Вопрос продакта:** «Возвращаются ли к нам покупатели? Покажи retention 1-го, 2-го и 3-го месяца по когортам».

**План решения:**

1. Когорта пользователя = месяц его первого заказа
2. Для каждого заказа посчитай «возраст» = месяцев с первого заказа
3. Сведи в таблицу: когорты × месяц жизни → доля вернувшихся

<details>
<summary>✅ Решение</summary>

```python
import pandas as pd

orders_raw = pd.read_csv("orders.csv")
users = pd.read_csv("users.csv")
orders_raw["order_date"] = pd.to_datetime(orders_raw["order_date"])

# Чистка в самом начале — 60 дублей и 25 отрицательных цен попадут в метрики
# если не убрать (модуль 3.3 объяснял почему это критично)
orders_all = orders_raw.drop_duplicates().query("price > 0").copy()

# orders1 — только completed заказы без пропуска user_id (для когортного анализа)
orders1 = orders_all[orders_all["status"] == "completed"].dropna(subset=["user_id"]).copy()
orders1["order_month"] = orders1["order_date"].dt.to_period("M")

# 1. Когорта = месяц первого заказа
first = orders1.groupby("user_id")["order_month"].min().rename("cohort")
orders1 = orders1.merge(first, on="user_id")

# 2. Возраст заказа в месяцах
orders1["age"] = (orders1["order_month"] - orders1["cohort"]).apply(lambda x: x.n)

# 3. Уникальные пользователи: когорта × возраст
cohort_users = (orders1.groupby(["cohort", "age"])["user_id"]
                      .nunique().reset_index())

table = cohort_users.pivot_table(index="cohort", columns="age",
                                 values="user_id")

# 4. Делим на размер когорты (возраст 0)
retention = table.div(table[0], axis=0).round(3)
retention
```

**Как читать:** строка — когорта, колонка 1 — доля вернувшихся через месяц. Если по диагонали вниз ретеншн растёт — продукт улучшается.

📌 **Проверь себя:** M1 первой когорты (2025-06) = **0.465** (46.5% вернулись на второй месяц).

</details>

---

## Задача 2. Воронка

**Вопрос продакта:** «Где мы теряем заказы? Покажи воронку по статусам».

Воронка здесь — по статусам заказа: created (все) → pending пройден → completed. На событийных логах (visit → cart → checkout → purchase) техника та же: уникальные пользователи на каждом шаге, конверсия = шаг N+1 / шаг N.

<details>
<summary>✅ Решение</summary>

```python
# orders_all определён в задаче 1 — все заказы после drop_duplicates + price > 0
# воронка строится по ВСЕМ статусам, без фильтра по status
total = len(orders_all)                                      # создано
not_cancelled = (orders_all["status"] != "cancelled").sum()  # не отменено
completed = (orders_all["status"] == "completed").sum()      # завершено

funnel = pd.DataFrame({
    "step": ["created", "not_cancelled", "completed"],
    "count": [total, not_cancelled, completed],
})
funnel["conversion_from_prev"] = funnel["count"] / funnel["count"].shift(1)
funnel["conversion_from_start"] = funnel["count"] / total
funnel
```

**Вывод формулируй так:** «теряем X% на отмене; сильнее всего проседает шаг такой-то — копать туда».

📌 **Проверь себя:** created = **5 015**, конверсия created→not_cancelled = **87.5%**, not_cancelled→completed = **88.5%**.

</details>

---

## Задача 3. ARPU / ARPPU / средний чек по сегментам

**Вопрос продакта:** «Сколько нам приносит пользователь в каждом сегменте?»

Различай три метрики: ARPU — выручка на ВСЕХ пользователей сегмента, ARPPU — на платящих, средний чек — на заказ.

<details>
<summary>✅ Решение</summary>

```python
# clean — completed заказы после чистки (orders_all из задачи 1)
clean = orders_all[orders_all["status"] == "completed"].copy()
clean["revenue"] = clean["price"] * clean["quantity"]

rev = (clean.merge(users[["user_id", "segment"]], on="user_id", how="left")
            .groupby("segment", dropna=False)
            .agg(revenue=("revenue", "sum"),
                 payers=("user_id", "nunique"),
                 orders_cnt=("order_id", "count")))

# всего пользователей в сегменте — из users, не из заказов!
seg_size = users.groupby("segment", dropna=False)["user_id"].nunique()

rev["arpu"] = rev["revenue"] / seg_size
rev["arppu"] = rev["revenue"] / rev["payers"]
rev["avg_check"] = rev["revenue"] / rev["orders_cnt"]
rev.round(0)
```

> ⚠️ **Ловушка:** знаменатель ARPU — все пользователи сегмента (таблица users), а не только те, кто есть в заказах. Посчитаешь от заказов — получишь ARPPU и завысишь метрику.

📌 **Проверь себя:** ARPU сегмента new ≈ **26 673 ₽**, ARPPU new ≈ **47 765 ₽**, средний чек new ≈ **8 707 ₽**. VIP по ARPU выше new и regular — **29 685 ₽**.

</details>

---

## Задача 4. Когортная таблица выручки

**Вопрос продакта:** «Сколько денег приносит когорта в первый, второй, третий месяц жизни?»

Та же механика, что в задаче 1, но в ячейках — выручка на пользователя когорты (LTV-кривая по сути).

<details>
<summary>✅ Решение</summary>

```python
# Добавляем cohort и age к clean (используем clean из задачи 3)
clean["order_month"] = clean["order_date"].dt.to_period("M")
first_ltv = clean.groupby("user_id")["order_date"].min()
clean = clean.merge(first_ltv.dt.to_period("M").rename("cohort"), on="user_id")
clean["age"] = (clean["order_month"] - clean["cohort"]).apply(lambda x: x.n)

rev_table = clean.pivot_table(index="cohort", columns="age",
                               values="revenue", aggfunc="sum")

cohort_size = clean.groupby("cohort")["user_id"].nunique()
ltv = rev_table.div(cohort_size, axis=0).round(0)

# накопленная выручка на пользователя по месяцам жизни
ltv_cum = ltv.cumsum(axis=1)
ltv_cum
```

📌 **Проверь себя:** накопленный LTV первой когорты (2025-06): M0 = **10 939 ₽**, M0+M1 = **16 371 ₽**, M0+M1+M2 = **21 191 ₽**.

</details>

---

## Чек после каждой задачи

- [ ] результат проверен глазами (head, размеры, нет ли inf/NaN в метриках)
- [ ] вывод сформулирован одним-двумя предложениями человеческим языком
- [ ] код читается сверху вниз без прыжков

➡️ Дальше: [3.9 Мини-визуализация](3_9_visualization.md)
