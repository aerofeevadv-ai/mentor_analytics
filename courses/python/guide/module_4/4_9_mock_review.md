# 4.9 Разбор мок-собеседований

Решения и чек-лист самооценки для [мок 1](4_7_mock_1.md) и [мок 2](4_8_mock_2.md).

---

## Мок 1 — разбор

### Задача 1. Дашборд по городам

<details>
<summary>✅ Решение</summary>

```python
result = (
    orders.groupby("city")
          .agg(
              orders_cnt=("order_id", "count"),
              buyers=("user_id", "nunique"),
              total_revenue=("amount", "sum"),
              avg_check=("amount", "mean")
          )
          .reset_index()
          .sort_values("total_revenue", ascending=False)
)
print(result)
```

**Вывод:**
```
     city  orders_cnt  buyers  total_revenue  avg_check
1  Moscow           3       2          23700     7900.0
2     SPB           2       2           5500     2750.0
0   Kazan           1       1            500      500.0
```

**Ключевые моменты:**
- `.agg` со словарём именованных агрегаций — не отдельные groupby для каждой метрики
- `nunique` для уникальных покупателей, не `count`
- `reset_index()` перед `sort_values`

</details>

---

### Задача 2. Обогащение сегментом — с ловушкой

<details>
<summary>✅ Решение</summary>

```python
# Диагностика
print("Дублей в users:", users["user_id"].duplicated().sum())  # 1!

# Чистка
users_clean = users.drop_duplicates(subset=["user_id"])

# Merge с валидацией
result = orders.merge(users_clean, on="user_id", how="left", validate="m:1")
print("Строк:", len(result))  # 4 — не размножились
print(result)
```

**Вывод:**
```
Дублей в users: 1
Строк: 4
   order_id  user_id  amount  segment
0         1       10     500      vip
1         2       20    1200  regular
2         3       10     800      vip
3         4       30     300      new
```

**Ключевые моменты:**
- Всегда проверять `duplicated()` перед merge
- `validate="m:1"` упадёт с ошибкой если справа есть дубли — страховка
- `how="left"` защищает от потери строк слева, но не от размножения

</details>

---

### Задача 3. Доля канала в бюджете

<details>
<summary>✅ Решение</summary>

```python
df["channel_total"] = df.groupby("channel")["spend"].transform("sum")
df["share_pct"]     = (df["spend"] / df["channel_total"] * 100).round(1)
print(df)
```

**Вывод:**
```
   channel  campaign_id  spend  channel_total  share_pct
0    email            1  50000          80000       62.5
1    email            2  30000          80000       37.5
2   social            3  80000         100000       80.0
3   social            4  20000         100000       20.0
4  context            5  40000          40000      100.0
```

**Ключевые моменты:**
- `transform("sum")` возвращает серию той же длины — не нужен merge обратно
- SQL-аналог: `SUM(spend) OVER (PARTITION BY channel)`

</details>

---

### Задача 4. Динамика по месяцам

<details>
<summary>✅ Решение</summary>

```python
df_2026 = df[df["event_date"].dt.year == 2026].copy()
df_2026["month"] = df_2026["event_date"].dt.to_period("M")

monthly = (
    df_2026.groupby("month")
           .agg(
               users=("user_id", "nunique"),
               revenue=("revenue", "sum")
           )
           .reset_index()
)
print("Строк после фильтра:", len(df_2026))  # 5 (2025-12-30 выброшена)
print(monthly)
```

**Вывод:**
```
Строк после фильтра: 5
     month  users  revenue
0  2026-01      2     2500
1  2026-02      2     2500
2  2026-03      1      800
```

**Ключевые моменты:**
- `.dt.year` для фильтра по году
- `to_period("M")` — не `dt.month`, иначе разные годы сольются

</details>

---

## Мок 2 — разбор

### Задача 1. Чистка и нормализация

<details>
<summary>✅ Решение</summary>

```python
df = df.dropna(subset=["name"])
df["name_clean"] = df["name"].str.strip().str.title()
df["category"]   = df["category_raw"].str.lower()
df["price"]      = df["price"].fillna(df["price"].median())

print(df[["product_id", "name_clean", "category", "price"]])
```

**Вывод:**
```
   product_id   name_clean     category    price
0           1   Laptop Pro  electronics  75000.0
1           2      Phone X  electronics  45000.0
3           4  Tablet Mini      tablets  25000.0
4           5   Laptop Air  electronics  85000.0
```

**Ключевые моменты:**
- `dropna(subset=["name"])` — только по критичной колонке
- `str.title()` — каждое слово с заглавной, осторожно с аббревиатурами
- `fillna(median)` считается до drop, если нужно заполнять после drop — пересчитать

</details>

---

### Задача 2. Время между заказами

<details>
<summary>✅ Решение</summary>

```python
df = df.sort_values(["user_id", "order_date"])
df["prev_date"]       = df.groupby("user_id")["order_date"].shift(1)
df["days_since_prev"] = (df["order_date"] - df["prev_date"]).dt.days
print(df)
```

**Вывод:**
```
   user_id order_date  amount  prev_date  days_since_prev
0        1 2026-01-01     500        NaT              NaN
1        1 2026-01-15     800 2026-01-01             14.0
2        1 2026-02-10    1200 2026-01-15             26.0
3        2 2026-01-08     300        NaT              NaN
4        2 2026-02-20     600 2026-01-08             43.0
```

**Ключевые моменты:**
- Сортировка обязательна перед `shift`
- `shift(1)` внутри `groupby` — смещение по группе, не по всему DataFrame
- NaN для первого заказа — корректное поведение, не ошибка

</details>

---

### Задача 3. SQL → pandas (ROAS)

<details>
<summary>✅ Решение</summary>

```python
result = (
    campaigns.groupby("channel")
             .agg(total_spend=("spend", "sum"),
                  total_rev=("revenue", "sum"))
             .reset_index()
)
result["roas"] = (result["total_rev"] / result["total_spend"]).round(2)
result = result.sort_values("roas", ascending=False)
print(result)
```

**Вывод:**
```
   channel  total_spend  total_rev  roas
1    email        25000     110000   4.4
0  context        25000      90000   3.6
2   social        50000     120000   2.4
```

**Ключевые моменты:**
- ROAS считается от сумм, не как среднее строковых значений
- `SUM(revenue)/SUM(spend)` — агрегация сначала, потом деление

</details>

---

### Задача 4. Номер заказа и первые покупки

<details>
<summary>✅ Решение</summary>

```python
df = df.sort_values(["user_id", "order_date"])
df["order_num"] = df.groupby("user_id").cumcount() + 1

first_orders = df[df["order_num"] == 1].copy()
print("Все заказы с нумерацией:")
print(df)
print("\nТолько первые заказы:")
print(first_orders[["order_id", "user_id", "order_date", "amount"]])
```

**Вывод:**
```
Все заказы с нумерацией:
   order_id  user_id order_date  amount  order_num
0       101        1 2026-01-05     500          1
2       103        1 2026-01-20     800          2
3       104        1 2026-02-10     400          3
1       102        2 2026-01-10    1200          1
4       105        2 2026-02-01     600          2
3       104        3 2026-01-15     300          1

Только первые заказы:
   order_id  user_id order_date  amount
0       101        1 2026-01-05     500
1       102        2 2026-01-10    1200
3       104        3 2026-01-15     300
```

**Ключевые моменты:**
- `cumcount() + 1` — cumcount стартует с 0
- Сортировать до cumcount, иначе нумерация произвольная

</details>

---

### Задача 5. Что выведет код (срез)

<details>
<summary>✅ Ответ и разбор</summary>

```python
a = [1, 2, 3]
b = a[:]
b.append(4)
print(a)   # [1, 2, 3]
print(b)   # [1, 2, 3, 4]
```

`a[:]` создаёт новый список (поверхностная копия). `b` и `a` — разные объекты. Изменение `b` не затрагивает `a`.

Контраст: `b = a` — оба указывают на один объект, любое изменение видят оба.

</details>

---

## Чек-лист самооценки

Пройди честно — не «мог бы», а «сделал».

### Правильность

- [ ] Мок 1: все 4 задачи дали корректный результат
- [ ] Мок 2: все 5 задач дали корректный результат
- [ ] Задача 2 мок 1: обнаружил и устранил дубли перед merge
- [ ] Задача 5 мок 2: объяснил разницу `b = a` и `b = a[:]`

### Ход мысли вслух

- [ ] Проговаривал план перед кодом («сначала проверю дубли, потом...»)
- [ ] Комментировал каждый шаг по ходу
- [ ] Когда застрял — сказал вслух «вижу два пути» или «не уверен, попробую так»

### Проверка результата

- [ ] Проверял `shape` или `head()` после каждого merge
- [ ] После фильтрации убеждался что осталось осмысленное число строк
- [ ] Цифры выглядят реалистично (не 0, не миллионы там где ожидались тысячи)

### Качество кода

- [ ] Нет chained assignment (`df[mask]["col"] = ...`)
- [ ] Нет `apply` там, где хватает векторной операции
- [ ] Понятные имена переменных

---

## Пороговые баллы

Подсчитай галочки:

| Раздел | Галочек | Оценка |
|---|---|---|
| Правильность | 4/4 | Все задачи решены верно |
| Ход мысли вслух | 3/3 | Коммуникация на уровне |
| Проверка результата | 3/3 | Нет слепых операций |
| Качество кода | 4/4 | Чистый pandas |

**14/14** — готов к реальному собеседованию. Можно идти.

**10–13** — хорошо, но есть точки роста. Повтори [tricky-задачи](4_2_tricky_pandas.md) по пропущенным пунктам и прогони мок ещё раз.

**Меньше 10** — ещё тренироваться. Пройди блоки [4.3](4_3_company_tasks.md) заново с таймером, потом вернись к моку.
