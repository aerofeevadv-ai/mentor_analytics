# 🎯 5.5 Тренировочный набор: 22 задачи

Три уровня. Правила: решай по [скрипту из 5.4](5_4_interview_behavior.md) — вслух, с edge cases и сложностью. Без LLM. Пройди набор дважды: второй прогон через 2–3 дня.

Как работать с задачей: попробуй решить сам → застрял — открой подсказку → реши → сверься с решением и сложностью.

<!-- TODO для автора: при подключении сборника задач из компаний алгоритмические задачи добавить сюда отдельным блоком «Уровень 4: давали в компаниях» с пометками типа компании. -->

---

## Уровень 1. Разогрев: проход по массиву (8 задач)

**1. Сумма без sum().** `[1, 2, 3, 4]` → `10`

<details>
<summary>💡 Подсказка</summary>

Аккумулятор `total = 0`, один проход, прибавляй каждый элемент.

</details>

**2. Максимум без max().** `[3, 7, 2, 9, 4]` → `9`

<details>
<summary>💡 Подсказка</summary>

Стартуй с первого элемента, сравнивай и обновляй. Подумай, что будет на пустом списке.

</details>

**3. Подсчёт чётных.** `[1, 2, 4, 7, 8]` → `3`

<details>
<summary>💡 Подсказка</summary>

Счётчик + условие `x % 2 == 0`.

</details>

**4. Индекс первого отрицательного.** `[5, 3, -2, 8]` → `2`, нет отрицательных → `-1`

<details>
<summary>💡 Подсказка</summary>

`enumerate` даёт индекс; `return` можно сделать прямо из цикла.

</details>

**5. Реверс строки без срезов.** `"hello"` → `"olleh"`

<details>
<summary>💡 Подсказка</summary>

Собирай новую строку, добавляя каждый следующий символ В НАЧАЛО.

</details>

**6. FizzBuzz.** Числа 1–N: кратно 3 → "Fizz", кратно 5 → "Buzz", кратно 15 → "FizzBuzz", иначе число

<details>
<summary>💡 Подсказка</summary>

Порядок веток: проверка кратности 15 — первая, иначе до неё не дойдёт.

</details>

**7. Факториал итеративно.** `5` → `120`, без рекурсии

<details>
<summary>💡 Подсказка</summary>

Аккумулятор `result = 1`, умножай на числа от 2 до n.

</details>

**8. N-е число Фибоначчи итеративно.** `fib(10)` → `55` (отсчёт: fib(0)=0, fib(1)=1)

<details>
<summary>💡 Подсказка</summary>

Храни два последних числа и обновляй их парой: `a, b = b, a + b`.

</details>

<details>
<summary>✅ Решения уровня 1</summary>

```python
# 1
def my_sum(arr):
    total = 0
    for x in arr:
        total += x
    return total
# O(n) время, O(1) память

# 2
def my_max(arr):
    mx = arr[0]
    for x in arr:
        if x > mx:
            mx = x
    return mx
# O(n) время, O(1) память
# edge case: пустой список уронит arr[0] — оговори вслух (вернуть None или считать вход непустым)

# 3
def count_even(arr):
    cnt = 0
    for x in arr:
        if x % 2 == 0:
            cnt += 1
    return cnt
# O(n) время, O(1) память

# 4
def first_negative(arr):
    for i, x in enumerate(arr):
        if x < 0:
            return i
    return -1
# O(n) время, O(1) память

# 5
def reverse_string(s):
    result = ""
    for ch in s:
        result = ch + result    # новый символ в начало
    return result
# ⚠️ Честная сложность — O(n²): строки неизменяемы, каждая конкатенация
# копирует result целиком. Это та самая «скрытая сложность» из 5.1.
# Как учебное «без срезов» решение ок, но сложность назови честно.
# Идиоматичные O(n)-варианты: s[::-1] или "".join(reversed(s))

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
# O(n) время, O(n) память (на результат)

# 7
def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
# O(n) время, O(1) память
# factorial(0) → 1: цикл не выполнится ни разу — корректно

# 8
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
# O(n) время, O(1) память
# рекурсия без кэша была бы O(2^n) — так на собесе писать не надо

```

Все задачи, кроме 5-й, — O(n). В задаче 6 проверка кратности 15 обязана идти первой (вспомни порядок веток из модуля 1).

</details>

---

## Уровень 2. Основа: dict и set (8 задач)

**9. Частоты элементов.** `["a","b","a"]` → `{"a": 2, "b": 1}`

<details>
<summary>💡 Подсказка</summary>

Словарь + `freq.get(x, 0) + 1`.

</details>

**10. Есть ли дубликаты.** `[1, 2, 3, 1]` → `True` — за O(n)

<details>
<summary>💡 Подсказка</summary>

set «виденного»: если элемент уже там — дубликат.

</details>

**11. Первый неповторяющийся элемент.** `[2, 3, 2, 4, 3]` → `4`

<details>
<summary>💡 Подсказка</summary>

Два прохода: сначала частоты, потом первый элемент с частотой 1.

</details>

**12. Самый частый элемент.** `[1, 3, 3, 2, 3]` → `3`

<details>
<summary>💡 Подсказка</summary>

Частоты, потом максимум по значению словаря.

</details>

**13. Топ-k самых частых.** `[1, 3, 3, 2, 3, 2]`, k=2 → `[3, 2]`

<details>
<summary>💡 Подсказка</summary>

Частоты → `sorted(freq.items(), key=..., reverse=True)` → срез `[:k]`. Разбор связки — в [5.2](5_2_array_pass.md).

</details>

**14. Пересечение двух списков** без дубликатов, за O(n + m)

<details>
<summary>💡 Подсказка</summary>

Преврати оба списка в set — дальше один оператор.

</details>

**15. Two sum.** Есть ли пара с суммой target — за O(n)

<details>
<summary>💡 Подсказка</summary>

seen-set: для каждого x проверяй, встречалось ли уже `target - x`.

</details>

**16. Анаграммы.** `"listen"` и `"silent"` → `True`

<details>
<summary>💡 Подсказка</summary>

Одинаковые частоты символов = анаграммы. Сначала сравни длины.

</details>

<details>
<summary>✅ Решения уровня 2</summary>

```python
# 9
def count_freq(arr):
    freq = {}
    for x in arr:
        freq[x] = freq.get(x, 0) + 1
    return freq
# O(n) время, O(n) память

# 10
def has_duplicates(arr):
    seen = set()
    for x in arr:
        if x in seen:
            return True
        seen.add(x)
    return False
# O(n) время, O(n) память

# 11
def first_unique(arr):
    freq = count_freq(arr)          # первый проход: частоты
    for x in arr:                   # второй проход: первый с частотой 1
        if freq[x] == 1:
            return x
    return None
# два последовательных прохода — это O(n), не O(n²); память O(n)

# 12
def most_frequent(arr):
    freq = count_freq(arr)
    best, best_cnt = None, 0
    for x, cnt in freq.items():
        if cnt > best_cnt:
            best, best_cnt = x, cnt
    return best
# O(n) время, O(n) память

# 13
def top_k(arr, k):
    freq = count_freq(arr)
    pairs = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    return [x for x, cnt in pairs[:k]]
# O(n) на частоты + O(u log u) на сортировку, u — число уникальных (u ≤ n)
# проговори: «сортирую только уникальные значения, не весь массив»

# 14
def intersection(a, b):
    return list(set(a) & set(b))
# O(n + m) время и память
# руками: set из a, проход по b с проверкой in и set "добавленных"

# 15
def two_sum(arr, target):
    seen = set()
    for x in arr:
        if target - x in seen:
            return True
        seen.add(x)
    return False
# O(n) время, O(n) память

# 16
def is_anagram(s1, s2):
    if len(s1) != len(s2):
        return False
    return count_freq(s1) == count_freq(s2)
# O(n) время, O(n) память
# сортировка sorted(s1) == sorted(s2) тоже валидна, но это O(n log n)
```

</details>

---

## Уровень 3. Два указателя и окно (6 задач)

**17. Палиндром** с игнором регистра и пробелов

<details>
<summary>💡 Подсказка</summary>

Сначала предобработка строки, потом left/right с двух концов навстречу.

</details>

**18. Пара с суммой в отсортированном массиве** — O(1) по памяти

<details>
<summary>💡 Подсказка</summary>

Сумма крайних мала → двигай левый указатель, велика → правый.

</details>

**19. Слияние двух отсортированных списков**

<details>
<summary>💡 Подсказка</summary>

Два указателя i, j по двум спискам. Не забудь хвост после цикла.

</details>

**20. Разворот списка на месте** без reverse() и срезов

<details>
<summary>💡 Подсказка</summary>

Меняй местами крайние элементы и сходись к середине.

</details>

**21. Удаление дубликатов из отсортированного массива на месте.** `[1, 1, 2, 3, 3]` → массив начинается с `[1, 2, 3]`, верни длину уникальной части `3` (LeetCode-формат)

<details>
<summary>💡 Подсказка</summary>

slow — граница уникальной части, fast бежит вперёд и ищет новые значения.

</details>

**22. Максимальная сумма окна длины k.** `[2, 1, 5, 1, 3, 2]`, k=3 → `9` (окно `[5, 1, 3]`)

<details>
<summary>💡 Подсказка</summary>

Посчитай сумму первого окна, дальше сдвигай: прибавь новый элемент, вычти выбывший. Это sliding window — окно как «два указателя на фиксированном расстоянии».

</details>

<details>
<summary>✅ Решения уровня 3</summary>

```python
# 17
def is_palindrome(s):
    s = s.replace(" ", "").lower()
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
# O(n) время; память O(n) на предобработку (replace/lower создают копию строки),
# сам проход указателями — O(1)

# 18
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
# O(n) время, O(1) память

# 19
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
# O(n + m) время и память

# 20
def reverse_in_place(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr
# O(n) время, O(1) память

# 21 — slow/fast указатели, LeetCode-формат
def dedup_sorted(arr):
    if not arr:
        return 0
    slow = 0                        # граница уникальной части
    for fast in range(1, len(arr)):
        if arr[fast] != arr[slow]:
            slow += 1
            arr[slow] = arr[fast]
    return slow + 1                 # длина уникальной части
# O(n) время, O(1) память
# Нюанс: массив изменён на месте, первые slow+1 элементов — уникальные.
# Вернуть arr[:slow + 1] нельзя: срез создаёт КОПИЮ — это уже не «на месте»
# (сравни с задачей 20). Поэтому LeetCode и просит вернуть длину, не массив.

# 22 — sliding window
def max_window_sum(arr, k):
    if len(arr) < k:
        return None
    window = sum(arr[:k])           # сумма первого окна
    best = window
    for i in range(k, len(arr)):
        window += arr[i] - arr[i - k]   # сдвиг: добавили новый, убрали выбывший
        if window > best:
            best = window
    return best
# O(n) время, O(1) память
# наивно (sum() для каждого окна) было бы O(n·k) — проговори, почему сдвиг быстрее
```

</details>

---

## 🏁 Финал модуля

- [ ] уровни 1–2 решаются без подсказок, вслух, со сложностью
- [ ] уровень 3 решён минимум на 5/6
- [ ] набор пройден дважды

Это ядро алго-вопросов для позиции аналитика: большинство секций собирается из этих паттернов. Если конкретная компания славится жёсткими алгоритмами — добери 10–15 задач LeetCode easy по темам:

- **строки и срезы** (теги string, two-pointers) — реверсы, палиндромы, подстроки
- **бинарный поиск** (binary-search) — идея «делим пополам» из [5.1](5_1_big_o.md)
- **sliding window** — продолжение задачи 22

Паттерны те же, что в наборе, — изменится только обёртка.

➡️ Дальше: [Модуль 6. Записи реальных собеседований](../module_6/00_index.md)
