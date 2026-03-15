"""
Сбор свежих комментариев YouTube-канала @analytic_offers.

Забирает все комментарии без ответа автора.
Сохраняет в .secrets/fresh_comments.json

Запуск:
    python3 .claude/skills/youtube-comments/scripts/fetch_comments.py
    python3 .claude/skills/youtube-comments/scripts/fetch_comments.py --days 30  # только за последние 30 дней
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))  # -> mentor_analytics/
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
OUTPUT_PATH = os.path.join(BASE_DIR, ".secrets", "fresh_comments.json")
CHANNEL_ID = "UC12sp7LmvlgMufTDV18oNuw"
PERSONAL_CHANNEL_ID = "UCiN9Mg6tU3Q-wiKpRoeiTKQ"
AUTHOR_IDS = {CHANNEL_ID, PERSONAL_CHANNEL_ID}


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
    """Получить все комментарии для видео, включая ответы."""
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

            # Проверяем есть ли ответ автора
            has_author_reply = False
            replies_data = []
            if item.get("replies"):
                for reply in item["replies"]["comments"]:
                    r_snippet = reply["snippet"]
                    if r_snippet.get("authorChannelId", {}).get("value") in AUTHOR_IDS:
                        has_author_reply = True
                    replies_data.append({
                        "id": reply["id"],
                        "author": r_snippet.get("authorDisplayName", ""),
                        "text": r_snippet.get("textDisplay", ""),
                        "likes": r_snippet.get("likeCount", 0),
                        "date": r_snippet.get("publishedAt", "")[:10],
                        "is_author": r_snippet.get("authorChannelId", {}).get("value") in AUTHOR_IDS,
                    })

            # API возвращает макс 5 ответов. Если больше — проверяем полностью
            if not has_author_reply and total_replies > len(replies_data):
                has_author_reply = check_author_reply_full(yt, top["id"])

            comments.append({
                "comment_id": top["id"],
                "video_id": video_id,
                "video_title": video_title,
                "author": snippet.get("authorDisplayName", ""),
                "text": snippet.get("textDisplay", ""),
                "likes": snippet.get("likeCount", 0),
                "date": snippet.get("publishedAt", "")[:10],
                "has_author_reply": has_author_reply,
                "reply_count": total_replies,
                "replies": replies_data,
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return comments


def main():
    # Парсим аргументы
    days_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            days_filter = int(sys.argv[i + 1])

    yt = get_youtube_client()

    print("Получаю список видео канала...")
    videos = get_channel_videos(yt)
    print(f"Найдено {len(videos)} видео\n")

    all_comments = []
    for v in videos:
        comments = get_comments_for_video(yt, v["id"], v["title"])
        all_comments.extend(comments)
        count_new = sum(1 for c in comments if not c["has_author_reply"])
        if comments:
            print(f"  {v['title'][:50]}... | {len(comments)} комм, {count_new} без ответа")

    # Фильтруем: только без ответа автора
    fresh = [c for c in all_comments if not c["has_author_reply"]]

    # Фильтр по дням если указан
    if days_filter:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_filter)).strftime("%Y-%m-%d")
        fresh = [c for c in fresh if c["date"] >= cutoff]
        print(f"\nФильтр: только за последние {days_filter} дней (с {cutoff})")

    # Сортируем: сначала больше лайков, потом свежие
    fresh.sort(key=lambda c: (-c["likes"], c["date"]), reverse=False)

    # Сохраняем
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(fresh, f, ensure_ascii=False, indent=2)

    # Сводка
    total_all = len(all_comments)
    total_fresh = len(fresh)
    total_with_reply = total_all - sum(1 for c in all_comments if not c["has_author_reply"])

    videos_with_fresh = set(c["video_id"] for c in fresh)
    top_liked = sorted(fresh, key=lambda c: -c["likes"])[:5]

    print(f"\n{'='*50}")
    print(f"СВОДКА")
    print(f"{'='*50}")
    print(f"Всего комментариев: {total_all}")
    print(f"С ответом автора: {total_with_reply}")
    print(f"Без ответа (свежие): {total_fresh}")
    print(f"Видео с неотвеченными: {len(videos_with_fresh)}")
    print(f"\nТоп по лайкам (без ответа):")
    for c in top_liked:
        print(f"  [{c['likes']} likes] @{c['author']}: {c['text'][:60]}...")
    print(f"\nСохранено в: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
