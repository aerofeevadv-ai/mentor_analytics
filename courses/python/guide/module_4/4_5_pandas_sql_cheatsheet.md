# 📎 4.5 Шпаргалка pandas ↔ SQL

Полная таблица соответствий. Держи под рукой на собеседовании готовился — вопрос «перепиши SQL на pandas» встречается регулярно.

---

## Таблица соответствий

| SQL | pandas |
|---|---|
| `SELECT col1, col2` | `df[["col1", "col2"]]` |
| `SELECT col AS new_name` | `df.rename(columns={"col": "new_name"})` |
| `WHERE age > 30` | `df[df["age"] > 30]` |
| `WHERE a > 1 AND b < 5` | `df[(df["a"] > 1) & (df["b"] < 5)]` |
| `WHERE city IN (...)` | `df[df["city"].isin([...])]` |
| `WHERE x BETWEEN 20 AND 30` | `df[df["x"].between(20, 30)]` |
| `WHERE name LIKE '%abc%'` | `df[df["name"].str.contains("abc", na=False)]` |
| `WHERE x IS NULL` | `df[df["x"].isna()]` |
| `WHERE x IS NOT NULL` | `df[df["x"].notna()]` |
| `CASE WHEN ... THEN ...` | `np.where(cond, a, b)` / `apply` / `map` |
| `CAST(x AS INT)` | `df["x"].astype(int)` |
| `COALESCE(x, 0)` | `df["x"].fillna(0)` |
| `GROUP BY city` | `df.groupby("city")` |
| `COUNT(*)` | `.size()` |
| `COUNT(col)` | `.count()` |
| `COUNT(DISTINCT col)` | `.nunique()` |
| `AVG / SUM / MIN / MAX` | `.mean() / .sum() / .min() / .max()` |
| `HAVING SUM(x) > 100` | агрегировать → фильтровать результат |
| `ORDER BY x DESC` | `df.sort_values("x", ascending=False)` |
| `LIMIT 10` | `.head(10)` |
| `JOIN ... ON` | `df1.merge(df2, on="key")` |
| `LEFT JOIN` | `df1.merge(df2, on="key", how="left")` |
| `FULL OUTER JOIN` | `how="outer"` |
| `UNION ALL` | `pd.concat([df1, df2], ignore_index=True)` |
| `SELECT DISTINCT` | `df.drop_duplicates()` |
| `ROW_NUMBER() OVER (PARTITION BY u ORDER BY d)` | `df.sort_values("d").groupby("u").cumcount() + 1` |
| `SUM(x) OVER (PARTITION BY u)` | `df.groupby("u")["x"].transform("sum")` |

---

## «Перепиши на pandas» — 3 разобранных примера

### Пример 1: группировка с фильтром

```sql
SELECT city, AVG(salary) AS avg_salary
FROM employees
WHERE age > 25
GROUP BY city
HAVING AVG(salary) > 70000
ORDER BY avg_salary DESC;
```

<details>
<summary>✅ pandas</summary>

```python
result = (
    employees[employees["age"] > 25]            # WHERE
    .groupby("city")["salary"].mean()           # GROUP BY + AVG
    .reset_index(name="avg_salary")
)
result = (result[result["avg_salary"] > 70000]  # HAVING = фильтр ПОСЛЕ агрегации
          .sort_values("avg_salary", ascending=False))
```

Ключ к HAVING: в pandas нет отдельного слова — просто фильтруешь уже агрегированный результат.

</details>

### Пример 2: join с агрегацией

```sql
SELECT u.segment, COUNT(DISTINCT o.user_id) AS buyers, SUM(o.amount) AS revenue
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id
GROUP BY u.segment;
```

<details>
<summary>✅ pandas</summary>

```python
result = (
    orders.merge(users[["user_id", "segment"]], on="user_id", how="left")
          .groupby("segment", dropna=False)
          .agg(buyers=("user_id", "nunique"),
               revenue=("amount", "sum"))
)
```

dropna=False — потому что LEFT JOIN в SQL оставил бы строки с NULL-сегментом, а groupby по умолчанию их выбросит.

</details>

### Пример 3: оконная функция

```sql
SELECT user_id, order_date, amount,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) AS rn
FROM orders;
```

<details>
<summary>✅ pandas</summary>

```python
orders["rn"] = (orders.sort_values("order_date")
                      .groupby("user_id")
                      .cumcount() + 1)
```

cumcount начинается с 0, поэтому +1. Для агрегата «окном на всю группу» (SUM OVER PARTITION) — `transform`.

</details>

🎯 **Практика:** возьми 3 своих рабочих SQL-запроса (или из SQL-тренажёра) и переведи на pandas. Проверь на датасете E-commerce, что результаты совпадают по цифрам.

➡️ Дальше: [4.6 Итоговый проект](4_6_final_project.md)
