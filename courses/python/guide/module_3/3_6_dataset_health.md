# 🎯 3.6 Датасет: Здоровье

Приёмы в сети клиник. Главный фокус — **чистка данных**: этот датасет самый грязный из пяти, как реальная выгрузка из старой CRM.

## Схема

**visits.csv** — приёмы (~3 500 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| visit_id | int | ключ, есть полные дубли строк |
| patient_id | int | |
| visit_date | str | ⚠️ два формата дат вперемешку |
| doctor_specialty | str | ⚠️ опечатки и регистр: «Терапевт», «терапевт », «Tерапевт» |
| patient_age | float | ⚠️ выбросы: 0, 150, пропуски |
| height_cm | float | пропуски |
| weight_kg | float | пропуски |
| visit_price | float | 0 для приёмов по ОМС |
| clinic | str | филиал |

## Задачи

1. Первичный анализ. Составь список всех проблем качества данных, которые видишь (минимум 5).
2. Удали полные дубли. Сколько строк ушло?
3. Приведи `visit_date` к datetime (подсказка: `pd.to_datetime(..., format="mixed")` или два прохода с errors="coerce").
4. Почисти `doctor_specialty`: пробелы, регистр. Выведи топ специальностей до и после — насколько изменилась картина?
5. Обработай `patient_age`: значения вне диапазона 0–110 замени на NaN. Сколько значений заменено? Посчитай медианный возраст по специальностям.
6. Создай колонку BMI = вес / (рост в метрах)². Для скольких приёмов BMI посчитать нельзя и почему?
7. Сравни среднюю стоимость платных приёмов (price > 0) по филиалам.
8. Какая доля приёмов по ОМС (price == 0) в каждом филиале?
9. Найди пациентов с 3+ приёмами. Какая у них самая частая специальность врача?
10. Сохрани очищенный датасет. Напиши комментарием в ноутбуке 3 строки: что почистил, что заменил на NaN, что оставил как есть и почему.

<details>
<summary>✅ Решения</summary>

```python
import pandas as pd

v = pd.read_csv("visits.csv")

# 2
before = len(v)
v = v.drop_duplicates()
before - len(v)

# 3
v["visit_date"] = pd.to_datetime(v["visit_date"], format="mixed")

# 4
v["doctor_specialty"].value_counts().head(10)
v["doctor_specialty"] = v["doctor_specialty"].str.strip().str.lower()
v["doctor_specialty"].value_counts().head(10)

# 5
mask_bad = (v["patient_age"] < 0) | (v["patient_age"] > 110)
mask_bad.sum()
v.loc[mask_bad, "patient_age"] = None
v.groupby("doctor_specialty")["patient_age"].median()

# 6
v["bmi"] = v["weight_kg"] / (v["height_cm"] / 100) ** 2
v["bmi"].isna().sum()   # пропуск роста ИЛИ веса → NaN в BMI

# 7
v[v["visit_price"] > 0].groupby("clinic")["visit_price"].mean()

# 8
(v.assign(oms=v["visit_price"] == 0)
  .groupby("clinic")["oms"].mean())

# 9
cnt = v.groupby("patient_id")["visit_id"].count()
frequent = cnt[cnt >= 3].index
v[v["patient_id"].isin(frequent)]["doctor_specialty"].value_counts().head(1)

# 10
v.to_csv("visits_clean.csv", index=False)
```

</details>

➡️ Дальше: [3.7 Маркетинг](3_7_dataset_marketing.md)
