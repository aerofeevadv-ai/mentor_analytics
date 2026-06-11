# B3. Работа с колонками

Переименование, типы, замены, частоты, применение функций. Группа, где чаще всего чинят «грязные» данные.

**SQL-аналог группы:** `AS`, `CAST`, `CASE WHEN`, `GROUP BY + COUNT`.

---

## rename() — переименование колонок

**Что делает:** меняет имена колонок по словарю «старое → новое».

```python
df = df.rename(columns={"name": "user_name", "age": "user_age"})
```

**SQL:** `SELECT name AS user_name`

**Чуть сложнее:** привести все имена к нижнему регистру после кривой выгрузки:

```python
df.columns = df.columns.str.lower().str.strip()
```

**Подводный камень:** rename возвращает копию, оригинал не меняется. Забыл `df = ...` — переименования «не произошло».

---

## astype() — приведение типов

**Что делает:** меняет тип колонки.

```python
df["age"] = df["age"].astype(int)
df["user_id"] = df["user_id"].astype(str)
```

**SQL:** `CAST(age AS INT)`

**Чуть сложнее:** числа с грязью (пробелы, пустые строки) сначала чистят, потом приводят:

```python
df["price"] = pd.to_numeric(df["price"], errors="coerce")   # что не число → NaN
```

**Подводные камни:**

- astype(int) падает, если в колонке есть NaN — сначала обработай пропуски
- даты приводи не astype, а `pd.to_datetime(df["dt"])`

---

## Даты: pd.to_datetime + аксессор .dt

**Что делает:** `pd.to_datetime()` преобразует строку в тип datetime, после чего через `.dt` доступны год, месяц, день, день недели и т. д.

```python
df["signup_date"] = pd.to_datetime(df["signup_date"])

df["signup_date"].dt.year        # год
df["signup_date"].dt.month       # номер месяца
df["signup_date"].dt.date        # только дата (без времени)
df["signup_date"].dt.dayofweek   # день недели: 0 = понедельник

# группировка по месяцу регистрации
df.groupby(df["signup_date"].dt.to_period("M")).size()
```

**SQL:** `EXTRACT(YEAR FROM signup_date)`, `DATE_TRUNC('month', signup_date)`

📌 **Форвард-ссылка:** полная практика с датами — в [модуле 3 (логистика)](../module_3/00_index.md), здесь только база.

---

## replace() — замена значений

**Что делает:** заменяет значения по словарю.

```python
df["city"] = df["city"].replace({"Мск": "Moscow", "Питер": "SPB"})
```

**SQL:** `CASE WHEN city = 'Мск' THEN 'Moscow' ...`

**Когда используется:** унификация категорий после ручного ввода, исправление опечаток в данных.

---

## value_counts() — частоты значений

**Что делает:** считает, сколько раз встречается каждое значение. Один из самых используемых методов вообще.

```python
df["segment"].value_counts()
# new       256
# active    189
# vip        73
```

**SQL:** `SELECT segment, COUNT(*) FROM t GROUP BY segment ORDER BY 2 DESC`

**Чуть сложнее:**

```python
df["segment"].value_counts(normalize=True)   # доли вместо счётчиков
df["city"].value_counts(dropna=False)        # показать и NaN
```

> ⚠️ **Подводный камень:** по умолчанию value_counts ПРЯЧЕТ пропуски. Колонка может быть наполовину пустой, а распределение выглядит красиво. Диагностируешь данные — всегда `dropna=False`.

---

## apply() — функция к колонке

**Что делает:** применяет твою функцию к каждому значению.

```python
def normalize_price(price):
    if price < 0:
        return 0
    return round(price, 2)

df["price_clean"] = df["price"].apply(normalize_price)
```

**Чуть сложнее:** с lambda для коротких преобразований:

```python
df["age_group"] = df["age"].apply(lambda x: "35+" if x >= 35 else ("18-35" if x >= 18 else "18-"))
```

**SQL:** `CASE WHEN age >= 35 THEN '35+' WHEN age >= 18 THEN '18-35' ELSE '18-' END`

**Подводный камень:** apply — это скрытый цикл, он медленный. Если существует векторный способ (арифметика, str-методы, replace) — используй его. apply — когда логика действительно нестандартная.

---

## map() — маппинг по словарю

**Что делает:** заменяет значения Series по словарю или функции.

```python
# Маппинг город → код региона (справочник региональных кодов)
city_to_region = {"Moscow": 77, "SPB": 78, "Kazan": 16, "Novosibirsk": 54, "Ekaterinburg": 66}
df["region_code"] = df["city"].map(city_to_region)
```

**SQL:** JOIN со справочником в миниатюре.

**Подводный камень:** значения, которых нет в словаре, станут NaN (replace в той же ситуации оставил бы оригинал). В `data.csv` в `city` есть «грязные» варианты (`MOSCOW`, `moscow`, ` Moscow`) — они не попадут в маппинг и станут NaN. Это и фича, и ловушка: NaN-ы видно явно, а не спрятаны под «неправильными» значениями.

---

## 🧠 Как этим пользуется профи

Получил новую таблицу → `value_counts(dropna=False)` по ключевым категориям → починил типы astype/to_numeric → конвертировал даты pd.to_datetime → унифицировал категории replace/map. Только потом метрики.

🎯 **Практика:** в `data.csv`: 1) приведи имена колонок к нижнему регистру; 2) посчитай распределение городов с долями и с учётом NaN — обрати внимание на «грязные» варианты (`MOSCOW`, ` Moscow` и т. д.); 3) создай колонку `age_group` («18−», «18–35», «35+») через apply с lambda; 4) создай колонку `region_code`, смапив `city` на коды регионов через словарь — посмотри, сколько строк получили NaN и почему; 5) конвертируй `signup_date` в datetime и выведи месяц регистрации.

<details>
<summary>✅ Решение</summary>

```python
import pandas as pd
df = pd.read_csv("data.csv")

# 1. Нижний регистр колонок
df.columns = df.columns.str.lower().str.strip()

# 2. Распределение городов с NaN и долями
df["city"].value_counts(dropna=False)
df["city"].value_counts(normalize=True, dropna=False)

# 3. age_group через apply
df["age_group"] = df["age"].apply(
    lambda x: "35+" if x >= 35 else ("18-35" if x >= 18 else "18-")
    if pd.notna(x) else None
)

# 4. region_code через map
city_to_region = {"Moscow": 77, "SPB": 78, "Kazan": 16, "Novosibirsk": 54, "Ekaterinburg": 66}
df["region_code"] = df["city"].map(city_to_region)
# NaN — «грязные» варианты (MOSCOW, moscow, KAZAN...) + изначальные пропуски в city
print("NaN в region_code:", df["region_code"].isna().sum())

# 5. Даты
df["signup_date"] = pd.to_datetime(df["signup_date"])
df["signup_month"] = df["signup_date"].dt.month
```

</details>

➡️ Дальше: [B4. Группировки и агрегации](2_m04_groupby.md)
