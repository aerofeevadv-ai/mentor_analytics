"""
Скачивание референсов обложек YouTube с топовых IT-каналов.

Запуск:
    python3 scripts/youtube_fetch_references.py

Что делает:
    1. Берёт список IT/аналитика YouTube-каналов
    2. Для каждого канала получает топ-видео по просмотрам
    3. Скачивает обложки в content/youtube/references/
    4. Сохраняет метаданные в references_meta.json
"""

import json
import os
import time
import urllib.request
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
REFS_DIR = os.path.join(BASE_DIR, "content", "youtube", "references")
META_PATH = os.path.join(REFS_DIR, "references_meta.json")

# Каналы для сбора референсов: handle → описание
CHANNELS = {
    # === Russian IT / Analytics / Career ===
    "@SergeyNemchinskiy": "RU IT career, bold text + talking head",
    "@t0digital": "RU tech (Диджитализируй), neon/dark style",
    "@itbeard": "RU IT podcast (АйТиБорода), split-screen guests",
    "@ArtemShumeiko": "RU Python dev, bright gradients + code",
    "@winderton": "RU CS, dark hacker aesthetic",
    "@HowdyhoNet": "RU programming (Хауди Хо), meme-like thumbnails",
    "@VladilenMinin": "RU frontend, clean educational style",
    # === English Data / Analytics ===
    "@AlexTheAnalyst": "EN data career, branded green thumbnails",
    "@LukeBarousse": "EN data nerd, data viz in thumbnails",
    "@Thuvu5": "EN data analytics, storytelling style",
    "@KenJee1": "EN data science, blue tones consistent",
    "@statquest": "EN statistics (StatQuest), hand-drawn iconic style",
    "@ClementMihailescu": "EN AlgoExpert, salary/company hooks",
    "@TinaHuang1": "EN tech career, cinematic quality",
    # === English Tech / Programming (thumbnail masters) ===
    "@Fireship": "EN tech, gold standard minimalist logos",
    "@NetworkChuck": "EN networking/hacking, high-energy face + props",
    "@t3dotgg": "EN React (Theo), dramatic hot-take style",
    "@ThePrimeagen": "EN programming, reaction-style thumbnails",
    "@TraversyMedia": "EN web dev tutorials, dark gradient + logos",
    "@WebDevSimplified": "EN web dev, clean red/dark scheme",
    "@TechWithTim": "EN Python tutorials, bright high-contrast",
    # ForrestKnight is in career section below
    # === Career / Tech Advice ===
    "@KevinPowell": "EN CSS, design-forward minimal thumbnails",
    "@NeetCode": "EN leetcode/algorithms, clean minimal + code",
    "@BroCodez": "EN programming, meme humor + bold text",
    "@ForrestKnight": "EN software eng, cinematic day-in-life",
    "@freecodecamp": "EN coding education, clean course-style",
    "@JoshuaFluke1": "EN tech career, controversy-driven shocked face",
}

# Fallback: прямые channel IDs для каналов, где handle может не резолвиться
CHANNEL_IDS_FALLBACK = {
    "@SergeyNemchinskiy": "UC1s1OsWNYDFpXBPmqfROoag",
    "@t0digital": "UC9MK8SybZcrHR3CUV4NMy2g",
    "@itbeard": "UCeObZv89Stb2xLtjLJ0De3Q",
    "@winderton": "UC4omkhNHsYLagT1o6hnmKQw",
    "@statquest": "UCtYLUTtgS3k1Fg4y5tAhLbw",
    "@ForrestKnight": "UC2WHjPDvbE6O328n17ZGcfg",
    "@freecodecamp": "UC8butISFwT-Wl7EV0hUK0BQ",
    "@JoshuaFluke1": "UC-91UA-Xy2Cvb98deRXuggA",
}


def get_credentials():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Сохраняем обновлённый токен
        token_data["token"] = creds.token
        with open(TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)
    return creds


def resolve_channel(yt, handle):
    """Resolve @handle to channel ID + stats."""
    # Попробовать через forHandle
    try:
        resp = yt.channels().list(
            part="snippet,statistics,contentDetails",
            forHandle=handle.lstrip("@"),
        ).execute()
        if resp.get("items"):
            item = resp["items"][0]
            return {
                "id": item["id"],
                "title": item["snippet"]["title"],
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
            }
    except Exception:
        pass

    # Fallback: прямой channel ID
    if handle in CHANNEL_IDS_FALLBACK:
        cid = CHANNEL_IDS_FALLBACK[handle]
        try:
            resp = yt.channels().list(
                part="snippet,statistics,contentDetails",
                id=cid,
            ).execute()
            if resp.get("items"):
                item = resp["items"][0]
                return {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                    "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
                }
        except Exception:
            pass

    # Fallback: поиск по имени
    try:
        resp = yt.search().list(
            part="snippet",
            q=handle.lstrip("@"),
            type="channel",
            maxResults=1,
        ).execute()
        if resp.get("items"):
            cid = resp["items"][0]["snippet"]["channelId"]
            resp2 = yt.channels().list(
                part="snippet,statistics,contentDetails",
                id=cid,
            ).execute()
            if resp2.get("items"):
                item = resp2["items"][0]
                return {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                    "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
                }
    except Exception:
        pass

    return None


def get_top_videos(yt, channel_info, max_videos=3):
    """Получить топ видео канала по просмотрам (только лонги)."""
    uploads_id = channel_info["uploads_playlist"]

    # Получаем все видео из uploads playlist
    video_ids = []
    next_page = None
    try:
        while len(video_ids) < 50:
            pl = yt.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_id,
                maxResults=50,
                pageToken=next_page,
            ).execute()

            for item in pl["items"]:
                video_ids.append(item["contentDetails"]["videoId"])

            next_page = pl.get("nextPageToken")
            if not next_page:
                break
    except Exception as e:
        print(f"  [ERR] playlist access: {e}")
        return []

    if not video_ids:
        return []

    # Получаем статистику и детали для всех видео (батчами по 50)
    all_videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch),
        ).execute()

        for item in resp.get("items", []):
            duration = item["contentDetails"]["duration"]
            # Фильтруем shorts (< 61 секунды)
            if is_short(duration):
                continue

            views = int(item["statistics"].get("viewCount", 0))
            subs = channel_info["subscribers"]
            # Views-to-subs ratio как прокси CTR
            vsr = views / subs if subs > 0 else 0

            thumbnails = item["snippet"].get("thumbnails", {})
            # Лучшее качество обложки
            thumb_url = None
            for q in ["maxres", "standard", "high", "medium", "default"]:
                if q in thumbnails:
                    thumb_url = thumbnails[q]["url"]
                    break

            all_videos.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "views": views,
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0)),
                "published": item["snippet"]["publishedAt"][:10],
                "duration": duration,
                "thumbnail_url": thumb_url,
                "views_to_subs": round(vsr, 2),
            })

    # Сортируем по views-to-subs ratio (прокси для CTR)
    all_videos.sort(key=lambda v: v["views_to_subs"], reverse=True)

    return all_videos[:max_videos]


def is_short(duration_iso):
    """Проверить, является ли видео shorts (< 61 сек) по ISO 8601 duration."""
    # PT1M30S, PT45S, PT1H2M3S
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_iso)
    if not m:
        return False
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    total = hours * 3600 + minutes * 60 + seconds
    return total <= 60


def download_thumbnail(video_id, url, channel_handle):
    """Скачать обложку."""
    os.makedirs(REFS_DIR, exist_ok=True)

    safe_handle = channel_handle.lstrip("@").replace("/", "_")
    filename = f"{safe_handle}_{video_id}.jpg"
    filepath = os.path.join(REFS_DIR, filename)

    if os.path.exists(filepath):
        return filename

    try:
        urllib.request.urlretrieve(url, filepath)
        return filename
    except Exception as e:
        print(f"  [ERR] download {video_id}: {e}")
        return None


def main():
    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)

    os.makedirs(REFS_DIR, exist_ok=True)

    all_references = []
    failed_channels = []

    for idx, (handle, description) in enumerate(CHANNELS.items(), 1):
        print(f"\n[{idx}/{len(CHANNELS)}] {handle} — {description}")

        try:
            # Resolve channel
            channel_info = resolve_channel(yt, handle)
            if not channel_info:
                print(f"  ❌ Не удалось найти канал")
                failed_channels.append(handle)
                continue

            print(f"  ✅ {channel_info['title']} ({channel_info['subscribers']:,} subs)")

            # Get top videos
            top_videos = get_top_videos(yt, channel_info, max_videos=3)
            if not top_videos:
                print(f"  ⚠️ Нет подходящих видео")
                continue
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            failed_channels.append(handle)
            continue

        for v in top_videos:
            # Download thumbnail
            filename = None
            if v["thumbnail_url"]:
                filename = download_thumbnail(v["video_id"], v["thumbnail_url"], handle)

            ref = {
                "channel_handle": handle,
                "channel_name": channel_info["title"],
                "channel_subs": channel_info["subscribers"],
                "channel_description": description,
                "video_id": v["video_id"],
                "title": v["title"],
                "views": v["views"],
                "likes": v["likes"],
                "views_to_subs": v["views_to_subs"],
                "published": v["published"],
                "thumbnail_file": filename,
                "thumbnail_url": v["thumbnail_url"],
                "youtube_url": f"https://youtube.com/watch?v={v['video_id']}",
            }
            all_references.append(ref)
            print(f"  📸 {v['views']:>10,} views (VSR {v['views_to_subs']:.1f}x) | {v['title'][:50]}")

        # Пауза между каналами (rate limiting)
        time.sleep(0.5)

    # Сортируем все по views_to_subs
    all_references.sort(key=lambda r: r["views_to_subs"], reverse=True)

    # Сохраняем метаданные
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(all_references, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print(f"Готово! Собрано {len(all_references)} референсов с {len(CHANNELS) - len(failed_channels)} каналов")
    print(f"Обложки: {REFS_DIR}")
    print(f"Метаданные: {META_PATH}")

    if failed_channels:
        print(f"\n⚠️ Не удалось найти {len(failed_channels)} каналов:")
        for ch in failed_channels:
            print(f"  - {ch}")

    # Топ-10 по VSR
    print(f"\n🏆 ТОП-10 по Views-to-Subs Ratio (прокси CTR):")
    print(f"{'VSR':>6} | {'Views':>10} | {'Channel':>20} | Title")
    print("-" * 90)
    for ref in all_references[:10]:
        print(f"{ref['views_to_subs']:>5.1f}x | {ref['views']:>10,} | {ref['channel_name'][:20]:>20} | {ref['title'][:40]}")


if __name__ == "__main__":
    main()
