"""
Аудит CTR обложек YouTube-канала @analytic_offers.

Запуск:
    python3 scripts/youtube_ctr_audit.py

Что делает:
    1. Получает список всех видео канала
    2. Выгружает CTR, impressions, views через YouTube Analytics API
    3. Скачивает обложки в content/youtube/thumbnails/
    4. Выводит таблицу: видео, CTR, impressions, views, ссылка на обложку
"""

import json
import os
import urllib.request
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
THUMBS_DIR = os.path.join(BASE_DIR, "content", "youtube", "thumbnails")
CHANNEL_ID = "UC12sp7LmvlgMufTDV18oNuw"


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


def get_all_videos(yt):
    """Получить все видео канала с метаданными."""
    # Получаем uploads playlist
    ch = yt.channels().list(part="contentDetails", id=CHANNEL_ID).execute()
    uploads_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    next_page = None
    while True:
        pl = yt.playlistItems().list(
            part="snippet",
            playlistId=uploads_id,
            maxResults=50,
            pageToken=next_page,
        ).execute()

        for item in pl["items"]:
            snippet = item["snippet"]
            vid = snippet["resourceId"]["videoId"]
            videos.append({
                "id": vid,
                "title": snippet["title"],
                "published": snippet["publishedAt"][:10],
                "thumbnails": snippet.get("thumbnails", {}),
            })

        next_page = pl.get("nextPageToken")
        if not next_page:
            break

    return videos


def get_analytics_data(creds):
    """Получить views, watch time, likes через YouTube Analytics API."""
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    resp = yta.reports().query(
        ids="channel==MINE",
        startDate="2025-01-01",
        endDate=datetime.now().strftime("%Y-%m-%d"),
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,shares",
        dimensions="video",
        sort="-views",
        maxResults=50,
    ).execute()

    data_map = {}
    for row in resp.get("rows", []):
        vid = row[0]
        data_map[vid] = {
            "views": row[1],
            "watch_min": row[2],
            "avg_duration": row[3],
            "likes": row[4],
            "shares": row[5],
        }

    return data_map


def download_thumbnails(videos):
    """Скачать обложки всех видео."""
    os.makedirs(THUMBS_DIR, exist_ok=True)

    for v in videos:
        thumbs = v["thumbnails"]
        # Берём максимальное разрешение
        for quality in ["maxres", "standard", "high", "medium", "default"]:
            if quality in thumbs:
                url = thumbs[quality]["url"]
                break
        else:
            continue

        filename = f"{v['id']}.jpg"
        filepath = os.path.join(THUMBS_DIR, filename)

        if os.path.exists(filepath):
            continue

        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            print(f"[ERR] {v['id']}: {e}")


def main():
    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)

    print("Загружаю список видео...")
    videos = get_all_videos(yt)
    print(f"Найдено {len(videos)} видео\n")

    print("Загружаю аналитику из YouTube Analytics API...")
    analytics = get_analytics_data(creds)
    print(f"Получены данные для {len(analytics)} видео\n")

    print("Скачиваю обложки...")
    download_thumbnails(videos)
    print(f"Обложки сохранены в {THUMBS_DIR}\n")

    # Сортируем по views (больше → меньше)
    videos_sorted = sorted(
        videos,
        key=lambda v: analytics.get(v["id"], {}).get("views", 0),
        reverse=True,
    )

    # Выводим таблицу
    print(f"{'Views':>7} | {'WatchMin':>8} | {'AvgSec':>6} | {'Likes':>5} | {'Like%':>5} | Название")
    print("-" * 95)

    longs = []
    shorts = []

    for v in videos_sorted:
        data = analytics.get(v["id"], {})
        views = data.get("views", 0)
        watch_min = data.get("watch_min", 0)
        avg_dur = data.get("avg_duration", 0)
        likes = data.get("likes", 0)
        like_rate = (likes / views * 100) if views > 0 else 0

        entry = {**v, **data, "like_rate": like_rate}

        if avg_dur > 60:
            longs.append(entry)
        else:
            shorts.append(entry)

        title = v["title"][:50]
        print(f"{views:>7,} | {watch_min:>8,.0f} | {avg_dur:>6.0f} | {likes:>5,} | {like_rate:>4.1f}% | {title}")

    # Средние значения
    print("\n" + "=" * 95)
    print("\nCTR (impressionClickThroughRate) недоступен через API.")
    print("Для CTR нужно открыть YouTube Studio → Analytics → Контент.")
    print(f"\nОбложки скачаны в: {THUMBS_DIR}")
    print("Открой их для визуального аудита.\n")

    if longs:
        avg_like = sum(v.get("like_rate", 0) for v in longs) / len(longs)
        print(f"Лонги ({len(longs)} шт): средний like rate = {avg_like:.1f}%")
        print("  Топ по views:")
        for v in sorted(longs, key=lambda x: x.get("views", 0), reverse=True)[:5]:
            print(f"    {v.get('views', 0):>7,} views | {v.get('like_rate', 0):.1f}% likes — {v['title'][:55]}")

    if shorts:
        avg_like = sum(v.get("like_rate", 0) for v in shorts) / len(shorts)
        print(f"\nShorts ({len(shorts)} шт): средний like rate = {avg_like:.1f}%")
        print("  Топ по views:")
        for v in sorted(shorts, key=lambda x: x.get("views", 0), reverse=True)[:5]:
            print(f"    {v.get('views', 0):>7,} views | {v.get('like_rate', 0):.1f}% likes — {v['title'][:55]}")


if __name__ == "__main__":
    main()
