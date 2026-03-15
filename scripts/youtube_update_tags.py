"""
Массовая простановка тегов на видео YouTube-канала @analytic_offers.

Запуск:
    python3 scripts/youtube_update_tags.py          # dry-run (только показать)
    python3 scripts/youtube_update_tags.py --apply   # применить изменения

Обновляет только видео БЕЗ тегов (29 из 33).
"""

import json
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")

# ── Общие теги-основа (канал + ниша) ──────────────────────────────────
BASE_TAGS = [
    "аналитика данных",
    "аналитик данных",
    "карьера в аналитике",
    "аналитика без воды",
]

# ── Тематические пулы ─────────────────────────────────────────────────
CAREER = ["карьера в IT", "войти в IT", "войти в айти", "работа в IT", "IT профессии"]
SALARY = ["зарплата аналитика", "сколько зарабатывает аналитик", "зарплата в IT", "доход аналитика"]
INTERVIEW = ["собеседование аналитика", "собеседование в IT", "как пройти собеседование", "подготовка к собеседованию", "вопросы на собеседовании"]
TOOLS = ["SQL", "Python", "Pandas", "инструменты аналитика", "BI", "дашборд"]
AI = ["AI для аналитика", "ChatGPT аналитика", "нейросети для работы", "искусственный интеллект", "автоматизация аналитики"]
WB = ["Wildberries", "аналитик Wildberries", "рекомендательные системы", "реальная работа аналитика"]
TRENDS = ["будущее аналитики", "тренды аналитики 2026", "аналитик будущего", "AI и аналитика"]
RESUME = ["резюме аналитика", "портфолио аналитика", "как составить резюме"]
BEGINNER = ["аналитик с нуля", "обучение аналитике", "как стать аналитиком", "аналитик без опыта"]

# ── Теги для каждого видео ─────────────────────────────────────────────
TAGS_MAP = {
    # === ЛОНГИ ===

    # Эра дашборд-аналитиков закончилась. Что делать в 2026?
    "cc94v6koNHA": BASE_TAGS + TRENDS + AI + [
        "дашборд-аналитик",
        "аналитик 2026",
        "ChatGPT заменит аналитика",
        "junior аналитик",
        "навыки аналитика",
        "рынок аналитики",
    ],

    # Как выбрать IT профессию? ПОЛНЫЙ гайд для новичков
    "uE1B74LNbuI": BASE_TAGS + CAREER + BEGINNER + [
        "как выбрать профессию",
        "IT для новичков",
        "профессии в IT",
        "программист",
        "UX/UI дизайнер",
        "системный аналитик",
        "продуктовый аналитик",
        "бизнес-аналитик",
    ],

    # Excel vs Python: зарплаты 150к vs 500к
    "NOpCMvNEkwA": BASE_TAGS + SALARY + TOOLS + [
        "Excel vs Python",
        "Excel аналитика",
        "Python аналитика",
        "рост зарплаты аналитика",
        "навыки аналитика",
        "стек аналитика",
        "150 000 vs 500 000",
    ],

    # ТОП-6 нужных инструментов аналитика
    "pZLij7bl8Tc": BASE_TAGS + TOOLS + BEGINNER + [
        "инструменты аналитика 2026",
        "A/B тесты",
        "Airflow",
        "визуализация данных",
        "продуктовая аналитика",
        "что учить аналитику",
        "стек аналитика",
    ],

    # AI для аналитика: 7 способов экономить 3 часа
    "MDAI8xKvb3U": BASE_TAGS + AI + TOOLS + [
        "AI инструменты",
        "Claude аналитика",
        "ChatGPT SQL",
        "дебаг SQL",
        "оптимизация запросов",
        "продуктивность аналитика",
        "AI на работе",
    ],

    # Что РЕАЛЬНО делает аналитик в Wildberries
    "JfH6A_n-bhQ": BASE_TAGS + WB + TOOLS + [
        "аналитик в маркетплейсе",
        "пайплайны данных",
        "ML модели",
        "реальные задачи аналитика",
        "работа аналитиком",
        "Clickhouse",
    ],

    # 4 задачи в рекомендациях Wildberries
    "zV3ntjczD38": BASE_TAGS + WB + [
        "кейсы аналитика",
        "ML модель",
        "A/B тесты",
        "реальные задачи аналитика",
        "data science",
        "машинное обучение",
        "работа с данными",
        "практика аналитики",
    ],

    # === SHORTS: из «Эра дашборд-аналитиков» ===

    # Почему сертификаты больше не работают в IT
    "sS24Qos_z3s": BASE_TAGS + TRENDS + BEGINNER + [
        "сертификаты IT",
        "курсы аналитики",
        "портфолио vs сертификат",
        "junior аналитик",
    ],

    # Аналитик-инженер — новая норма рынка
    "NZgonE3lRi4": BASE_TAGS + TRENDS + [
        "аналитик-инженер",
        "analytics engineer",
        "рынок аналитики",
        "навыки аналитика 2026",
        "рост в аналитике",
        "data engineer",
    ],

    # 3 ТРЕНДА в аналитике 2026
    "e-luSu6XpL0": BASE_TAGS + TRENDS + [
        "тренды IT 2026",
        "аналитик 2026",
        "рынок IT",
        "навыки будущего",
        "data science тренды",
    ],

    # === SHORTS: из «Зарплаты аналитиков» / Excel vs Python ===

    # Почему один аналитик получает 150к, а другой 450к
    "QVAOhPwufTw": BASE_TAGS + SALARY + CAREER + [
        "зарплата 150к vs 450к",
        "рост зарплаты",
        "навыки для зарплаты",
        "грейды аналитика",
    ],

    # === SHORTS: из «AI для аналитика» ===

    # Как AI экономит часы работы аналитику
    "IDbaz8zVLX0": BASE_TAGS + AI + [
        "AI экономит время",
        "дебаг SQL с AI",
        "продуктивность",
        "автоматизация работы",
        "ChatGPT для работы",
    ],

    # AI объяснит любой запрос простыми словами
    "qD0UlcaKQaM": BASE_TAGS + AI + TOOLS + [
        "AI объяснит код",
        "ChatGPT SQL",
        "разбор кода",
        "понять SQL запрос",
    ],

    # Как AI меняет работу аналитиков данных
    "VSyZXJEatmY": BASE_TAGS + AI + TRENDS + [
        "AI меняет профессию",
        "будущее аналитика",
        "ChatGPT для аналитика",
        "навыки аналитика",
    ],

    # === SHORTS: из «Что делает аналитик в WB» ===

    # Стек аналитика в WB - не Excel
    "i2b7_HmXQvs": BASE_TAGS + WB + TOOLS + [
        "стек аналитика",
        "Clickhouse",
        "Airflow",
        "пайплайны данных",
        "big data",
    ],

    # АНАЛИТИК: Курсы vs Реальность
    "vHIOMqdHjFs": BASE_TAGS + WB + BEGINNER + [
        "курсы vs реальность",
        "курсы аналитики",
        "реальная работа аналитика",
        "стажировка аналитик",
    ],

    # 5 шагов РЕАЛЬНОЙ задачи аналитика
    "EKfh-oy4L1o": BASE_TAGS + WB + [
        "задачи аналитика",
        "реальная аналитика",
        "гипотезы в аналитике",
        "автоматизация",
        "визуализация данных",
        "работа с базами данных",
    ],

    # === SHORTS: из «Как выбрать IT профессию» ===

    # UX/UI дизайнер — выгодная профессия
    "kc66Eqz7vpc": CAREER + [
        "UX/UI дизайнер",
        "UX дизайн",
        "UI дизайн",
        "дизайнер в IT",
        "профессия дизайнера",
        "IT для новичков",
        "как выбрать профессию",
        "зарплата дизайнера",
        "войти в IT",
    ],

    # Системный аналитик - недооценённая профессия
    "Fyc8y_Vd5ic": BASE_TAGS + CAREER + [
        "системный аналитик",
        "профессия системный аналитик",
        "бизнес-анализ",
        "IT для гуманитариев",
        "зарплата системного аналитика",
    ],

    # АНАЛИТИК ДАННЫХ — профессия без упора на код
    "Jqembw_lRJE": BASE_TAGS + CAREER + SALARY + [
        "аналитик без кода",
        "профессия аналитик данных",
        "зарплата аналитика данных",
        "data analyst",
    ],

    # Машинное обучение - профессия БУДУЩЕГО
    "slBWJt1hc4A": CAREER + [
        "машинное обучение",
        "machine learning",
        "data science",
        "ML инженер",
        "зарплата ML",
        "профессия будущего",
        "искусственный интеллект",
        "Python",
        "карьера в IT",
        "высокие зарплаты IT",
    ],

    # === SHORTS: из «ТОП-10 вопросов на собеседовании» ===

    # Как ПРАВИЛЬНО отвечать на вопрос про зарплату
    "kNpLLbpAdxg": BASE_TAGS + INTERVIEW + SALARY + [
        "вопрос про зарплату",
        "зарплатные ожидания",
        "как называть зарплату",
        "переговоры о зарплате",
    ],

    # Как ПРАВИЛЬНО отвечать на вопрос про факапы
    "POGq2mQPLEk": BASE_TAGS + INTERVIEW + [
        "вопрос про ошибки",
        "факапы на работе",
        "STAR метод",
        "как отвечать про ошибки",
        "поведенческое интервью",
    ],

    # Как ПРАВИЛЬНО рассказывать о достижениях
    "zt8CKeFfF4Y": BASE_TAGS + INTERVIEW + RESUME + [
        "достижения на собеседовании",
        "как рассказать о себе",
        "STAR метод",
        "самопрезентация",
    ],

    # === SHORTS: из «Чем РЕАЛЬНО занимается аналитик» ===

    # Можно ли стать аналитиком гуманитарию?
    "J2NC6aYJ3nM": BASE_TAGS + BEGINNER + [
        "аналитик гуманитарий",
        "гуманитарий в IT",
        "аналитик без технического образования",
        "смена профессии",
        "переход в аналитику",
        "войти в IT",
    ],

    # СКОЛЬКО можно зарабатывать в аналитике
    "UOm8FKgKsFo": BASE_TAGS + SALARY + [
        "грейды аналитика",
        "junior аналитик зарплата",
        "senior аналитик зарплата",
        "middle аналитик",
        "рост зарплаты",
    ],

    # === SHORTS: из «Как ПРАВИЛЬНО изучать аналитику» ===

    # Как упаковать опыт для резюме?
    "Pih023ZQMGk": BASE_TAGS + RESUME + BEGINNER + [
        "проекты для резюме",
        "опыт аналитика",
        "pet проекты",
        "как упаковать опыт",
    ],

    # === SHORTS: из «Вот что используют аналитики: ТОП-6» ===

    # С чего начинается аналитика?
    "GZuaYCeOvzc": BASE_TAGS + TOOLS + BEGINNER + [
        "с чего начать аналитику",
        "первый шаг в аналитику",
        "SQL для начинающих",
    ],

    # AIRFLOW: как автоматизировать работу аналитика
    "HTnembt0ufw": BASE_TAGS + TOOLS + [
        "Airflow",
        "Apache Airflow",
        "автоматизация",
        "ETL",
        "пайплайны данных",
        "оркестрация",
        "data engineering",
    ],
}


def get_youtube_client():
    with open(TOKEN_PATH) as f:
        token = json.load(f)
    creds = Credentials(
        token=token["token"],
        refresh_token=token["refresh_token"],
        token_uri=token["token_uri"],
        client_id=token["client_id"],
        client_secret=token["client_secret"],
        scopes=token["scopes"],
    )
    return build("youtube", "v3", credentials=creds)


def main():
    apply = "--apply" in sys.argv
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== Режим: {mode} ===\n")

    yt = get_youtube_client()

    # Fetch current video data
    video_ids = list(TAGS_MAP.keys())
    current = {}
    for i in range(0, len(video_ids), 50):
        batch = ",".join(video_ids[i : i + 50])
        resp = yt.videos().list(part="snippet", id=batch).execute()
        for item in resp["items"]:
            current[item["id"]] = item

    updated = 0
    skipped = 0
    errors = 0

    for vid, tags in TAGS_MAP.items():
        if vid not in current:
            print(f"[SKIP] {vid} — не найдено на канале")
            skipped += 1
            continue

        item = current[vid]
        existing_tags = item["snippet"].get("tags", [])
        title = item["snippet"]["title"][:60]

        if existing_tags:
            print(f"[SKIP] {vid} | {title}... — уже {len(existing_tags)} тегов")
            skipped += 1
            continue

        # Deduplicate and limit
        unique_tags = list(dict.fromkeys(tags))[:25]

        print(f"[{'UPDATE' if apply else 'WOULD'}] {vid} | {title}...")
        print(f"         +{len(unique_tags)} тегов: {', '.join(unique_tags[:5])}...")

        if apply:
            try:
                item["snippet"]["tags"] = unique_tags
                yt.videos().update(
                    part="snippet",
                    body={"id": vid, "snippet": item["snippet"]},
                ).execute()
                updated += 1
                print(f"         OK")
                time.sleep(0.5)  # rate limit
            except Exception as e:
                print(f"         ERROR: {e}")
                errors += 1

    print(f"\n=== Итого: {updated} обновлено, {skipped} пропущено, {errors} ошибок ===")
    if not apply:
        print("Запустите с --apply для применения изменений.")


if __name__ == "__main__":
    main()
