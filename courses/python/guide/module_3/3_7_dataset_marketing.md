# 🎯 3.7 Датасет: Маркетинг

Рекламные кампании по каналам. Главный фокус — **расчёт производных метрик**: CTR, CR, CPC, CAC, ROMI. Деление на ноль прилагается.

## Схема

**campaigns.csv** — дневная статистика кампаний (~2 500 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| date | str | день |
| campaign_id | int | |
| channel | str | context / social / seo / email / blogger |
| spend | float | расход, есть нули (органика) |
| impressions | int | показы |
| clicks | int | клики, есть нули |
| conversions | int | покупки |
| revenue | float | выручка от конверсий |

## Минимум теории: метрики

| Метрика | Формула |
|---|---|
| CTR | clicks / impressions |
| CR | conversions / clicks |
| CPC | spend / clicks |
| CAC | spend / conversions |
| ROMI | (revenue − spend) / spend |

> ⚠️ **Деление на ноль:** в pandas `x / 0` даёт `inf`, а не ошибку — и inf молча ломает средние. В этом датасете inf живёт в CAC (spend > 0 при conversions == 0) и в ROMI (spend == 0). После делений проверяй: `np.isinf(df["cac"]).sum()`, заменяй `df.replace([np.inf, -np.inf], np.nan)`.

## Задачи

1. Посчитай CTR, CR, CPC, CAC, ROMI для каждой строки. Разберись с inf: где возник и почему, замени на NaN.
2. Сводка по каналам: суммарный spend, revenue, конверсии и средневзвешенные CTR/CR (считать от сумм, не среднее от строк!).
3. Какой канал самый дорогой по CAC? Какой самый прибыльный по ROMI?
4. Динамика расходов и выручки по неделям. В какие недели маркетинг сработал «в минус»?
5. Найди кампании, которые тратят, но не конвертят (spend > 0, conversions == 0 за всё время). Сколько денег на них ушло?
6. Сравни эффективность каналов в будни и выходные.
7. Топ-5 кампаний по ROMI среди тех, у кого суммарный spend > 150 000 (почему фильтр важен — объясни: высокий ROMI на маленьком бюджете не факт, что переживёт масштабирование).
8. Витрина «канал × месяц»: ROMI в сводной таблице. Какой канал стабильнее остальных?

<details>
<summary>✅ Решения</summary>

```python
import pandas as pd
import numpy as np

c = pd.read_csv("campaigns.csv")
c["date"] = pd.to_datetime(c["date"])

# 1
c["ctr"] = c["clicks"] / c["impressions"]
c["cr"] = c["conversions"] / c["clicks"]
c["cpc"] = c["spend"] / c["clicks"]
c["cac"] = c["spend"] / c["conversions"]
c["romi"] = (c["revenue"] - c["spend"]) / c["spend"]
# inf возникает в cac (spend > 0, conversions == 0) и в romi (spend == 0)
c = c.replace([np.inf, -np.inf], np.nan)
# 📌 Проверь себя: inf в cac = 727 строк, inf в romi = 162 строки

# 2 — средневзвешенно: от сумм!
by_channel = c.groupby("channel").agg(
    spend=("spend", "sum"),
    revenue=("revenue", "sum"),
    impressions=("impressions", "sum"),
    clicks=("clicks", "sum"),
    conversions=("conversions", "sum"),
)
by_channel["ctr"] = by_channel["clicks"] / by_channel["impressions"]
by_channel["cr"] = by_channel["conversions"] / by_channel["clicks"]

# 3
by_channel["cac"] = by_channel["spend"] / by_channel["conversions"]
by_channel["romi"] = (by_channel["revenue"] - by_channel["spend"]) / by_channel["spend"]
by_channel.sort_values("cac", ascending=False).head(1)
by_channel.sort_values("romi", ascending=False).head(1)
# 📌 Проверь себя: самый дорогой CAC — blogger (≈ 1 862 ₽ за конверсию),
# лучший ROMI — seo (≈ 15.03, т.е. +1 403% к вложениям)

# 4
weekly = c.groupby(c["date"].dt.to_period("W")).agg(
    spend=("spend", "sum"), revenue=("revenue", "sum"))
weekly[weekly["revenue"] < weekly["spend"]]
# 📌 Проверь себя: 0 недель «в минус» — маркетинг всегда окупается на уровне недели

# 5
agg = c.groupby("campaign_id").agg(
    spend=("spend", "sum"), conv=("conversions", "sum"))
dead = agg[(agg["spend"] > 0) & (agg["conv"] == 0)]
len(dead), dead["spend"].sum()
# 📌 Проверь себя: 4 кампании без конверсий, потрачено на них ≈ 709 411 ₽

# 6
c["is_weekend"] = c["date"].dt.dayofweek >= 5
c.groupby(["channel", "is_weekend"]).agg(
    spend=("spend", "sum"), revenue=("revenue", "sum"))

# 7 — фильтр spend > 150 000: важен, иначе топ займут кампании с 40–60k spend,
# у которых аномально высокий ROMI на маленьком объёме (не масштабируется)
camp = c.groupby("campaign_id").agg(
    spend=("spend", "sum"), revenue=("revenue", "sum"))
camp = camp[camp["spend"] > 150000]
camp["romi"] = (camp["revenue"] - camp["spend"]) / camp["spend"]
camp.sort_values("romi", ascending=False).head(5)
# 📌 Проверь себя: топ-1 по ROMI (spend > 150k) — campaign 14, ROMI ≈ 4.73

# 8
c.pivot_table(index="channel", columns=c["date"].dt.to_period("M"),
              values="romi", aggfunc="mean")
```

</details>

> 💡 **Главная мысль задачи 2:** среднее от построчных CTR ≠ CTR канала. Метрики-отношения агрегируются от сумм числителя и знаменателя. Это любимая проверка на понимание в собеседованиях и реальный источник ошибок в отчётах.

➡️ Дальше: [3.8 Рабочие задачи аналитика](3_8_work_tasks.md)
