# WORKFLOWS.md

Короткий справочник по типовым сценариям работы в репозитории.

## Всегда перед началом

1. Прочитай [`CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/CLAUDE.md)
2. Перейди в нужный раздел и прочитай локальный `CLAUDE.md`
3. Посмотри соседние файлы, чтобы не создавать новый формат поверх существующего

## 1. Новый YouTube-ролик

Где работать:

- [`content/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/content/CLAUDE.md)
- [`content/youtube/README.md`](/Users/aleksejerofeev/mentor_analytics/content/youtube/README.md)
- `content/youtube/productions/[slug]/`

Порядок:

1. Создать папку `content/youtube/productions/[slug]/`
2. Сначала написать `brief.md`
3. После согласования написать `script.md`
4. Затем собрать:
   - `editing_brief.md`
   - `thumbnail_brief.md`
   - `seo.md`
   - `shorts_brief.md`
5. При необходимости добавить `refs/ref_01.md`, `ref_02.md`

## 2. Новый Telegram-пост

Где работать:

- [`content/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/content/CLAUDE.md)
- `content/telegram/`

Порядок:

1. Определить тип: полезный / нарративный / анонс
2. Сформулировать один главный тезис
3. Создать файл в формате `YYYY-MM-DD_slug.md`, если это полноценный пост
4. Сохранить статус `DRAFT` или `ГОТОВО`

## 3. Новый курс или новый крупный раздел курса

Где работать:

- [`courses/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/courses/CLAUDE.md)

Порядок:

1. Сначала `structure.md`
2. Затем `sections/XX_*.md`
3. Только после согласования всех частей писать финальный `guide.md`
4. После этого добавлять `scripts/intro_script.md` и нужные скринкасты

Правило:

- не перепрыгивать сразу к финальному гайду

## 4. Доработка существующего курса

Где работать:

- в уже существующей структуре курса

Порядок:

1. Открыть `00_index.md` и соседние файлы модуля
2. Понять, это правка содержания, структуры или упражнений
3. Сохранять стиль и глубину рядом стоящих материалов
4. Если меняется структура модуля, обновить индекс

## 5. Работа по резюме-проекту

Где работать:

- [`resume/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/resume/CLAUDE.md)
- [`resume/README.md`](/Users/aleksejerofeev/mentor_analytics/resume/README.md)

Порядок:

1. Сначала анализ входных материалов в `inputs/` и `analysis/`
2. Потом создание или обновление артефактов в `outputs/`
3. Для аудита конкретного резюме опираться на уже созданные критерии и шаблоны

## 6. Работа с YouTube-скриптами

Где работать:

- `scripts/`
- [`content/youtube/README.md`](/Users/aleksejerofeev/mentor_analytics/content/youtube/README.md)
- [`Makefile`](/Users/aleksejerofeev/mentor_analytics/Makefile)

Быстрые команды:

- `make check-env`
- `make yt-auth`
- `make yt-comments`
- `make yt-comments-30`
- `make yt-ideas-discover`
- `make yt-ideas-topic TOPIC='...'`
- `make yt-titles-dry`
- `make yt-tags-dry`

Правило:

- всё, что связано с OAuth, Sheets и YouTube API, считать чувствительным действием

## 7. Транскрибация локального видео

Команда:

- `make transcribe FILE=video.mp4`

Нюансы:

- модель Whisper скачивается при первом запуске
- результат сохраняется рядом с видео или по указанному пути

## 8. Экспорт Markdown в PDF

Команда:

- `make pdf PATH=content/youtube/productions/some-slug/`

Нюансы:

- нужен `pandoc`
- если PDF-движка нет, возможен fallback в HTML

## 9. Правка маркетинговых артефактов

Где работать:

- `marketing/`

Порядок:

1. Прочитать соседние ТЗ и планы
2. Понять, это стратегический документ, ТЗ подрядчику или внутренний чеклист
3. Не менять бизнес-смысл формулировок без явной причины

## 10. Если задача неочевидна

Минимальный безопасный порядок:

1. Открыть корневой [`CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/CLAUDE.md)
2. Открыть локальный `CLAUDE.md` раздела
3. Открыть 2-3 соседних файла по теме
4. Только потом редактировать
