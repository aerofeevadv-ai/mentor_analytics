# 🎯 3.6 Датасет: Здоровье

Приёмы в сети клиник. Главный фокус — **чистка данных**: этот датасет самый грязный из пяти, как реальная выгрузка из старой CRM.

## Схема

**visits.csv** — приёмы (~3 500 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| visit_id | int | ключ, есть полные дубли строк |
| patient_id | int | |
| visit_date | str | ⚠️ два формата дат вперемешку |
| doctor_specialty | str | ⚠️ грязь: «терапевт », «ТЕРАПЕВТ», «tерапевт» (латинская t) |
| patient_age | float | ⚠️ выбросы: 0, отрицательные, 150, пропуски |
| height_cm | float | пропуски |
| weight_kg | float | пропуски |
| visit_price | float | 0 для приёмов по ОМС |
| clinic | str | филиал |

## Задачи

1. Первичный анализ. Составь список всех проблем качества данных, которые видишь (минимум 5).
2. Удали полные дубли. Сколько строк ушло?
3. Приведи `visit_date` к datetime. Здесь два формата дат вперемешку — проверь после конвертации, что месяцы не «поехали» (подсказка: `dayfirst=True` или два прохода с явными `format` и `errors="coerce"`).
4. Почисти `doctor_specialty`: пробелы, регистр, опечатки. Выведи топ специальностей до и после — насколько изменилась картина?
5. Обработай `patient_age`: значения вне диапазона 1–110 замени на NaN (возраст 0 в этой выгрузке — ошибка ввода, а не младенцы, как и отрицательные). Сколько значений заменено? Посчитай медианный возраст по специальностям.
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
# 📌 Проверь себя: ушло 80 строк, осталось 3500

# 3
v["visit_date"] = pd.to_datetime(v["visit_date"], format="mixed", dayfirst=True)
# альтернатива — два прохода с явными форматами:
# p1 = pd.to_datetime(v["visit_date"], format="%d.%m.%Y", errors="coerce")
# p2 = pd.to_datetime(v["visit_date"], format="%Y-%m-%d", errors="coerce")
# v["visit_date"] = p1.fillna(p2)
v["visit_date"].min(), v["visit_date"].max()   # sanity-check диапазона
# 📌 Проверь себя: даты с 2026-01-01 по 2026-05-30

# 4
v["doctor_specialty"].value_counts().head(10)
v["doctor_specialty"] = (v["doctor_specialty"].str.strip().str.lower()
                          .str.replace("t", "т", regex=False))  # латинская t в «tерапевт»
v["doctor_specialty"].value_counts().head(10)
# 📌 Проверь себя: 16 «специальностей» → 5; терапевт 1402

# 5
mask_bad = (v["patient_age"] < 1) | (v["patient_age"] > 110)
mask_bad.sum()
v.loc[mask_bad, "patient_age"] = None
v.groupby("doctor_specialty")["patient_age"].median()
# 📌 Проверь себя: заменено 65 значений; медианы по специальностям 45–47 лет

# 6
v["bmi"] = v["weight_kg"] / (v["height_cm"] / 100) ** 2
v["bmi"].isna().sum()   # пропуск роста ИЛИ веса → NaN в BMI
# 📌 Проверь себя: 1066 приёмов без BMI

# 7
v[v["visit_price"] > 0].groupby("clinic")["visit_price"].mean()
# 📌 Проверь себя: Юг ≈ 2783, Север ≈ 2774, Центр ≈ 2740

# 8
(v.assign(oms=v["visit_price"] == 0)
  .groupby("clinic")["oms"].mean())
# 📌 Проверь себя: максимум у Севера ≈ 36.9%

# 9
cnt = v.groupby("patient_id")["visit_id"].count()
frequent = cnt[cnt >= 3].index
v[v["patient_id"].isin(frequent)]["doctor_specialty"].value_counts().head(1)
# 📌 Проверь себя: 658 пациентов, самая частая специальность — терапевт

# 10
v.to_csv("visits_clean.csv", index=False)
```

</details>

> ⚠️ **Ловушка `format="mixed"`:** без `dayfirst=True` pandas трактует «09.02.2026» как 2 сентября, а не 9 февраля — для любой даты с днём ≤ 12. Исключения не будет: в этом датасете 409 из 1059 дат формата dd.mm.yyyy **молча** уехали бы не в тот месяц, и вся динамика по месяцам стала бы выдумкой. Поэтому после любой конвертации дат — sanity-check: min/max и распределение по месяцам. Любимый вопрос на собеседованиях про «грязные» даты.

➡️ Дальше: [3.7 Маркетинг](3_7_dataset_marketing.md)
