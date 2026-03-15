"""
Google Sheets → YouTube: постинг ответов и удаление комментариев.

Читает таблицу, постит одобренные ответы, удаляет отмеченные комментарии.
Обновляет статус в таблице и comments_log.md.

Запуск:
    python3 scripts/youtube_post_replies.py --dry-run     # только показать что будет сделано
    python3 scripts/youtube_post_replies.py --apply        # реально постить
    python3 scripts/youtube_post_replies.py --sheet-id ID  # указать конкретную таблицу
"""

import json
import os
import sys
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
SHEET_ID_PATH = os.path.join(BASE_DIR, ".secrets", "comments_sheet_id.txt")
COMMENTS_LOG = os.path.join(BASE_DIR, "content", "youtube", "comments_log.md")
CHANNEL_ID = "UC12sp7LmvlgMufTDV18oNuw"

# Индексы колонок (0-based)
COL_VIDEO = 0
COL_AUTHOR = 1
COL_COMMENT = 2
COL_LIKES = 3
COL_TONALITY = 4
COL_ACTION = 5
COL_DRAFT_REPLY = 6
COL_EDIT = 7
COL_APPROVE = 8
COL_COMMENT_ID = 9


def get_credentials():
    with open(TOKEN_PATH) as f:
        token = json.load(f)
    return Credentials(
        token=token["token"],
        refresh_token=token["refresh_token"],
        token_uri=token["token_uri"],
        client_id=token["client_id"],
        client_secret=token["client_secret"],
        scopes=token["scopes"],
    )


def read_sheet(sheets, spreadsheet_id):
    """Прочитать все строки из таблицы."""
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Комментарии!A:K",
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    return rows[1:]  # Без заголовков


def get_cell(row, index, default=""):
    """Безопасно получить значение ячейки."""
    if index < len(row):
        return row[index]
    return default


def is_approved(row):
    """Проверить что строка одобрена."""
    val = get_cell(row, COL_APPROVE).strip().lower()
    return val == "да"


def get_reply_text(row):
    """Получить финальный текст ответа: Правка если есть, иначе Предложенный ответ."""
    edit = get_cell(row, COL_EDIT).strip()
    draft = get_cell(row, COL_DRAFT_REPLY).strip()
    return edit if edit else draft


def post_reply(yt, parent_id, text):
    """Отправить ответ на комментарий."""
    return yt.comments().insert(
        part="snippet",
        body={
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text,
            }
        },
    ).execute()


def delete_comment(yt, comment_id):
    """Удалить комментарий через moderation."""
    yt.comments().setModerationStatus(
        id=comment_id,
        moderationStatus="rejected",
    ).execute()


def update_sheet_status(sheets, spreadsheet_id, row_index, status):
    """Обновить статус в колонке K (11-я) для обработанной строки."""
    cell = f"Комментарии!K{row_index + 2}"  # +2: заголовок + 0-based
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=cell,
        valueInputOption="USER_ENTERED",
        body={"values": [[status]]},
    ).execute()


def ensure_status_header(sheets, spreadsheet_id):
    """Добавить заголовок «Статус» в K1 если его нет."""
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Комментарии!K1",
    ).execute()
    values = result.get("values", [])
    if not values or not values[0]:
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Комментарии!K1",
            valueInputOption="USER_ENTERED",
            body={"values": [["Статус"]]},
        ).execute()


def update_comments_log(replied, deleted, videos_with_replies, leads):
    """Дописать запись в comments_log.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n### {today}\n\n"
    entry += f"- Ответов опубликовано: {len(replied)}\n"
    entry += f"- Удалено: {len(deleted)}\n"

    if videos_with_replies:
        entry += f"- Видео с ответами: {', '.join(sorted(videos_with_replies))}\n"
    if leads:
        entry += f"- Лиды: {', '.join(leads)}\n"

    entry += f"- Способ: через Google Sheets → youtube_post_replies.py\n"

    with open(COMMENTS_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Лог обновлён: {COMMENTS_LOG}")


def main():
    # Аргументы
    dry_run = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv
    sheet_id = None

    for i, arg in enumerate(sys.argv):
        if arg == "--sheet-id" and i + 1 < len(sys.argv):
            sheet_id = sys.argv[i + 1]

    if not dry_run and not apply:
        print("Укажи режим: --dry-run или --apply")
        sys.exit(1)

    # Таблица
    if not sheet_id and os.path.exists(SHEET_ID_PATH):
        with open(SHEET_ID_PATH) as f:
            sheet_id = f.read().strip()

    if not sheet_id:
        print("Не найден ID таблицы. Укажи --sheet-id или запусти сначала youtube_comments_to_sheets.py")
        sys.exit(1)

    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)

    print(f"Таблица: https://docs.google.com/spreadsheets/d/{sheet_id}")
    rows = read_sheet(sheets, sheet_id)
    print(f"Всего строк: {len(rows)}\n")

    # Собираем задачи
    to_reply = []
    to_delete = []

    for i, row in enumerate(rows):
        if not is_approved(row):
            continue

        # Пропускаем уже обработанные
        status = get_cell(row, 10)  # Колонка K (index 10)
        if status:
            continue

        action = get_cell(row, COL_ACTION).strip().lower()
        comment_id = get_cell(row, COL_COMMENT_ID)

        if not comment_id:
            continue

        if action == "удалить":
            to_delete.append({
                "row_index": i,
                "comment_id": comment_id,
                "author": get_cell(row, COL_AUTHOR),
                "text": get_cell(row, COL_COMMENT)[:60],
            })
        elif action == "ответить":
            reply_text = get_reply_text(row)
            if not reply_text:
                print(f"  [SKIP] Строка {i+2}: нет текста ответа для @{get_cell(row, COL_AUTHOR)}")
                continue
            to_reply.append({
                "row_index": i,
                "comment_id": comment_id,
                "author": get_cell(row, COL_AUTHOR),
                "video": get_cell(row, COL_VIDEO),
                "reply_text": reply_text,
                "is_edited": bool(get_cell(row, COL_EDIT).strip()),
            })

    # Сводка
    print(f"К ответу: {len(to_reply)}")
    print(f"К удалению: {len(to_delete)}")
    print()

    if not to_reply and not to_delete:
        print("Нет одобренных действий.")
        return

    # Dry run
    if dry_run:
        print("=== DRY RUN ===\n")
        for r in to_reply:
            edited = " [правка]" if r["is_edited"] else ""
            print(f"  ОТВЕТИТЬ @{r['author']}{edited}:")
            print(f"    {r['reply_text'][:100]}...")
            print()
        for d in to_delete:
            print(f"  УДАЛИТЬ @{d['author']}: {d['text']}...")
        print(f"\nДля применения запусти с --apply")
        return

    # Apply
    print("=== ПРИМЕНЯЮ ===\n")
    ensure_status_header(sheets, sheet_id)

    replied = []
    deleted = []
    videos_with_replies = set()
    today = datetime.now().strftime("%Y-%m-%d")

    for r in to_reply:
        try:
            post_reply(yt, r["comment_id"], r["reply_text"])
            status = f"отвечено {today}"
            update_sheet_status(sheets, sheet_id, r["row_index"], status)
            replied.append(r)
            videos_with_replies.add(r["video"])
            edited = " [правка]" if r["is_edited"] else ""
            print(f"  OK ответ @{r['author']}{edited}")
        except Exception as e:
            print(f"  ОШИБКА ответ @{r['author']}: {e}")

    for d in to_delete:
        try:
            delete_comment(yt, d["comment_id"])
            status = f"удалено {today}"
            update_sheet_status(sheets, sheet_id, d["row_index"], status)
            deleted.append(d)
            print(f"  OK удалён @{d['author']}")
        except Exception as e:
            print(f"  ОШИБКА удаление @{d['author']}: {e}")

    # Лог
    print(f"\nОтвечено: {len(replied)}, Удалено: {len(deleted)}")

    if replied or deleted:
        leads = []  # Лиды определяются в skill при классификации
        update_comments_log(replied, deleted, videos_with_replies, leads)


if __name__ == "__main__":
    main()
