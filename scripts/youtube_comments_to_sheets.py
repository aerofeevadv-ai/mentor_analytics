"""
YouTube Comments → Google Sheets.

Парсит комментарии без ответа автора через YouTube API,
заливает в Google Sheets для ревью.

Запуск:
    python3 scripts/youtube_comments_to_sheets.py
    python3 scripts/youtube_comments_to_sheets.py --days 30
    python3 scripts/youtube_comments_to_sheets.py --sheet-id EXISTING_SHEET_ID

Таблица создаётся автоматически (или обновляется существующая).
ID таблицы сохраняется в .secrets/comments_sheet_id.txt
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
SHEET_ID_PATH = os.path.join(BASE_DIR, ".secrets", "comments_sheet_id.txt")
CHANNEL_ID = "UC12sp7LmvlgMufTDV18oNuw"
# Личный аккаунт Алексея — тоже считается «ответом автора»
PERSONAL_CHANNEL_ID = "UCiN9Mg6tU3Q-wiKpRoeiTKQ"
AUTHOR_IDS = {CHANNEL_ID, PERSONAL_CHANNEL_ID}

HEADERS = [
    "Видео", "Автор", "Комментарий", "Лайки", "Тональность",
    "Действие", "Предложенный ответ", "Правка", "Апрув", "comment_id",
]


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


def get_channel_videos(yt):
    """Получить все видео канала."""
    videos = []
    page_token = None
    while True:
        resp = yt.search().list(
            part="id,snippet",
            channelId=CHANNEL_ID,
            type="video",
            maxResults=50,
            pageToken=page_token,
            order="date",
        ).execute()
        for item in resp.get("items", []):
            videos.append({
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "published": item["snippet"]["publishedAt"],
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return videos


def check_author_reply_full(yt, parent_id):
    """Проверить все ответы на комментарий (для тредов с >5 ответами)."""
    page_token = None
    while True:
        resp = yt.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            pageToken=page_token,
            textFormat="plainText",
        ).execute()
        for item in resp.get("items", []):
            if item["snippet"].get("authorChannelId", {}).get("value") in AUTHOR_IDS:
                return True
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return False


def get_comments_for_video(yt, video_id, video_title):
    """Получить комментарии для видео без ответа автора."""
    comments = []
    page_token = None
    while True:
        try:
            resp = yt.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                textFormat="plainText",
            ).execute()
        except Exception as e:
            if "commentsDisabled" in str(e):
                break
            raise

        for item in resp.get("items", []):
            top = item["snippet"]["topLevelComment"]
            snippet = top["snippet"]
            total_replies = item["snippet"].get("totalReplyCount", 0)

            has_author_reply = False
            if item.get("replies"):
                for reply in item["replies"]["comments"]:
                    r_snippet = reply["snippet"]
                    if r_snippet.get("authorChannelId", {}).get("value") in AUTHOR_IDS:
                        has_author_reply = True
                        break

            # API возвращает макс 5 ответов в replies.comments.
            # Если ответов больше и автор не найден — проверяем через comments().list()
            if not has_author_reply and total_replies > len(item.get("replies", {}).get("comments", [])):
                has_author_reply = check_author_reply_full(yt, top["id"])

            if not has_author_reply:
                comments.append({
                    "comment_id": top["id"],
                    "video_id": video_id,
                    "video_title": video_title,
                    "author": snippet.get("authorDisplayName", ""),
                    "text": snippet.get("textDisplay", ""),
                    "likes": snippet.get("likeCount", 0),
                    "date": snippet.get("publishedAt", "")[:10],
                })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return comments


def fetch_all_fresh_comments(yt, days_filter=None):
    """Получить все комментарии без ответа автора."""
    print("Получаю список видео канала...")
    videos = get_channel_videos(yt)
    print(f"Найдено {len(videos)} видео\n")

    all_comments = []
    for v in videos:
        comments = get_comments_for_video(yt, v["id"], v["title"])
        all_comments.extend(comments)
        if comments:
            print(f"  {v['title'][:50]}... | {len(comments)} без ответа")

    if days_filter:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_filter)).strftime("%Y-%m-%d")
        all_comments = [c for c in all_comments if c["date"] >= cutoff]
        print(f"\nФильтр: последние {days_filter} дней (с {cutoff})")

    # Сортировка: больше лайков сначала, потом свежие
    all_comments.sort(key=lambda c: (-c["likes"], c["date"]))

    print(f"\nИтого без ответа: {len(all_comments)}")
    return all_comments


def create_spreadsheet(sheets):
    """Создать новую таблицу."""
    today = datetime.now().strftime("%Y-%m-%d")
    body = {
        "properties": {"title": f"YT Комментарии — {today}"},
        "sheets": [{
            "properties": {
                "title": "Комментарии",
                "gridProperties": {"frozenRowCount": 1},
            },
        }],
    }
    result = sheets.spreadsheets().create(body=body).execute()
    sheet_id = result["spreadsheetId"]

    # Сохраняем ID
    with open(SHEET_ID_PATH, "w") as f:
        f.write(sheet_id)

    print(f"Создана таблица: https://docs.google.com/spreadsheets/d/{sheet_id}")
    return sheet_id


def format_sheet(sheets, spreadsheet_id):
    """Форматирование: ширина колонок, чекбоксы, скрытие comment_id."""
    # Получаем sheetId
    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = meta["sheets"][0]["properties"]["sheetId"]

    requests = [
        # Ширина колонок
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 200}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
            "properties": {"pixelSize": 120}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3},
            "properties": {"pixelSize": 350}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4},
            "properties": {"pixelSize": 60}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5},
            "properties": {"pixelSize": 120}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6},
            "properties": {"pixelSize": 100}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7},
            "properties": {"pixelSize": 350}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 7, "endIndex": 8},
            "properties": {"pixelSize": 350}, "fields": "pixelSize",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 8, "endIndex": 9},
            "properties": {"pixelSize": 70}, "fields": "pixelSize",
        }},
        # Скрыть колонку comment_id (J)
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 9, "endIndex": 10},
            "properties": {"hiddenByUser": True}, "fields": "hiddenByUser",
        }},
        # Заголовок жирным
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
            }},
            "fields": "userEnteredFormat(textFormat,backgroundColor)",
        }},
        # Перенос текста в колонках Комментарий, Предложенный ответ, Правка
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 1000,
                       "startColumnIndex": 2, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
            "fields": "userEnteredFormat.wrapStrategy",
        }},
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 1000,
                       "startColumnIndex": 6, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
            "fields": "userEnteredFormat.wrapStrategy",
        }},
        # Data validation: Действие — dropdown
        {"setDataValidation": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 1000,
                       "startColumnIndex": 5, "endColumnIndex": 6},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "ответить"},
                        {"userEnteredValue": "удалить"},
                        {"userEnteredValue": "игнор"},
                    ],
                },
                "showCustomUi": True,
                "strict": True,
            },
        }},
        # Data validation: Апрув — checkbox
        {"setDataValidation": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 1000,
                       "startColumnIndex": 8, "endColumnIndex": 9},
            "rule": {
                "condition": {"type": "BOOLEAN"},
                "showCustomUi": True,
            },
        }},
    ]

    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def upload_to_sheets(sheets, spreadsheet_id, comments):
    """Залить комментарии в таблицу."""
    rows = [HEADERS]
    for c in comments:
        rows.append([
            c["video_title"],
            c["author"],
            c["text"],
            c["likes"],
            "",  # Тональность — заполняется в SKILL
            "",  # Действие — заполняется в SKILL
            "",  # Предложенный ответ — заполняется в SKILL
            "",  # Правка — пустая для Алексея
            False,  # Апрув — чекбокс
            c["comment_id"],
        ])

    # Очистить и записать
    sheets.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range="Комментарии!A:J",
    ).execute()

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Комментарии!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()

    print(f"Загружено {len(comments)} комментариев в таблицу")


def main():
    # Аргументы
    days_filter = None
    sheet_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            days_filter = int(sys.argv[i + 1])
        if arg == "--sheet-id" and i + 1 < len(sys.argv):
            sheet_id = sys.argv[i + 1]

    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)

    # Парсим комментарии
    comments = fetch_all_fresh_comments(yt, days_filter)

    if not comments:
        print("Нет новых комментариев без ответа!")
        return

    # Таблица: создаём или используем существующую
    if not sheet_id and os.path.exists(SHEET_ID_PATH):
        with open(SHEET_ID_PATH) as f:
            sheet_id = f.read().strip()
        print(f"Используем существующую таблицу: {sheet_id}")

    if not sheet_id:
        sheet_id = create_spreadsheet(sheets)
        format_sheet(sheets, sheet_id)
    else:
        # Проверяем доступ к существующей таблице
        try:
            sheets.spreadsheets().get(spreadsheetId=sheet_id).execute()
        except Exception:
            print("Таблица недоступна, создаю новую...")
            sheet_id = create_spreadsheet(sheets)
            format_sheet(sheets, sheet_id)

    upload_to_sheets(sheets, sheet_id, comments)

    # Сохраняем JSON для skill (классификация + черновики)
    output_path = os.path.join(BASE_DIR, ".secrets", "fresh_comments.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"JSON сохранён: {output_path}")

    print(f"\nСсылка: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"Sheet ID: {sheet_id}")


if __name__ == "__main__":
    main()
