# 🎯 5.5 Тренировочный набор: 18 задач

Три уровня. Правила: решай по [скрипту из 5.4](5_4_interview_behavior.md) — вслух, с edge cases и сложностью. Без LLM. Пройди набор дважды: второй прогон через 2–3 дня.

> ⚠️ **TODO для автора:** при подключении сборника задач из компаний алгоритмические задачи добавить сюда отдельным блоком «Уровень 4: давали в компаниях» с пометками типа компании.

---

## Уровень 1. Разогрев: проход по массиву (6 задач)

1. **Сумма без sum().** `[1, 2, 3, 4]` → `10`
2. **Максимум без max().** `[3, 7, 2, 9, 4]` → `9`
3. **Подсчёт чётных.** `[1, 2, 4, 7, 8]` → `3`
4. **Индекс первого отрицательного.** `[5, 3, -2, 8]` → `2`, нет отрицательных → `-1`
5. **Реверс строки без срезов.** `"hello"` → `"olleh"`
6. **FizzBuzz.** Числа 1–N: кратно 3 → "Fizz", кратно 5 → "Buzz", кратно 15 → "FizzBuzz", иначе число

<details>
<summary>✅ Решения уровня 1</summary>

```python
# 1
def my_sum(arr):
    total = 0
    for x in arr:
        total += x
    return total

# 2
def my_max(arr):
    mx = arr[0]
    for x in arr:
        if x > mx:
            mx = x
    return mx

# 3
def count_even(arr):
    cnt = 0
    for x in arr:
        if x % 2 == 0:
            cnt += 1
    return cnt

# 4
def first_negative(arr):
    for i, x in enumerate(arr):
        if x < 0:
            return i
    return -1

# 5
def reverse_string(s):
    result = ""
    for ch in s:
        result = ch + result
    return result

# 6
def fizzbuzz(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(i)
    return result
```

Все — O(n). В задаче 6 проверка кратности 15 обязана идти первой (вспомни порядок веток из модуля 1).

</details>

---

## Уровень 2. Основа: dict и set (7 задач)

7. **Частоты элементов.** `["a","b","a"]` → `{"a": 2, "b": 1}`
8. **Есть ли дубликаты.** `[1, 2, 3, 1]` → `True` — за O(n)
9. **Первый неповторяющийся элемент.** `[2, 3, 2, 4, 3]` → `4`
10. **Самый частый элемент.** `[1, 3, 3, 2, 3]` → `3`
11. **Пересечение двух списков** без дубликатов, за O(n + m)
12. **Two sum.** Есть ли пара с суммой target — за O(n)
13. **Анаграммы.** `"listen"` и `"silent"` → `True`

<details>
<summary>✅ Решения уровня 2</summary>

```python
# 7
def count_freq(arr):
    freq = {}
    for x in arr:
        freq[x] = freq.get(x, 0) + 1
    return freq

# 8
def has_duplicates(arr):
    seen = set()
    for x in arr:
        if x in seen:
            return True
        seen.add(x)
    return False

# 9
def first_unique(arr):
    freq = count_freq(arr)          # первый проход: частоты
    for x in arr:                   # второй проход: первый с частотой 1
        if freq[x] == 1:
            return x
    return None
# два последовательных прохода — это O(n), не O(n²)

# 10
def most_frequent(arr):
    freq = count_freq(arr)
    best, best_cnt = None, 0
    for x, cnt in freq.items():
        if cnt > best_cnt:
            best, best_cnt = x, cnt
    return best

# 11
def intersection(a, b):
    return list(set(a) & set(b))
# руками: set из a, проход по b с проверкой in и set "добавленных"

# 12
def two_sum(arr, target):
    seen = set()
    for x in arr:
        if target - x in seen:
            return True
        seen.add(x)
    return False

# 13
def is_anagram(s1, s2):
    if len(s1) != len(s2):
        return False
    return count_freq(s1) == count_freq(s2)
# сортировка sorted(s1) == sorted(s2) тоже валидна, но это O(n log n)
```

</details>

---

## Уровень 3. Два указателя (5 задач)

14. **Палиндром** с игнором регистра и пробелов
15. **Пара с суммой в отсортированном массиве** — O(1) по памяти
16. **Слияние двух отсортированных списков**
17. **Разворот списка на месте** без reverse() и срезов
18. **Удаление дубликатов из отсортированного массива на месте.** `[1, 1, 2, 3, 3]` → `[1, 2, 3]`

<details>
<summary>✅ Решения уровня 3</summary>

```python
# 14
def is_palindrome(s):
    s = s.replace(" ", "").lower()
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True

# 15
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        s = arr[left] + arr[right]
        if s == target:
            return True
        elif s < target:
            left += 1
        else:
            right -= 1
    return False

# 16
def merge_sorted(a, b):
    result, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i]); i += 1
        else:
            result.append(b[j]); j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result

# 17
def reverse_in_place(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

# 18 — slow/fast указатели
def dedup_sorted(arr):
    if not arr:
        return arr
    slow = 0                        # граница уникальной части
    for fast in range(1, len(arr)):
        if arr[fast] != arr[slow]:
            slow += 1
            arr[slow] = arr[fast]
    return arr[:slow + 1]
```

</details>

---

## 🏁 Финал модуля

- [ ] уровни 1–2 решаются без подсказок, вслух, со сложностью
- [ ] уровень 3 решён минимум на 4/5
- [ ] набор пройден дважды

Этого достаточно для ~90% алго-секций на позиции аналитика. Если конкретная компания славится жёсткими алгоритмами — добери 10–15 задач LeetCode easy по тегам array/hash-table, паттерны те же.

➡️ Дальше: [Модуль 6. Записи реальных собеседований](../module_6/00_index.md)
