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

# 2
sellers.duplicated(subset=["seller_id"]).sum()
sellers[sellers.duplicated(subset=["seller_id"], keep=False)].sort_values("seller_id")
sellers = (sellers.sort_values("rating")
                  .drop_duplicates(subset=["seller_id"], keep="last"))

# 3
# до чистки merge размножил бы товары задублированных продавцов
m = products.merge(sellers, on="seller_id", how="left")
len(products), len(m)   # после чистки совпадают

# 4
no_seller = m[m["seller_name"].isna()]
len(no_seller)
(no_seller["price"] * no_seller["sales_30d"]).sum() / (m["price"] * m["sales_30d"]).sum()

# 5
m["revenue_30d"] = m["price"] * m["sales_30d"]
m.groupby("city")["revenue_30d"].sum().sort_values(ascending=False)

# 6
m.groupby("is_verified")["rating"].mean()

# 7
top = (m.groupby(["seller_id", "seller_name"], dropna=False)["revenue_30d"]
        .sum().sort_values(ascending=False).head(10))

# 8
(m.assign(out_of_stock=m["in_stock"] == 0)
  .groupby("category")["out_of_stock"].mean()
  .sort_values(ascending=False))

# 9
vitrina = m.groupby(["seller_id", "seller_name"]).agg(
    products_cnt=("product_id", "count"),
    in_stock_cnt=("in_stock", lambda x: (x > 0).sum()),
    revenue_30d=("revenue_30d", "sum"),
    avg_price=("price", "mean"),
)
vitrina[vitrina["products_cnt"] >= 5]
```

</details>

➡️ Дальше: [3.5 Логистика](3_5_dataset_logistics.md)
