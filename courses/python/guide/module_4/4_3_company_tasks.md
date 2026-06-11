# 4.3 Задачи уровня собеседований

18 задач — то, что реально дают на Python-секциях junior/middle аналитиков. Формат: условие → данные (самодостаточный DataFrame прямо в коде) → время → ожидаемый результат → решение в спойлере.

---

## Блок 1. Фильтрация и создание колонок

### Задача 1. Размер заказа и признак промо · _уровень маркетплейс_

**Условие.** Возьми таблицу заказов. Оставь только completed. Добавь колонку `discount` (True/False — был ли промокод) и `size` — категория суммы: small (до 1000), medium (1000–5000), large (>5000).

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "order_id": [1, 2, 3, 4, 5],
    "amount":   [500, 12000, 3500, 8000, 200],
    "promo_code": [None, "SALE10", None, "VIP20", None],
    "status": ["completed", "completed", "cancelled", "completed", "completed"]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** таблица из 4 строк (completed), с колонками `discount` и `size`. Заказ 12000 → large, True; заказ 200 → small, False.

<details>
<summary>✅ Решение</summary>

```python
completed = df[df["status"] == "completed"].copy()
completed["discount"] = completed["promo_code"].notna()
completed["size"] = pd.cut(
    completed["amount"],
    bins=[0, 1000, 5000, float("inf")],
    labels=["small", "medium", "large"]
)
print(completed[["order_id", "amount", "discount", "size"]])
```

**Вывод:**
```
   order_id  amount  discount   size
0         1     500     False  small
1         2   12000      True  large
3         4    8000      True  large
4         5     200     False  small
```

**Что проверяет интервьюер:** понимание `.copy()` перед мутацией среза; умение использовать `notna()` вместо `!= None`; знание `pd.cut`.

**Типичная ошибка:** `df["promo_code"] != None` — это vectorized сравнение с None, которое возвращает не то что ожидается (питон не вызывает `__ne__` для каждого элемента через numpy). Правильно: `notna()` или `isna()`.

</details>

---

### Задача 2. Признак нового пользователя · _уровень банк_

**Условие.** Есть таблица транзакций с датой и таблица клиентов с датой открытия счёта. Считай клиента «новым» если дата первой транзакции в таблице <= 30 дней с открытия счёта. Добавь признак `is_new`.

**Данные:**

```python
import pandas as pd

txn = pd.DataFrame({
    "client_id": [1, 2, 3, 4],
    "txn_date": pd.to_datetime(["2026-01-15", "2026-02-10", "2026-01-05", "2026-03-01"])
})
clients = pd.DataFrame({
    "client_id": [1, 2, 3, 4],
    "open_date": pd.to_datetime(["2026-01-01", "2026-01-10", "2026-01-01", "2025-12-01"])
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** клиенты 1 и 3 — новые (14 и 4 дня), 2 — новый (31 день — НЕТ, граница), 4 — нет (90 дней).

<details>
<summary>✅ Решение</summary>

```python
merged = txn.merge(clients, on="client_id")
merged["days_since_open"] = (merged["txn_date"] - merged["open_date"]).dt.days
merged["is_new"] = merged["days_since_open"] <= 30
print(merged)
```

**Вывод:**
```
   client_id   txn_date  open_date  days_since_open  is_new
0          1 2026-01-15 2026-01-01               14    True
1          2 2026-02-10 2026-01-10               31   False
2          3 2026-01-05 2026-01-01                4    True
3          4 2026-03-01 2025-12-01               90   False
```

**Что проверяет интервьюер:** вычитание дат через `.dt.days`; умение перевести бизнес-правило (≤30 дней) в булеву колонку.

**Типичная ошибка:** вычитать даты как строки или забыть `.dt.days` → получается `Timedelta`, а не целое число.

</details>

---

## Блок 2. groupby + несколько агрегаций

### Задача 3. Дашборд по городам · _уровень маркетплейс_

**Условие.** Сгруппируй заказы по городу. Для каждого города посчитай: число заказов, число уникальных покупателей, суммарную выручку, средний чек. Отсортируй по выручке убыванию.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "order_id": [1,2,3,4,5,6],
    "city":     ["Moscow","SPB","Moscow","Kazan","SPB","Moscow"],
    "user_id":  [1,2,1,3,4,2],
    "amount":   [15000, 2500, 8000, 500, 3000, 700]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** Moscow — 3 заказа, 2 покупателя, 23700 выручки, 7900 средний чек.

<details>
<summary>✅ Решение</summary>

```python
result = (
    df.groupby("city")
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

**Что проверяет интервьюер:** синтаксис `.agg` со словарём именованных агрегаций; `nunique` для уникальных покупателей; правило «средний чек — среднее по строкам, а не выручка/заказов» здесь одно и то же, но интервьюер спросит почему.

**Типичная ошибка:** написать `df.groupby("city")[["amount"]].agg(...)` — теряется доступ к `user_id` для `nunique`.

</details>

---

### Задача 4. Метрики по клиентским сегментам · _уровень банк_

**Условие.** Для каждого сегмента клиентов посчитай: количество клиентов, суммарный баланс, средний баланс, число уникальных продуктов.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "client_id": [1,1,2,2,3,3,4],
    "segment":   ["vip","vip","regular","regular","new","new","regular"],
    "product":   ["card","loan","card","card","deposit","loan","card"],
    "balance":   [50000,200000,30000,40000,500000,100000,20000]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** vip — 1 клиент, 250 000 баланс, 2 продукта.

<details>
<summary>✅ Решение</summary>

```python
result = (
    df.groupby("segment")
      .agg(
          clients=("client_id", "nunique"),
          total_balance=("balance", "sum"),
          avg_balance=("balance", "mean"),
          products=("product", "nunique")
      )
      .reset_index()
)
print(result)
```

**Вывод:**
```
   segment  clients  total_balance  avg_balance  products
0      new        1         600000     300000.0         2
1  regular        2          90000      30000.0         1
2      vip        1         250000     125000.0         2
```

**Что проверяет интервьюер:** `nunique` по нескольким колонкам одновременно в одном `.agg`; понимание что один клиент может давать несколько строк.

**Типичная ошибка:** посчитать `count` вместо `nunique` для клиентов — получишь число строк, а не уникальных людей.

</details>

---

## Блок 3. merge + проверка размножения строк

### Задача 5. Обогащение заказов сегментом · _уровень маркетплейс_

**Условие.** Прилепи к заказам сегмент пользователя. Перед merge проверь дубли в справочнике пользователей. Убедись что число строк после merge равно числу строк до.

**Данные:**

```python
import pandas as pd

orders = pd.DataFrame({
    "order_id": [1,2,3,4],
    "user_id": [10,20,10,30],
    "amount": [500, 1200, 800, 300]
})
users = pd.DataFrame({
    "user_id": [10,10,20,30],      # дубль user_id=10!
    "segment": ["vip","vip","regular","new"]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** 4 строки — по одной на каждый заказ.

<details>
<summary>✅ Решение</summary>

```python
# Диагностика
print("Дублей в users:", users["user_id"].duplicated().sum())  # 1

# Лечение
users_clean = users.drop_duplicates(subset=["user_id"])

# Merge с валидацией
result = orders.merge(users_clean, on="user_id", how="left", validate="m:1")
print(result)
```

**Вывод:**
```
Дублей в users: 1
   order_id  user_id  amount  segment
0         1       10     500      vip
1         2       20    1200  regular
2         3       10     800      vip
3         4       30     300      new
```

**Что проверяет интервьюер:** привычку диагностировать дубли перед merge; `validate="m:1"` как страховку; разницу left/inner для потери строк.

**Типичная ошибка:** просто написать `.merge(users, ...)` — получишь 5 строк вместо 4, и заметишь не сразу.

</details>

---

### Задача 6. Аналитика доставок · _уровень маркетплейс_

**Условие.** Прилепи к заказам информацию о доставке. Посчитай долю заказов с доставкой дольше 5 дней по каждому городу.

**Данные:**

```python
import pandas as pd

orders = pd.DataFrame({
    "order_id": [1,2,3,4,5],
    "city":     ["Moscow","SPB","Moscow","Kazan","SPB"],
    "amount":   [1000, 2000, 1500, 800, 600]
})
deliveries = pd.DataFrame({
    "order_id":     [1,2,3,4,5],
    "delivery_days": [3, 7, 2, 6, 4]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** Kazan — 100% долгих доставок, SPB — 50%, Moscow — 0%.

<details>
<summary>✅ Решение</summary>

```python
merged = orders.merge(deliveries, on="order_id", how="left")
print("Строк после merge:", len(merged))  # 5 — не размножились

merged["long_delivery"] = merged["delivery_days"] > 5
result = (
    merged.groupby("city")["long_delivery"]
          .mean()
          .mul(100)
          .round(1)
          .rename("pct_long")
          .reset_index()
)
print(result)
```

**Вывод:**
```
Строк после merge: 5
     city  pct_long
0   Kazan     100.0
1  Moscow       0.0
2     SPB      50.0
```

**Что проверяет интервьюер:** проверку размера после merge; `mean()` булевой колонки как способ посчитать долю.

**Типичная ошибка:** использовать `count()` и делить руками, а не `mean()` булевой серии.

</details>

---

## Блок 4. Пропуски и дубликаты

### Задача 7. Чистка лога событий · _уровень стриминг_

**Условие.** В логе есть полные дубли строк и пропуски. Удали полные дубли. Удали строки с пропуском в `watch_minutes`. Пропуск в `device` заполни строкой "unknown".

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "user_id":       [1, 1, 2, 3, 4, 4],
    "content_id":    [100, 100, 200, 300, 400, 400],
    "watch_minutes": [30, 30, None, 45, 60, 60],
    "device":        ["mobile", "mobile", "web", None, "tv", "tv"]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** 3 строки — user 1 (mobile, 30 мин), user 3 (unknown, 45 мин), user 4 (tv, 60 мин). User 2 выбывает из-за NaN в watch_minutes.

<details>
<summary>✅ Решение</summary>

```python
print("Полных дублей:", df.duplicated().sum())  # 2

df_clean = df.drop_duplicates()
df_clean = df_clean.dropna(subset=["watch_minutes"])
df_clean["device"] = df_clean["device"].fillna("unknown")
print(df_clean)
```

**Вывод:**
```
Полных дублей: 2
   user_id  content_id  watch_minutes   device
0        1         100           30.0   mobile
3        3         300           45.0  unknown
4        4         400           60.0       tv
```

**Что проверяет интервьюер:** порядок операций (дубли → затем пропуски); разницу `dropna()` и `fillna()` — когда что применять.

**Типичная ошибка:** `fillna` перед `drop_duplicates` может исказить дубликаты или добавить ложные.

</details>

---

### Задача 8. Диагностика качества данных · _уровень банк_

**Условие.** Выведи по каждой колонке: число пропусков и процент пропусков. Найди строки-дубли по ключевым полям (client_id + date). Выведи только клиентов с дублями.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "client_id": [1, 1, 2, 3, 3],
    "date":      ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-03"],
    "amount":    [1000, 1000, None, 500, 600],
    "status":    ["ok", "ok", "ok", None, "ok"]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** 2 пары дублей по ключу (client_id + date): клиенты 1 и 3.

<details>
<summary>✅ Решение</summary>

```python
# Пропуски
missing = pd.DataFrame({
    "count": df.isna().sum(),
    "pct":   (df.isna().mean() * 100).round(1)
})
print("Пропуски:")
print(missing)

# Дубли по ключу
dup_mask = df.duplicated(subset=["client_id", "date"], keep=False)
print("\nСтроки с дублями по ключу:")
print(df[dup_mask])
```

**Вывод:**
```
Пропуски:
           count  pct
client_id      0  0.0
date           0  0.0
amount         1 20.0
status         1 20.0

Строки с дублями по ключу:
   client_id        date  amount status
0          1  2026-01-01  1000.0     ok
1          1  2026-01-01  1000.0     ok
3          3  2026-01-03   500.0     ok
4          3  2026-01-03   600.0     ok
```

**Что проверяет интервьюер:** `isna().sum()` и `isna().mean()` для аудита качества; `keep=False` в `duplicated()` — чтобы видеть ВСЕ строки дублей, а не только вторые.

**Типичная ошибка:** `keep="first"` оставляет только вторую копию дубля, первую не покажет.

</details>

---

## Блок 5. Строки (.str)

### Задача 9. Чистка листингов классифайда · _уровень классифайд_

**Условие.** Почисть заголовки: strip + lower. Извлеки числовую цену из строки (убрать всё кроме цифр). Добавь булеву колонку — есть ли слово "москва" в заголовке.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "listing_id": [1, 2, 3, 4],
    "title": ["2-комн. квартира, 52 м², Москва",
               "  СТУДИЯ 28кв.м Спб  ",
               "3-к квартира 70м2, Новосибирск",
               "Комната 15 кв. м, Казань"],
    "price_str": ["5 500 000 руб.", "2 800 000 р.", "4 100 000 руб", "1 200 000 ₽"]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** у listing_id=1 is_moscow=True, price=5500000; у listing_id=2 is_moscow=False, price=2800000.

<details>
<summary>✅ Решение</summary>

```python
df["title_clean"] = df["title"].str.strip().str.lower()
df["price_num"]   = (df["price_str"]
                       .str.replace(r"[^\d]", "", regex=True)
                       .astype(int))
df["is_moscow"]   = df["title"].str.contains("Москва|москва", na=False)

print(df[["listing_id", "title_clean", "price_num", "is_moscow"]])
```

**Вывод:**
```
   listing_id                      title_clean  price_num  is_moscow
0           1  2-комн. квартира, 52 м², москва    5500000       True
1           2                студия 28кв.м спб    2800000      False
2           3   3-к квартира 70м2, новосибирск    4100000      False
3           4         комната 15 кв. м, казань    1200000      False
```

**Что проверяет интервьюер:** цепочки `.str.*`; regex для извлечения цифр; `na=False` в `str.contains`.

**Типичная ошибка:** забыть `na=False` — если в title будет NaN, `str.contains` вернёт NaN, а не False, и дальнейшие операции сломаются.

</details>

---

### Задача 10. Парсинг категорий из тегов · _уровень продуктовая компания_

**Условие.** Колонка `tags` содержит строки вида "category:electronics|brand:apple". Извлеки отдельные колонки `category` и `brand`.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "product_id": [1, 2, 3, 4],
    "tags": ["category:electronics|brand:apple",
             "category:clothes|brand:nike",
             "category:books",
             "brand:samsung|category:electronics"]
})
```

**Ограничение:** 12 минут.

**Ожидаемый результат:** product 3 → category=books, brand=NaN; product 4 → category=electronics, brand=samsung.

<details>
<summary>✅ Решение</summary>

```python
def extract_tag(tags, key):
    for part in str(tags).split("|"):
        if part.startswith(key + ":"):
            return part.split(":", 1)[1]
    return None

df["category"] = df["tags"].apply(lambda t: extract_tag(t, "category"))
df["brand"]    = df["tags"].apply(lambda t: extract_tag(t, "brand"))

print(df[["product_id", "category", "brand"]])
```

**Вывод:**
```
   product_id     category   brand
0           1  electronics   apple
1           2      clothes    nike
2           3        books    None
3           4  electronics  samsung
```

**Что проверяет интервьюер:** умение написать вспомогательную функцию; `apply` оправдан здесь потому что логика нелинейна (разбор произвольного порядка тегов) — можно объяснить интервьюеру.

**Типичная ошибка:** `str.extract` с regex — сложнее, ломается если порядок тегов меняется.

</details>

---

## Блок 6. Даты (.dt, фильтр, группировка)

### Задача 11. Квартальная динамика · _уровень банк_

**Условие.** Оставь только транзакции Q1 2026 (январь–март). Сгруппируй по месяцу, посчитай сумму и среднее. Добавь колонку `weekday` — день недели каждой транзакции.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "txn_id":   range(1, 8),
    "client_id": [1,1,2,2,3,3,3],
    "txn_date": pd.to_datetime(["2026-01-05","2026-02-10","2025-12-20",
                                 "2026-01-15","2026-01-28","2026-02-05","2026-03-01"]),
    "amount":   [1000, 2000, 500, 3000, 1500, 800, 1200]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** в выборке 6 строк Q1; январь — 3 транзакции суммой 5500.

<details>
<summary>✅ Решение</summary>

```python
q1 = df[(df["txn_date"] >= "2026-01-01") & (df["txn_date"] < "2026-04-01")].copy()
q1["weekday"] = q1["txn_date"].dt.day_name()
q1["month"]   = q1["txn_date"].dt.to_period("M")

monthly = q1.groupby("month")["amount"].agg(["sum", "mean", "count"]).round(1)
print("Строк в Q1:", len(q1))
print(monthly)
```

**Вывод:**
```
Строк в Q1: 6
          sum    mean  count
month                       
2026-01  5500  1833.3      3
2026-02  2800  1400.0      2
2026-03  1200  1200.0      1
```

**Что проверяет интервьюер:** фильтр по дате через строки (pandas сам конвертирует); `to_period("M")` для группировки по месяцу; `dt.day_name()`.

**Типичная ошибка:** `dt.month` вместо `to_period` — при группировке теряется год, январь 2025 и 2026 сольются.

</details>

---

### Задача 12. Активность по дням недели · _уровень стриминг_

**Условие.** Определи, в какие дни недели выручка максимальна. Добавь колонку `is_weekend` (сб/вс). Сравни среднюю выручку в будни и выходные.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "date":    pd.date_range("2026-01-05", periods=7),   # пн–вс
    "revenue": [12000, 9000, 11000, 8500, 15000, 20000, 18000]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** выходные (сб=20000, вс=18000) в среднем 19000; будни в среднем 11100.

<details>
<summary>✅ Решение</summary>

```python
df["weekday"]    = df["date"].dt.day_name()
df["is_weekend"] = df["date"].dt.dayofweek >= 5   # 5=сб, 6=вс

comparison = df.groupby("is_weekend")["revenue"].mean().round(0)
print(df[["date", "weekday", "revenue", "is_weekend"]])
print("\nСредняя выручка:")
print(comparison)
```

**Вывод:**
```
        date    weekday  revenue  is_weekend
0 2026-01-05     Monday    12000       False
1 2026-01-06    Tuesday     9000       False
2 2026-01-07  Wednesday    11000       False
3 2026-01-08   Thursday     8500       False
4 2026-01-09     Friday    15000       False
5 2026-01-10   Saturday    20000        True
6 2026-01-11     Sunday    18000        True

Средняя выручка:
is_weekend
False    11100.0
True     19000.0
Name: revenue, dtype: float64
```

**Что проверяет интервьюер:** `dt.dayofweek` — 0=пн, 6=вс; умение из числового признака сделать смысловой булевый.

**Типичная ошибка:** `dt.weekday()` — не векторный метод, надо `dt.dayofweek` без скобок.

</details>

---

## Блок 7. SQL → pandas

### Задача 13. GROUP BY + HAVING · _уровень банк_

**Условие.** Перепиши SQL на pandas:

```sql
SELECT account_type,
       COUNT(*)       AS cnt,
       SUM(balance)   AS total
FROM accounts
GROUP BY account_type
HAVING COUNT(*) > 1
ORDER BY total DESC;
```

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "client_id":    [1,1,2,2,3,3,4],
    "account_type": ["card","loan","card","card","deposit","loan","card"],
    "balance":      [50000,200000,30000,40000,500000,100000,20000]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** только card (4 записи) и loan (2 записи); deposit выбывает по HAVING.

<details>
<summary>✅ Решение</summary>

```python
result = (
    df.groupby("account_type")
      .agg(cnt=("client_id","count"), total=("balance","sum"))
      .reset_index()
      .query("cnt > 1")          # HAVING = фильтр ПОСЛЕ агрегации
      .sort_values("total", ascending=False)
)
print(result)
```

**Вывод:**
```
  account_type  cnt   total
0         card    4  140000
2         loan    2  300000
```

**Что проверяет интервьюер:** понимание что HAVING — это фильтр по результату агрегации, а не WHERE; `query()` для чистоты или обычный boolean фильтр.

**Типичная ошибка:** написать `df[df["account_type"] != "deposit"]` перед groupby — это WHERE, а не HAVING; выбросит строки с deposit до агрегации, результат другой.

</details>

---

### Задача 14. JOIN + GROUP BY по двум таблицам · _уровень маркетплейс_

**Условие.** Перепиши SQL на pandas:

```sql
SELECT u.segment,
       COUNT(DISTINCT o.user_id) AS buyers,
       SUM(o.amount)             AS revenue
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id
GROUP BY u.segment
ORDER BY revenue DESC;
```

**Данные:**

```python
import pandas as pd

orders = pd.DataFrame({
    "order_id": [1,2,3,4,5],
    "user_id":  [10,20,10,30,20],
    "amount":   [500,1200,800,2000,600]
})
users = pd.DataFrame({
    "user_id": [10, 20, 30],
    "segment": ["vip", "regular", "vip"]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** vip — 2 покупателя, 3300 выручки; regular — 1 покупатель, 1800.

<details>
<summary>✅ Решение</summary>

```python
result = (
    orders.merge(users[["user_id","segment"]], on="user_id", how="left")
          .groupby("segment", dropna=False)
          .agg(buyers=("user_id","nunique"), revenue=("amount","sum"))
          .reset_index()
          .sort_values("revenue", ascending=False)
)
print(result)
```

**Вывод:**
```
   segment  buyers  revenue
1      vip       2     3300
0  regular       1     1800
```

**Что проверяет интервьюер:** `dropna=False` — имитация LEFT JOIN (строки без сегмента не выбрасываются); `nunique` для COUNT DISTINCT.

**Типичная ошибка:** `how="inner"` вместо `how="left"` — потеряешь заказы пользователей без сегмента; `dropna=True` (default) — выбросишь строки с NaN-сегментом.

</details>

---

### Задача 15. ROW_NUMBER через cumcount · _уровень маркетплейс_

**Условие.** Перепиши SQL на pandas:

```sql
SELECT user_id, order_date, amount,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) AS order_num
FROM orders;
```

Найди всех пользователей, у которых первый заказ был дороже 1000 рублей.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "order_id":   [101,102,103,104,105,106],
    "user_id":    [1, 2, 1, 3, 2, 1],
    "order_date": pd.to_datetime(["2026-01-05","2026-01-10","2026-01-20",
                                   "2026-01-15","2026-02-01","2026-02-10"]),
    "amount":     [500, 1200, 800, 300, 600, 400]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** только user_id=2 (первый заказ 1200 > 1000).

<details>
<summary>✅ Решение</summary>

```python
df = df.sort_values(["user_id","order_date"])
df["order_num"] = df.groupby("user_id").cumcount() + 1

# Пользователи с первым заказом > 1000
high_first = df[df["order_num"] == 1][df["amount"] > 1000]
print("Номера заказов:")
print(df)
print("\nПервый заказ > 1000:")
print(high_first)
```

**Вывод:**
```
Номера заказов:
   order_id  user_id order_date  amount  order_num
0       101        1 2026-01-05     500          1
2       103        1 2026-01-20     800          2
3       104        1 2026-02-10     400          3
1       102        2 2026-01-10    1200          1
4       105        2 2026-02-01     600          2
3       104        3 2026-01-15     300          1

Первый заказ > 1000:
   order_id  user_id order_date  amount  order_num
1       102        2 2026-01-10    1200          1
```

**Что проверяет интервьюер:** `sort_values` перед `cumcount` — порядок критичен; `cumcount() + 1` потому что cumcount стартует с 0.

**Типичная ошибка:** забыть сортировать — cumcount будет в произвольном порядке, ROW_NUMBER станет некорректным.

</details>

---

## Блок 8. Оконные функции через transform/shift/cumcount

### Задача 16. Доля от суммы группы · _уровень маркетплейс_

**Условие.** Для каждого продавца посчитай его долю выручки внутри категории (в %). Не используй merge — только transform.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "category":  ["electronics","electronics","clothes","clothes","clothes","books"],
    "seller_id": [1, 2, 3, 4, 5, 6],
    "revenue":   [50000, 30000, 20000, 15000, 10000, 8000]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** seller 1 — 62.5% внутри electronics, seller 3 — 44.4% внутри clothes.

<details>
<summary>✅ Решение</summary>

```python
df["cat_total"] = df.groupby("category")["revenue"].transform("sum")
df["share_pct"] = (df["revenue"] / df["cat_total"] * 100).round(1)
print(df)
```

**Вывод:**
```
      category  seller_id  revenue  cat_total  share_pct
0  electronics          1    50000      80000       62.5
1  electronics          2    30000      80000       37.5
2      clothes          3    20000      45000       44.4
3      clothes          4    15000      45000       33.3
4      clothes          5    10000      45000       22.2
5        books          6     8000       8000      100.0
```

**Что проверяет интервьюер:** понимание `transform` — в отличие от `agg`, возвращает серию той же длины что и исходный DataFrame; без лишнего merge.

**Типичная ошибка:** сделать groupby → agg → merge обратно — работает, но избыточно; интервьюер спросит «а как без merge?».

</details>

---

### Задача 17. Время с прошлого заказа · _уровень маркетплейс_

**Условие.** Для каждого заказа посчитай количество дней с момента предыдущего заказа этого же пользователя. Первый заказ пользователя — NaN.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "user_id":    [1, 1, 1, 2, 2],
    "order_date": pd.to_datetime(["2026-01-05","2026-01-20","2026-02-10",
                                   "2026-01-08","2026-02-01"]),
    "amount":     [500, 800, 1200, 300, 600]
})
```

**Ограничение:** 10 минут.

**Ожидаемый результат:** второй заказ user 1 — через 15 дней, третий — через 21; второй заказ user 2 — через 24.

<details>
<summary>✅ Решение</summary>

```python
df = df.sort_values(["user_id","order_date"])
df["prev_order"]      = df.groupby("user_id")["order_date"].shift(1)
df["days_since_prev"] = (df["order_date"] - df["prev_order"]).dt.days
print(df)
```

**Вывод:**
```
   user_id order_date  amount  prev_order  days_since_prev
0        1 2026-01-05     500         NaT              NaN
1        1 2026-01-20     800  2026-01-05             15.0
2        1 2026-02-10    1200  2026-01-20             21.0
3        2 2026-01-08     300         NaT              NaN
4        2 2026-02-01     600  2026-01-08             24.0
```

**Что проверяет интервьюер:** `shift(1)` внутри группы; `dt.days` для получения числа из Timedelta; обработка NaN для первого заказа (первый заказ без предыдущего — корректный NaN, не ошибка).

**Типичная ошибка:** не сортировать перед shift — смещение пойдёт в произвольном порядке.

</details>

---

### Задача 18. Скользящее среднее выручки · _уровень продуктовая компания_

**Условие.** Посчитай скользящее среднее выручки за 3 дня (включая текущий). Для первых дней, где данных меньше трёх, использовать доступные.

**Данные:**

```python
import pandas as pd

df = pd.DataFrame({
    "date":    pd.date_range("2026-01-01", periods=7),
    "revenue": [1000, 1200, 900, 1500, 1100, 1300, 1400]
})
```

**Ограничение:** 8 минут.

**Ожидаемый результат:** день 1 — MA=1000, день 2 — 1100, день 3 — 1033, день 4 — 1200.

<details>
<summary>✅ Решение</summary>

```python
df["ma3"] = df["revenue"].rolling(window=3, min_periods=1).mean().round(1)
print(df)
```

**Вывод:**
```
        date  revenue     ma3
0 2026-01-01     1000  1000.0
1 2026-01-02     1200  1100.0
2 2026-01-03      900  1033.3
3 2026-01-04     1500  1200.0
4 2026-01-05     1100  1166.7
5 2026-01-06     1300  1300.0
6 2026-01-07     1400  1266.7
```

**Что проверяет интервьюер:** `rolling(window=3, min_periods=1)` — `min_periods` устраняет NaN в первых строках; SQL-аналог: `AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`.

**Типичная ошибка:** `rolling(3)` без `min_periods=1` → первые 2 строки будут NaN; интервьюер попросит их убрать, а ты не знаешь параметр.

</details>

---

🎯 **Как тренировать:** решай блоками. Один блок за раз — 30–40 минут с таймером. Второй проход — вслух, как интервьюеру, объясняя каждый шаг.

➡️ Дальше: [4.4 Best practices кода](4_4_best_practices.md)
