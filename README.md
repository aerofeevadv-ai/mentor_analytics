# Mentor Analytics

Рабочий репозиторий проекта Mentor Analytics: менторство "до оффера", контент, курсы и инструменты для работы с резюме аналитиков.

## Что находится в репозитории

- `content/` - YouTube, Telegram, social-контент и связанные workflow
- `courses/` - гайды и материалы курсов 20/80
- `resume/` - проект по аудиту и улучшению резюме аналитиков
- `marketing/` - маркетинговые артефакты и ТЗ
- `scripts/` - вспомогательные Python-скрипты для YouTube, транскрибации, PDF и изображений
- `outputs/` - артефакты, которые генерируются в процессе работы
- `.secrets/` - локальные секреты и токены, не коммитятся в git

## С чего начать

1. Открой [`CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/CLAUDE.md) - это главный бизнес-контекст.
2. Перейди в нужный подпроект и прочитай его локальный `CLAUDE.md`:
   - [`content/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/content/CLAUDE.md)
   - [`courses/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/courses/CLAUDE.md)
   - [`resume/CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/resume/CLAUDE.md)
3. Только после этого начинай создавать или редактировать артефакты.

## Типовые сценарии

### Контент

- Для нового YouTube-видео сначала создать `brief.md`, затем после согласования писать `script.md`
- Для Telegram-поста можно сразу писать пост, если понятны тип и тезис
- Детали по YouTube и скриптам: [`content/youtube/README.md`](/Users/aleksejerofeev/mentor_analytics/content/youtube/README.md)

### Курсы

- Нельзя сразу писать финальный гайд
- Сначала `structure.md`, потом `sections/`, и только после статуса `СОГЛАСОВАНО` - полный `guide.md`

### Резюме

- Сначала анализ входных резюме и исследований
- Затем генерация артефактов в `outputs/`

## Python-окружение

В репозитории нет пакетного менеджера уровня `pyproject.toml`, поэтому базовый способ запуска сейчас такой:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для локальной настройки окружения смотри:

- [`.env.example`](/Users/aleksejerofeev/mentor_analytics/.env.example) - какие переменные и локальные файлы ожидаются
- [`Makefile`](/Users/aleksejerofeev/mentor_analytics/Makefile) - короткие команды для типовых сценариев

## Что важно не трогать без необходимости

- `.secrets/` - токены, ключи, служебные JSON-файлы
- `.claude/settings.local.json` - локальная конфигурация среды
- Пользовательские незакоммиченные изменения в рабочем дереве

## Полезные файлы

- [`CLAUDE.md`](/Users/aleksejerofeev/mentor_analytics/CLAUDE.md) - корневой контекст проекта
- [`AGENTS.md`](/Users/aleksejerofeev/mentor_analytics/AGENTS.md) - инструкция для AI-агентов и исполнителей
- [`STATUS.md`](/Users/aleksejerofeev/mentor_analytics/STATUS.md) - быстрый снимок текущего состояния репозитория
- [`WORKFLOWS.md`](/Users/aleksejerofeev/mentor_analytics/WORKFLOWS.md) - короткие сценарии типовой работы
- [`requirements.txt`](/Users/aleksejerofeev/mentor_analytics/requirements.txt) - Python-зависимости для `scripts/`
- [`.env.example`](/Users/aleksejerofeev/mentor_analytics/.env.example) - шаблон локального окружения
- [`Makefile`](/Users/aleksejerofeev/mentor_analytics/Makefile) - быстрые команды для локальной работы
