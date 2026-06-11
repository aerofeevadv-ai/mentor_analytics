# B4. Группировки и агрегации

Главный инструмент аналитики: метрики в разрезах. Если из всего модуля останется одна группа методов — пусть будет эта.

**SQL-аналог группы:** `GROUP BY`, агрегатные функции, `COUNT(DISTINCT)`.

---

## groupby() — группировка

**Что делает:** разбивает таблицу на группы по значениям колонки и применяет агрегацию к каждой группе.

```python
df.groupby("segment")["salary"].mean()
# segment
# active    81282.0
# new       74500.0
# vip       72664.0
```

**SQL:** `SELECT segment, AVG(salary) FROM t GROUP BY segment`

Читается так же, как SQL, только наоборот: сгруппируй по segment → возьми колонку salary → посчитай среднее.

**Чуть сложнее:** группировка по нескольким колонкам:

```python
df.groupby(["city", "segment"])["salary"].mean()
df.groupby(["city", "segment"], as_index=False)["salary"].mean()   # результат — плоская таблица
```

**Подводные камни:**

- groupby по умолчанию делает группирующие колонки индексом результата. Хочешь обычную таблицу — `as_index=False` или `.reset_index()`
- **groupby молча выбрасывает строки с NaN в ключе группировки.** В `data.csv` в `city` 21 пропуск — эти строки исчезнут из любого groupby по city, и суммы «не сойдутся»

---

## Агрегатные функции

```python
df.groupby("segment")["salary"].mean()       # среднее
df.groupby("segment")["salary"].median()     # медиана
df.groupby("segment")["salary"].sum()        # сумма
df.groupby("segment")["salary"].count()      # количество непустых
df.groupby("segment")["user_id"].nunique()   # уникальные — COUNT(DISTINCT)
df.groupby("segment")["salary"].min()        # минимум
df.groupby("segment")["salary"].max()        # максимум
```

> ⚠️ **Подводный камень:** `count()` считает непустые значения, `size()` — все строки группы. На колонке с пропусками результаты разные. На собеседовании любят спросить разницу.

---

## agg() — несколько агрегаций сразу

**Что делает:** считает несколько метрик за один проход.

```python
df.groupby("segment")["salary"].agg(["mean", "median", "count"])
```

**Чуть сложнее:** разные агрегации к разным колонкам, с именами результатов:

```python
df.groupby("segment").agg(
    avg_salary=("salary", "mean"),
    users=("user_id", "nunique"),
    total_rows=("user_id", "count")
)
```

**SQL:** `SELECT segment, AVG(salary) AS avg_salary, COUNT(DISTINCT user_id) AS users ... GROUP BY segment`

Этот синтаксис (named aggregation) — самый читаемый, используй его по умолчанию.

---

## pivot_table() — сводная таблица

**Что делает:** таблица «строки × колонки × агрегат» — как сводная в Excel.

```python
df.pivot_table(
    index="city",        # строки
    columns="segment",   # колонки
    values="salary",     # что агрегируем
    aggfunc="mean"       # как
)
```

**SQL-аналог:** прямого аналога нет — это `GROUP BY city, segment`, развёрнутый по двум осям. В SQL пришлось бы писать `CASE WHEN segment = 'vip' THEN salary END` для каждого сегмента.

**Когда используется:** метрика в двух разрезах одновременно; когортные таблицы (увидишь в модуле 3 на retention).

**Подводный камень:** дефолтный aggfunc — mean. Хотел суммы, забыл указать — получил средние без единого предупреждения.

---

## transform() — агрегат без схлопывания строк

**Что делает:** как groupby + агрегат, но результат «размазывается» обратно по строкам оригинального DataFrame. Число строк остаётся прежним.

```python
df["avg_salary_by_segment"] = df.groupby("segment")["salary"].transform("mean")
df["share_in_group"] = df["salary"] / df.groupby("segment")["salary"].transform("sum")
```

**SQL-аналог:** `AVG(salary) OVER (PARTITION BY segment)` — оконная функция.

**Когда используется:** сравнить каждого пользователя со средним по его группе; посчитать долю от итога по группе; нормализация внутри сегмента.

---

## shift() / diff() внутри групп — LAG и прирост

**Что делает:** `shift(1)` сдвигает значения вниз (предыдущее), `diff()` считает разность текущего и предыдущего. Внутри groupby — LAG по каждой группе отдельно.

```python
# «предыдущая дата регистрации» по сегменту
df_s = df.sort_values("signup_date")
df_s["prev_signup_in_segment"] = df_s.groupby("segment")["signup_date"].shift(1)
```

**SQL-аналог:** `LAG(signup_date) OVER (PARTITION BY segment ORDER BY signup_date)`

**Когда используется:** временные ряды, вычисление интервалов между событиями, прирост метрики от периода к периоду.

---

## idxmax() / nlargest() — быстрый топ

```python
# индекс строки с максимальной зарплатой по сегменту
idx = df.groupby("segment")["salary"].idxmax()
df.loc[idx, ["segment", "name", "salary"]]   # сами строки

# топ-3 строки по зарплате в целом
df.nlargest(3, "salary")
```

**SQL:** `SELECT ... ORDER BY salary DESC LIMIT 3`

---

## Топ-N внутри группы

```python
# топ-2 пользователя по зарплате в каждом сегменте
top2 = (
    df.dropna(subset=["salary"])
    .sort_values("salary", ascending=False)
    .groupby("segment")
    .head(2)
)
```

**SQL:** `ROW_NUMBER() OVER (PARTITION BY segment ORDER BY salary DESC) <= 2`

---

## 🧠 Как этим пользуется профи

Один разрез, одна метрика → groupby + агрегат. Несколько метрик → agg с именами. Два разреза → pivot_table. Нужно сравнить строку с группой — transform. Временной ряд по группам — shift/diff. После любого groupby — head() на результат: проверить, что размер и значения осмысленны.

🎯 **Практика:** в `data.csv`: 1) средняя и медианная зарплата по сегментам одной таблицей; 2) число уникальных пользователей по городу и сегменту через pivot_table; 3) добавь колонку с долей зарплаты каждого пользователя от средней по его сегменту (transform); 4) объясни словами, почему `count()` по salary меньше, чем `size()`, и куда делись строки с пропуском в city при groupby по city.

<details>
<summary>✅ Решение</summary>

```python
import pandas as pd
df = pd.read_csv("data.csv")

# 1. средняя и медианная зарплата по сегментам
df.groupby("segment")["salary"].agg(["mean", "median"])

# 2. pivot_table: уникальные пользователи по city × segment
df.pivot_table(
    index="city", columns="segment",
    values="user_id", aggfunc="nunique"
)

# 3. transform: доля зарплаты от средней по сегменту
df["salary_vs_avg"] = df["salary"] / df.groupby("segment")["salary"].transform("mean")

# 4. count() vs size() + пропуски в city
# count() считает непустые salary — где NaN, строка не считается
# При groupby("city"): 21 строка с NaN в city молча выпадает из результата
# Сумма size() по группам < len(df) именно на эти 21 строку
print(df.groupby("segment")["salary"].count())   # непустые
print(df.groupby("segment")["salary"].size())    # все строки группы
```

</details>

➡️ Дальше: [B5. Объединение таблиц](2_m05_merge.md)
