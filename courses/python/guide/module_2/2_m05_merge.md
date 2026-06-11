# B5. Объединение таблиц

Данные почти никогда не лежат в одной таблице: заказы отдельно, пользователи отдельно, справочники отдельно. Эта группа — про то, как их соединять.

**SQL-аналог группы:** `JOIN`, `UNION ALL`.

---

## merge() — соединение по ключу

**Что делает:** объединяет две таблицы по общей колонке. Это JOIN, который ты знаешь.

```python
orders.merge(users, on="user_id")                  # INNER JOIN по user_id
orders.merge(users, on="user_id", how="left")      # LEFT JOIN
```

**SQL:** `FROM orders JOIN users ON orders.user_id = users.user_id`

**Типы соединения — как в SQL:**

| how | SQL | Что остаётся |
|---|---|---|
| inner (дефолт) | INNER JOIN | только совпавшие ключи |
| left | LEFT JOIN | все строки левой таблицы |
| right | RIGHT JOIN | все строки правой |
| outer | FULL OUTER JOIN | всё из обеих |

**Чуть сложнее:** разные имена ключей и одинаковые имена колонок:

```python
orders.merge(users, left_on="client_id", right_on="user_id")
orders.merge(users, on="user_id", suffixes=("_order", "_user"))
```

> ⚠️ **Подводный камень №1 — дубли ключей.** Если user_id в правой таблице встречается дважды, каждая строка левой размножится. Было 10 000 заказов, после merge стало 14 000 — значит, в «справочнике» дубли. Проверка до merge: `users["user_id"].duplicated().sum()`, проверка после: shape. Это самый частый источник завышенных метрик в реальной работе и любимая tricky-задача собеседований.

> ⚠️ **Подводный камень №2 — потерянные строки.** inner по умолчанию: строки без пары молча исчезают. Считаешь метрики по всем заказам — используй how="left" от таблицы заказов и проверь, сколько NaN пришло из правой таблицы.

---

## validate — однострочная страховка от дублей

Параметр `validate` проверяет кратность связи до слияния и падает с ошибкой, если реальность расходится с ожиданием:

```python
orders.merge(users, on="user_id", how="left", validate="many_to_one")
# Упадёт, если в users окажутся дубли по user_id
# Варианты: "one_to_one", "one_to_many", "many_to_one", "many_to_many"
```

Три лишние секунды при написании кода — экономия часа разбора «почему строк вдруг стало больше».

---

## concat() — склейка таблиц

**Что делает:** склеивает таблицы по вертикали (друг под друга) или горизонтали.

```python
# Вертикально: данные за январь + февраль (UNION ALL)
df_all = pd.concat([df_jan, df_feb], ignore_index=True)

# Горизонтально: приставить колонки сбоку (редко, лучше merge)
df_wide = pd.concat([df1, df2], axis=1)
```

**SQL:** вертикальный concat = `UNION ALL` (дубликаты НЕ удаляются — как ALL, не как UNION).

**Подводные камни:**

- `ignore_index=True` обязателен при вертикальной склейке, иначе индексы задублируются (0,1,2,0,1,2...)
- колонки матчатся по именам: если в одной таблице `revenue`, а в другой `Revenue` — получишь обе колонки и NaN в каждой

---

## merge или concat?

| Задача | Инструмент |
|---|---|
| Обогатить заказы данными пользователей | merge (по ключу) |
| Склеить одинаковые таблицы за разные месяцы | concat (вертикально) |
| «JOIN» из SQL | merge |
| «UNION ALL» из SQL | concat |

---

## 🧠 Как этим пользуется профи

Перед merge: проверил дубли ключа в обеих таблицах. После merge: сверил shape с ожиданием и посчитал NaN в приклеенных колонках. Три лишние строки кода, которые экономят часы поиска «почему выручка выросла вдвое».

🎯 **Практика:** в датасетах курса есть `orders.csv` (order_id, user_id, order_date, city, category, price, quantity, promo_code, status) и `users.csv` (user_id, signup_date, segment, channel). 1) Приклей к заказам сегмент пользователя так, чтобы ни один заказ не потерялся; 2) посмотри, сколько заказов осталось без сегмента (user не найден в users) — используй `how="left"`; 3) добавь `validate="many_to_one"` — убедись, что ключ в users уникален; 4) намеренно добавь дубль одного user_id в users, повтори merge без validate и объясни, что произошло с количеством строк.

<details>
<summary>✅ Решение</summary>

```python
import pandas as pd
orders = pd.read_csv("orders.csv")
users  = pd.read_csv("users.csv")

# 1-2. LEFT JOIN, не теряем заказы
merged = orders.merge(users, on="user_id", how="left", validate="many_to_one")
print("shape:", merged.shape)    # должно быть (5100, 12)
print("без сегмента:", merged["segment"].isna().sum())

# 3. validate держит честность ключа
# 4. Демонстрация роста строк при дублях ключа
users_with_dup = pd.concat([users, users.iloc[[0]]], ignore_index=True)
merged_dup = orders.merge(users_with_dup, on="user_id", how="left")
print("строк с дублём ключа:", merged_dup.shape[0])   # больше 5100!
```

</details>

➡️ Дальше: [B6. Пропуски](2_m06_missing.md)
