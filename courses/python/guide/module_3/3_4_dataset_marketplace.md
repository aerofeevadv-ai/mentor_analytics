# 🎯 3.4 Датасет: Маркетплейс

Каталог товаров и продавцы. Главный фокус — **merge и его ловушки**: дубли ключей, потерянные строки, расхождение метрик.

## Схема

**products.csv** — товары (~3 000 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| product_id | int | ключ |
| seller_id | int | внешний ключ к продавцам |
| category | str | есть пропуски |
| price | str | ⚠️ грязный: пробелы, запятые вместо точек |
| in_stock | int | остаток |
| sales_30d | int | продажи за 30 дней |

**sellers.csv** — продавцы (~400 строк)

| Колонка | Тип | Особенности |
|---|---|---|
| seller_id | int | ⚠️ есть дубли (продавец заведён дважды) |
| seller_name | str | |
| rating | float | есть пропуски |
| city | str | |
| is_verified | bool | |

## Задачи

1. Приведи `price` к числу (`str.replace` + `pd.to_numeric(errors="coerce")`). Сколько значений не удалось распознать?
2. Проверь дубли seller_id в sellers. Посмотри на них глазами: чем отличаются копии? Оставь по продавцу одну запись (с максимальным rating).
3. Сделай merge товаров с продавцами ДО чистки дублей и ПОСЛЕ. Сравни количество строк, объясни разницу.
4. Сколько товаров остались без продавца (битый seller_id)? Какая на них приходится доля продаж?
5. Выручка за 30 дней (price × sales_30d) по городам продавцов.
6. Сравни средний рейтинг верифицированных и неверифицированных продавцов.
7. Топ-10 продавцов по выручке. Есть ли среди них продавцы без рейтинга?
8. Доля товаров не в наличии (in_stock == 0) по категориям, отсортируй по убыванию.
9. Витрина по продавцам: товаров в каталоге, из них в наличии, суммарная выручка, средняя цена. Только продавцы с 5+ товарами.

<details>
<summary>✅ Решения</summary>

```python
import pandas as pd

products = pd.read_csv("products.csv")
sellers = pd.read_csv("sellers.csv")

# 1
products["price"] = (products["price"].str.strip()
                                       .str.replace(",", ".", regex=False))
products["price"] = pd.to_numeric(products["price"], errors="coerce")
products["price"].isna().sum()
# 📌 Проверь себя: 20 значений не распознались

# 2
sellers.duplicated(subset=["seller_id"]).sum()
sellers[sellers.duplicated(subset=["seller_id"], keep=False)].sort_values("seller_id")
# na_position="first" — иначе keep="last" оставит копию с NaN вместо рейтинга
sellers = (sellers.sort_values("rating", na_position="first")
                  .drop_duplicates(subset=["seller_id"], keep="last"))
# 📌 Проверь себя: 30 дублей, после чистки 400 продавцов

# 3
# до чистки merge размножил бы товары задублированных продавцов
m = products.merge(sellers, on="seller_id", how="left")
len(products), len(m)   # после чистки совпадают
# 📌 Проверь себя: до чистки 3221 строка, после — 3000

# 4
no_seller = m[m["seller_name"].isna()]
len(no_seller)
(no_seller["price"] * no_seller["sales_30d"]).sum() / (m["price"] * m["sales_30d"]).sum()
# 📌 Проверь себя: 87 товаров, ≈3.1% продаж

# 5
m["revenue_30d"] = m["price"] * m["sales_30d"]
m.groupby("city")["revenue_30d"].sum().sort_values(ascending=False)
# 📌 Проверь себя: лидер Kazan ≈ 12 366 679

# 6
m.groupby("is_verified")["rating"].mean()
# 📌 Проверь себя: 3.74 у неверифицированных против 3.82 у верифицированных

# 7
top = (m.groupby(["seller_id", "seller_name"], dropna=False)["revenue_30d"]
        .sum().sort_values(ascending=False).head(10))
# 📌 Проверь себя: топ-1 seller_236 ≈ 461 163; без рейтинга в топ-10 — один продавец

# 8
(m.assign(out_of_stock=m["in_stock"] == 0)
  .groupby("category")["out_of_stock"].mean()
  .sort_values(ascending=False))
# 📌 Проверь себя: худшая категория home — 15.9% не в наличии

# 9
vitrina = m.groupby(["seller_id", "seller_name"]).agg(
    products_cnt=("product_id", "count"),
    in_stock_cnt=("in_stock", lambda x: (x > 0).sum()),
    revenue_30d=("revenue_30d", "sum"),
    avg_price=("price", "mean"),
)
vitrina[vitrina["products_cnt"] >= 5]
# 📌 Проверь себя: 343 продавца с 5+ товарами
```

</details>

> ⚠️ **NaN при сортировке:** `sort_values` всегда отправляет NaN в конец — независимо от `ascending`. Поэтому `sort_values("rating") + keep="last"` оставит у продавца копию **без рейтинга**, если она есть: в этом датасете так потеряли бы рейтинг 4 продавца. Лекарство — `na_position="first"`. Молчаливая ловушка, на собеседованиях её любят.

➡️ Дальше: [3.5 Логистика](3_5_dataset_logistics.md)
