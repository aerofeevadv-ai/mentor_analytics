# 4.2 Tricky-задачи pandas

Ловушки, на которых проверяют глубину понимания. Формат: сначала попробуй ответить сам, потом открой разбор.

---

## 1. Merge размножил строки

В orders 10 000 строк. После `orders.merge(users, on="user_id", how="left")` стало 11 400. Почему и как чинить?

<details>
<summary>Разбор</summary>

В users есть дубли user_id: каждая строка orders склеилась с КАЖДОЙ копией пользователя. left join не защищает от размножения — он защищает от потери строк левой таблицы.

```python
users["user_id"].duplicated().sum()          # диагностика
users = users.drop_duplicates(subset=["user_id"])   # лечение (осознанно!)
```

Профилактика: `orders.merge(users, on="user_id", how="left", validate="m:1")` — упадёт с понятной ошибкой, если справа дубли.

</details>

---

## 2. None, NaN и почему `== None` не работает

Что вернёт `df[df["city"] == None]` и как правильно найти строки с пропуском?

<details>
<summary>Разбор</summary>

Вернёт пустой DataFrame — даже если в колонке полно пропусков. Разберёмся почему, потому что здесь две разные вещи:

**None vs NaN в pandas**

В Python `None == None` → `True` (это работает). Но pandas при создании колонки object-типа конвертирует `None` в `NaN` либо хранит как Python-объект. В обоих случаях `== None` не срабатывает:

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({"city": ["Moscow", None, np.nan, "SPB"]})

df["city"] == None   # [False, False, False, False] — все False!
df["city"].isna()    # [False, True,  True,  False] — правильно
```

Почему `== None` даёт `False` даже для `None`-строк? Потому что pandas применяет vectorized-сравнение через numpy, где операция `array == None` реализована как элементное `__eq__`, а не питонный `is` или `==` объекта. Numpy возвращает `False` для любого сравнения с `None` в object-массиве.

**Отдельно про `np.nan == np.nan`**

По стандарту IEEE 754 NaN не равен сам себе:
```python
np.nan == np.nan   # False
np.nan is np.nan   # True — это один объект, но по значению не равен
```

Поэтому `df["city"] == np.nan` тоже всегда даёт `False`.

**Правильный способ во всех случаях** — `isna()`:

```python
df[df["city"].isna()]     # ловит и None, и NaN, и pd.NA
```

**Бонусный вопрос:** почему `df["a"] != df["b"]` считает «разными» две ячейки, в которых обе NaN? По той же причине: `NaN != NaN` → `True`. Для сравнения двух колонок с учётом NaN используй `df["a"].equals(df["b"])` или `df[["a","b"]].isna().all(axis=1)`.

</details>

---

## 3. Куда пропали строки после groupby

`df.groupby("city")["revenue"].sum().sum()` меньше, чем `df["revenue"].sum()`. Как так?

<details>
<summary>Разбор</summary>

В city есть NaN — groupby по умолчанию выбрасывает строки с пропуском в ключе. Выручка этих строк исчезла из группировки.

```python
df.groupby("city", dropna=False)["revenue"].sum()   # NaN станет отдельной группой
```

</details>

---

## 4. count() vs size()

Чем отличаются `df.groupby("city")["salary"].count()` и `df.groupby("city").size()`?

<details>
<summary>Разбор</summary>

count() считает НЕпустые значения колонки salary в группе, size() — все строки группы, включая пропуски. Разница между ними = количество NaN в salary по группам. Кстати, полезный приём диагностики.

</details>

---

## 5. Цепочка фильтров не сохранилась

```python
df[df["age"] > 30]["salary"] = 0
```

Код выполнился (иногда с warning), но df не изменился. Почему?

<details>
<summary>Разбор</summary>

Chained assignment: `df[маска]` создаёт промежуточную копию, и присвоение уходит в неё, а не в оригинал. Это и есть знаменитый SettingWithCopyWarning.

Правильно — через loc одной операцией:

```python
df.loc[df["age"] > 30, "salary"] = 0
```

Правило: чтение можно цепочкой, запись — только через loc.

</details>

---

## 6. Сортировка «потеряла» строки

Аналитик отсортировал по выручке по убыванию, взял head(10) — а топовый клиент не попал. Почему?

<details>
<summary>Разбор</summary>

У топового клиента в колонке NaN: при сортировке NaN всегда уходят в конец, при любом ascending. Если пропуск означает «не посчитано», сначала разберись с пропусками, потом строй топ.

```python
df.sort_values("revenue", ascending=False, na_position="first")   # увидеть их
```

</details>

---

## 7. inplace=True не сработал в цепочке

```python
df.dropna().reset_index(drop=True, inplace=True)
```

df не изменился. Почему?

<details>
<summary>Разбор</summary>

dropna() вернул копию, и inplace-операция применилась к ней — копия тут же умерла. Смешивать цепочки и inplace нельзя. Современный стиль: вообще без inplace, явное присваивание:

```python
df = df.dropna().reset_index(drop=True)
```

</details>

---

## 8. apply там, где не надо

Кандидат пишет `df["price"].apply(lambda x: x * 1.2)`. Работает. Что скажет интервьюер?

<details>
<summary>Разбор</summary>

Что это скрытый цикл: на больших данных в разы медленнее векторного `df["price"] * 1.2`. apply оправдан только для логики, которую нельзя выразить векторно. Умение объяснить, КОГДА apply уместен — и есть проверяемое понимание.

</details>

---

## 9. Среднее от средних

По таблице дневных CTR кампаний посчитали `df["ctr"].mean()` и назвали это «CTR канала». Что не так?

<details>
<summary>Разбор</summary>

Среднее отношений ≠ отношение сумм. Маленькая кампания с CTR 10% перевесит гиганта с CTR 1%. Правильно: суммировать clicks и impressions, делить суммы. Это уже было в [3.7](../module_3/3_7_dataset_marketing.md) — на собесах спрашивают постоянно.

</details>

---

## 10. value_counts спрятал проблему

В колонке 40% пропусков, но `value_counts()` показывает красивое распределение. Что произошло?

<details>
<summary>Разбор</summary>

value_counts по умолчанию выбрасывает NaN. Распределение посчитано по оставшимся 60%. Диагностика данных — всегда `value_counts(dropna=False)`.

</details>

---

🎯 **Как тренировать:** пройди все 10 дважды. Второй раз — отвечай вслух, как интервьюеру, до открытия разбора. Можешь объяснить «почему», а не только «как чинить» — готов.

➡️ Дальше: [4.3 Задачи из реальных компаний](4_3_company_tasks.md)
