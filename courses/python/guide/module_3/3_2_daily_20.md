# 🎯 3.2 Ежедневный практикум: 20 задач

Решается на датасете **E-commerce**: `orders.csv` + `users.csv` (описание схемы — в [3.3](3_3_dataset_ecommerce.md)).

Правила — в [3.1](3_1_methodology.md): каждый день с чистого листа, на время, без подсказок. Цель: 25–30 минут.

---

## Задачи

**Просмотр**

1. Загрузи `orders.csv`. Выведи размер таблицы, первые 5 строк и структуру (типы, пропуски).
2. Выведи статистику числовых колонок. Назови одно подозрительное значение, которое видишь.

**Фильтрация**

3. Выведи заказы из Москвы дороже 5 000.
4. Выведи заказы категорий «electronics» и «books», исключив отменённые (`status == "cancelled"`).

**Колонки**

5. Создай колонку `revenue` = price × quantity.
6. Посчитай распределение заказов по категориям: количество и доли, включая пропуски.

**Группировки**

7. По каждому городу: суммарная выручка, число заказов, число уникальных покупателей. Одной таблицей с понятными именами колонок.
8. Построй сводную: средняя выручка заказа по категориям (строки) и городам (колонки).

**Объединение**

9. Приклей к заказам сегмент пользователя из `users.csv` так, чтобы ни один заказ не потерялся. Проверь размер до и после.
10. Посчитай выручку по сегментам. Сколько выручки у заказов без сегмента (NaN)?

**Пропуски**

11. Посчитай пропуски по всем колонкам заказов.
12. Заполни пропуски в `promo_code` значением `"no_promo"`. Удали заказы без `user_id`, объясни себе почему их можно удалить.

**Дубликаты**

13. Найди полные дубли строк, посмотри на них, удали.
14. Проверь дубли по `order_id`. Если есть — оставь по каждому заказу строку с последней датой.

**Сортировка**

15. Топ-10 заказов по выручке.
16. Отсортируй заказы по городу (А–Я) и дате (новые сверху).

**Текст**

17. Почисти колонку `city`: пробелы и регистр. Сравни число уникальных городов до и после.
18. Найди все заказы, в названии категории которых есть «electro», без учёта регистра и с защитой от NaN.

**Чтение и запись**

19. Сохрани очищенный датафрейм в `orders_clean.csv` без индекса.
20. Загрузи его обратно и проверь, что размер совпадает.

<details>
<summary>✅ Эталонные решения</summary>

```python
import pandas as pd

# 1
orders = pd.read_csv("orders.csv")
orders.shape
orders.head()
orders.info()
# 📌 Проверь себя: (5100, 9)

# 2
orders.describe()
# подозрительное: отрицательная price / нулевой quantity — найди в min
# 📌 Проверь себя: min price = -59541, min quantity = 0

# 3
orders[(orders["city"] == "Moscow") & (orders["price"] > 5000)]
# 📌 Проверь себя: 665 строк

# 4
orders[
    orders["category"].isin(["electronics", "books"])
    & (orders["status"] != "cancelled")
]
# 📌 Проверь себя: 1427 строк

# 5
orders["revenue"] = orders["price"] * orders["quantity"]

# 6
orders["category"].value_counts(dropna=False)
orders["category"].value_counts(normalize=True, dropna=False)
# 📌 Проверь себя: топ — sport (862), пропусков 155

# 7
orders.groupby("city").agg(
    total_revenue=("revenue", "sum"),
    orders_cnt=("order_id", "count"),
    buyers=("user_id", "nunique"),
)
# 📌 Проверь себя: 19 строк — city ещё грязный, чистка будет в задаче 17

# 8
orders.pivot_table(index="category", columns="city",
                   values="revenue", aggfunc="mean")
# 📌 Проверь себя: electronics × Moscow ≈ 26 451

# 9
users = pd.read_csv("users.csv")
print(orders.shape)
merged = orders.merge(users[["user_id", "segment"]], on="user_id", how="left")
print(merged.shape)   # строк столько же — дублей ключа нет
# 📌 Проверь себя: (5100, 10) → (5100, 11)

# 10
merged.groupby("segment", dropna=False)["revenue"].sum()
# 📌 Проверь себя: у заказов без сегмента (NaN) ≈ 3 576 054

# 11
orders.isna().sum()
# 📌 Проверь себя: user_id 103, category 155, promo_code 3309

# 12
orders["promo_code"] = orders["promo_code"].fillna("no_promo")
orders = orders.dropna(subset=["user_id"])
# заказ без user_id нельзя привязать ни к какой метрике пользователя
# 📌 Проверь себя: осталось 4997 строк

# 13
orders.duplicated().sum()
orders[orders.duplicated(keep=False)]
orders = orders.drop_duplicates()
# 📌 Проверь себя: 58 дублей, осталось 4939 строк

# 14
orders.duplicated(subset=["order_id"]).sum()
orders = (orders.sort_values("order_date")
                .drop_duplicates(subset=["order_id"], keep="last"))
# 📌 Проверь себя: 39 дублей, осталось 4900 строк

# 15
orders.sort_values("revenue", ascending=False).head(10)
# 📌 Проверь себя: максимальная выручка заказа 161 055

# 16
orders.sort_values(["city", "order_date"], ascending=[True, False])

# 17
orders["city"].nunique()
orders["city"] = orders["city"].str.strip().str.lower()
orders["city"].nunique()
# 📌 Проверь себя: 19 → 5

# 18
orders[orders["category"].str.contains("electro", case=False, na=False)]
# 📌 Проверь себя: 776 строк

# 19
orders.to_csv("orders_clean.csv", index=False)

# 20
check = pd.read_csv("orders_clean.csv")
check.shape == orders.shape
# 📌 Проверь себя: (4900, 10), True
```

</details>

---

Уложился в 25–30 минут → практикум зачтён, держи форму одним прогоном раз в несколько дней до самого собеседования.

➡️ Дальше: [3.3 Датасет E-commerce](3_3_dataset_ecommerce.md)
