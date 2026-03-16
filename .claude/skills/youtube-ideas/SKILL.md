---
name: youtube-ideas
description: Use when the user asks to "find video ideas", "discover topics", "what to film", "идеи для видео", "что снять", "найти темы", "поиск идей", "topic research", "конкуренты YouTube". Scans competitor channels or searches by topic, scores videos by virality, returns top ideas for the channel.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# YouTube Ideas — Поиск виральных идей для видео

Skill для регулярного поиска идей: анализ конкурентов (RU + EN), оценка по virality score, топ-5 идей для канала «Аналитика без воды».

## Контекст канала

- **Канал:** Аналитика без воды (@analytic_offers)
- **Ниша:** карьера в аналитике, переход в профессию, подготовка к собеседованиям
- **Аудитория:** начинающие аналитики, переходящие из других профессий, 25-35 лет
- **Подписчики:** ~2 040
- **Хиты:** «Как изучать аналитику» (40K), «Чем занимается аналитик» (19K)

---

## Два режима

### 1. Discovery — сканирование конкурентов

```bash
python3 /Users/aleksejerofeev/mentor_analytics/scripts/youtube_find_ideas.py --discover [--months 6] [--max-duration 25] [--top 5]
```

Проходит по 30+ каналам (RU + EN), собирает последние 50 видео с каждого, считает virality score, выдаёт топ.

### 2. Topic — поиск по теме

```bash
python3 /Users/aleksejerofeev/mentor_analytics/scripts/youtube_find_ideas.py --topic "продуктовые метрики" [--max-duration 25] [--top 5]
```

Ищет видео по теме через YouTube Search API, оценивает по тому же score.

### Параметры

| Параметр | По умолчанию | Описание |
|---|---|---|
| `--months` | 6 | Максимальный возраст видео (только discover) |
| `--max-duration` | 25 | Макс. длительность в минутах |
| `--top` | 5 | Количество результатов |

---

## Virality Score (формула)

```
score = VSR_norm × 0.30 + VPD_norm × 0.30 + engagement_norm × 0.15 + freshness × 0.15 + duration_fit × 0.10
```

| Компонент | Что считаем | Вес |
|---|---|---|
| **VSR** (Views/Subs) | Виральность — сколько раз видео перебило базу подписчиков | 30% |
| **VPD** (Views/Day) | Динамика набора просмотров с учётом возраста | 30% |
| **Engagement** | (likes + comments) / views | 15% |
| **Freshness** | 1.0 (<3 мес), 0.7 (<6 мес), 0.4 (<12 мес), 0.2 (старше) | 15% |
| **Duration fit** | 1.0 (5-15 мин), 0.7 (15-25 мин), 0.3 (25-40 мин), 0 (40+) | 10% |

Score нормализуется к шкале 0-10.

---

## Выходные файлы

- **MD-отчёт:** `content/youtube/ideas/YYYY-MM-DD_discover.md` или `YYYY-MM-DD_topic-slug.md`
- **JSON-кэш:** `.secrets/ideas_cache.json` (для повторного анализа без API-вызовов)

---

## Workflow после запуска

1. **Запусти скрипт** (discover или topic)
2. **Прочитай MD-файл** из `content/youtube/ideas/`
3. **Для каждого видео из топа** проанализируй:
   - **Почему залетело:** высокий VSR = тема резонирует шире подписчиков; высокий VPD = свежий хайп
   - **Подходит ли для канала:** релевантно аудитории (аналитики, переход в IT)?
   - **Какой угол взять:** как адаптировать под позиционирование «до оффера»?
   - **Заголовок + обложка:** предложи варианты (используй паттерны из `/youtube-thumbnails`)
4. **Выдай итоговую рекомендацию:** топ-3 идеи, которые стоит снять, с обоснованием
5. **Если нужен сценарий** — передай в `/youtube-scripts` (TODO: будущий skill)

---

## Как интерпретировать Score

| Score | Значение |
|---|---|
| 8-10 | Супервиральное — тема залетела сильно выше нормы канала |
| 6-8 | Сильное видео — хорошая идея для адаптации |
| 4-6 | Средний результат — тема рабочая, но не вау |
| < 4 | Слабое — не стоит копировать |

### На что обращать внимание

- **Высокий VSR + низкий VPD** = SEO-накопитель (набирал годами, а не виральность)
- **Высокий VPD + низкий VSR** = большой канал, тема работает только при массе подписчиков
- **Высокий engagement** = тема вызывает дискуссию (хорошо для комментариев и алгоритма)
- **Cluster одинаковых тем** = явный спрос, стоит снять свою версию

---

## Фильтры (автоматические)

- Shorts (< 61 сек) — исключены
- Видео длиннее `--max-duration` минут — исключены
- Менее 1 000 просмотров — исключены (шум)

---

## Связка с другими skills

- `/youtube-thumbnails` — создать обложку для выбранной идеи
- `/youtube-comments` — проверить, просят ли зрители эту тему в комментариях
- Сценарий — TODO (будущий skill)

---

## Частота использования

- **Discovery:** раз в 2 недели (синхронно с графиком публикаций 1 лонг / 2 недели)
- **Topic:** по запросу, когда нужно проверить конкретную тему перед съёмкой

---

## Если токен протух

```bash
python3 /Users/aleksejerofeev/mentor_analytics/scripts/youtube_auth.py
```

---

## Каналы-конкуренты (30+)

Список в скрипте `scripts/youtube_find_ideas.py`, переменная `CHANNELS`.

RU: Немчинский, t0digital, АйТиБорода, Шумейко, winderton, Хауди Хо, Владилен Минин, Karpov.Courses, Data Learn, Глеб Михайлов, AI Search, selfedu.

EN: Alex The Analyst, Luke Barousse, Thu Vu, Ken Jee, StatQuest, Clement Mihailescu, Tina Huang, Fireship, NetworkChuck, Theo, ThePrimeagen, Traversy, Web Dev Simplified, TechWithTim, NeetCode, BroCodez, Forrest Knight, freeCodeCamp, Joshua Fluke.
