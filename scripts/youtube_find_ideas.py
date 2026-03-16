"""
Поиск идей для YouTube-видео: анализ виральных видео конкурентов.

Два режима:
    # Discovery: сканировать конкурентов, найти топ виральных видео
    python3 scripts/youtube_find_ideas.py --discover [--months 6] [--max-duration 25] [--top 5]

    # Topic: найти лучшие видео по теме
    python3 scripts/youtube_find_ideas.py --topic "продуктовые метрики" [--max-duration 25] [--top 5]

Virality Score:
    score = VSR_norm * 0.30 + VPD_norm * 0.30 + engagement_norm * 0.15
            + freshness * 0.15 + duration_fit * 0.10
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")
CACHE_PATH = os.path.join(BASE_DIR, ".secrets", "ideas_cache.json")
IDEAS_DIR = os.path.join(BASE_DIR, "content", "youtube", "ideas")

# Каналы для discovery (расширенный список)
CHANNELS = {
    # === Russian IT / Analytics / Career ===
    "@SergeyNemchinskiy": "RU IT career",
    "@t0digital": "RU tech (Диджитализируй)",
    "@itbeard": "RU IT podcast (АйТиБорода)",
    "@ArtemShumeiko": "RU Python dev",
    "@winderton": "RU CS",
    "@HowdyhoNet": "RU programming (Хауди Хо)",
    "@VladilenMinin": "RU frontend",
    # === Russian Analytics specific ===
    "@kaborche": "RU аналитика (Karpov.Courses)",
    "@datalearn_io": "RU data engineering (Data Learn)",
    "@gleb_mikhailov": "RU аналитика данных",
    "@aisearch_ru": "RU data science",
    "@selfedu_rus": "RU Python + ML",
    # === English Data / Analytics ===
    "@AlexTheAnalyst": "EN data career",
    "@LukeBarousse": "EN data nerd",
    "@Thuvu5": "EN data analytics",
    "@KenJee1": "EN data science",
    "@statquest": "EN statistics (StatQuest)",
    "@ClementMihailescu": "EN AlgoExpert",
    "@TinaHuang1": "EN tech career",
    # === English Tech / Programming ===
    "@Fireship": "EN tech",
    "@NetworkChuck": "EN networking/hacking",
    "@t3dotgg": "EN React (Theo)",
    "@ThePrimeagen": "EN programming",
    "@TraversyMedia": "EN web dev tutorials",
    "@WebDevSimplified": "EN web dev",
    "@TechWithTim": "EN Python tutorials",
    # === Career / Tech Advice ===
    "@NeetCode": "EN leetcode/algorithms",
    "@BroCodez": "EN programming",
    "@ForrestKnight": "EN software eng",
    "@freecodecamp": "EN coding education",
    "@JoshuaFluke1": "EN tech career",
}

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
        token_data["token"] = creds.token
        with open(TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)
    return creds


def resolve_channel(yt, handle):
    """Resolve @handle to channel ID + stats."""
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


def parse_duration_seconds(duration_iso):
    """Parse ISO 8601 duration to seconds."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_iso)
    if not m:
        return 0
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_duration(total_seconds):
    """Format seconds to M:SS or H:MM:SS."""
    if total_seconds <= 0:
        return "0:00"
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def days_since(date_str):
    """Days since ISO date string."""
    pub = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return max((now - pub).days, 1)


def calc_freshness(days):
    """Freshness score based on age."""
    if days < 90:
        return 1.0
    if days < 180:
        return 0.7
    if days < 365:
        return 0.4
    return 0.2


def calc_duration_fit(total_seconds):
    """Duration fit score."""
    minutes = total_seconds / 60
    if 5 <= minutes <= 15:
        return 1.0
    if 15 < minutes <= 25:
        return 0.7
    if 25 < minutes <= 40:
        return 0.3
    return 0.0


def min_max_normalize(values):
    """Min-max normalize a list of floats. Returns list of normalized values."""
    if not values:
        return []
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def get_channel_videos(yt, channel_info, max_duration_min):
    """Get filtered videos from a channel's uploads playlist."""
    uploads_id = channel_info["uploads_playlist"]
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
        print(f"  [ERR] playlist: {e}")
        return []

    if not video_ids:
        return []

    return enrich_videos(yt, video_ids, channel_info, max_duration_min)


def enrich_videos(yt, video_ids, channel_info_or_none, max_duration_min):
    """Fetch video details, filter, return enriched list.

    If channel_info_or_none is None, fetch channel stats per video.
    """
    videos = []
    # Fetch video details in batches of 50
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch),
        ).execute()

        for item in resp.get("items", []):
            duration_sec = parse_duration_seconds(item["contentDetails"]["duration"])

            # Filter shorts
            if duration_sec <= 60:
                continue
            # Filter too long
            if duration_sec > max_duration_min * 60:
                continue

            views = int(item["statistics"].get("viewCount", 0))
            # Filter low views
            if views < 1000:
                continue

            likes = int(item["statistics"].get("likeCount", 0))
            comments = int(item["statistics"].get("commentCount", 0))
            published = item["snippet"]["publishedAt"]

            videos.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "channel_id": item["snippet"]["channelId"],
                "channel_title": item["snippet"].get("channelTitle", ""),
                "views": views,
                "likes": likes,
                "comments": comments,
                "published": published[:10],
                "published_iso": published,
                "duration_sec": duration_sec,
                "duration_fmt": format_duration(duration_sec),
                "_channel_info": channel_info_or_none,
            })

    # If no channel_info, resolve subscribers per unique channel
    if channel_info_or_none is None:
        channel_ids = list({v["channel_id"] for v in videos})
        subs_map = {}
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i:i + 50]
            try:
                resp = yt.channels().list(
                    part="statistics",
                    id=",".join(batch),
                ).execute()
                for item in resp.get("items", []):
                    subs_map[item["id"]] = int(
                        item["statistics"].get("subscriberCount", 0)
                    )
            except Exception:
                pass

        for v in videos:
            v["subscribers"] = subs_map.get(v["channel_id"], 0)
    else:
        for v in videos:
            v["subscribers"] = channel_info_or_none["subscribers"]
            v["channel_title"] = channel_info_or_none["title"]

    # Add days_age and clean up internal field
    for v in videos:
        v.pop("_channel_info", None)
        v["days_age"] = days_since(v["published_iso"])

    return videos


def score_videos(videos):
    """Calculate virality score for each video. Returns sorted list."""
    if not videos:
        return []

    # Raw metrics
    vsrs = []
    vpds = []
    engagements = []
    for v in videos:
        subs = v["subscribers"]
        vsr = v["views"] / subs if subs > 0 else 0
        days = days_since(v["published_iso"])
        vpd = v["views"] / days
        eng = (v["likes"] + v["comments"]) / v["views"] if v["views"] > 0 else 0

        v["vsr"] = round(vsr, 2)
        v["vpd"] = round(vpd, 1)
        v["engagement"] = round(eng, 4)
        v["days_age"] = days

        vsrs.append(vsr)
        vpds.append(vpd)
        engagements.append(eng)

    # Normalize
    vsrs_n = min_max_normalize(vsrs)
    vpds_n = min_max_normalize(vpds)
    engs_n = min_max_normalize(engagements)

    for i, v in enumerate(videos):
        freshness = calc_freshness(v["days_age"])
        duration_fit = calc_duration_fit(v["duration_sec"])

        score = (
            vsrs_n[i] * 0.30
            + vpds_n[i] * 0.30
            + engs_n[i] * 0.15
            + freshness * 0.15
            + duration_fit * 0.10
        )

        v["score"] = round(score * 10, 1)  # Scale to 0-10
        v["freshness"] = freshness
        v["duration_fit"] = duration_fit

    videos.sort(key=lambda v: v["score"], reverse=True)
    return videos


def discover_mode(yt, months, max_duration_min, top_n):
    """Scan competitor channels, find top viral videos."""
    all_videos = []
    failed = []

    for idx, (handle, desc) in enumerate(CHANNELS.items(), 1):
        print(f"[{idx}/{len(CHANNELS)}] {handle} — {desc}")

        channel_info = resolve_channel(yt, handle)
        if not channel_info:
            print(f"  [SKIP] channel not found")
            failed.append(handle)
            continue

        print(f"  {channel_info['title']} ({channel_info['subscribers']:,} subs)")

        videos = get_channel_videos(yt, channel_info, max_duration_min)

        # Filter by age
        if months:
            max_days = months * 30
            videos = [v for v in videos if v["days_age"] <= max_days]

        for v in videos:
            v["query"] = channel_info["title"]
        all_videos.extend(videos)
        print(f"  {len(videos)} videos after filters")

        time.sleep(0.3)

    scored = score_videos(all_videos)
    top = scored[:top_n]

    print(f"\nTotal: {len(all_videos)} videos from {len(CHANNELS) - len(failed)} channels")
    if failed:
        print(f"Failed channels: {', '.join(failed)}")

    return top, len(all_videos), len(CHANNELS) - len(failed)


def topic_mode(yt, topic, max_duration_min, top_n):
    """Search YouTube for best videos on a topic."""
    print(f"Searching: \"{topic}\"")

    video_ids = []
    next_page = None

    # Search in two passes: relevance and viewCount
    for order in ["viewCount", "relevance"]:
        try:
            resp = yt.search().list(
                part="id",
                q=topic,
                type="video",
                order=order,
                maxResults=50,
                pageToken=next_page,
            ).execute()
            for item in resp.get("items", []):
                vid = item["id"].get("videoId")
                if vid and vid not in video_ids:
                    video_ids.append(vid)
        except Exception as e:
            print(f"  [ERR] search ({order}): {e}")

    print(f"  Found {len(video_ids)} unique videos")

    if not video_ids:
        return [], 0, 0

    videos = enrich_videos(yt, video_ids, None, max_duration_min)
    for v in videos:
        v["query"] = topic
    scored = score_videos(videos)
    top = scored[:top_n]

    return top, len(videos), len({v["channel_id"] for v in videos})


def save_results(videos, mode, topic, total_analyzed, channels_count):
    """Save results to JSON cache and MD file."""
    os.makedirs(IDEAS_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    # JSON cache
    cache = {
        "date": today,
        "mode": mode,
        "topic": topic,
        "total_analyzed": total_analyzed,
        "channels_count": channels_count,
        "results": videos,
    }
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # MD file
    if mode == "discover":
        slug = "discover"
        title = "Discovery"
    else:
        slug = "topic-" + re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", topic).strip("-").lower()
        title = f"Topic: {topic}"

    md_path = os.path.join(IDEAS_DIR, f"{today}_{slug}.md")

    lines = [
        f"# YouTube Ideas: {title}",
        f"**Дата:** {today} | **Режим:** {mode} | **Каналов:** {channels_count} | **Видео проанализировано:** {total_analyzed}",
        "",
        "| # | Score | Запрос | Автор | Видео | Views | VSR | VPD | Длина | Дата | Ссылка |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for i, v in enumerate(videos, 1):
        url = f"https://youtube.com/watch?v={v['video_id']}"
        title_short = v["title"][:50].replace("|", "\\|")
        if len(v["title"]) > 50:
            title_short += "..."
        query_short = v.get("query", "")[:25].replace("|", "\\|")
        channel_short = v["channel_title"][:20].replace("|", "\\|")
        lines.append(
            f"| {i} | {v['score']:.1f} | {query_short} | {channel_short} | {title_short} "
            f"| {v['views']:,} | {v['vsr']:.1f}x | {v['vpd']:,.0f} "
            f"| {v['duration_fmt']} | {v['published']} | [link]({url}) |"
        )

    lines.append("")

    # Detail section
    lines.append("---")
    lines.append("")
    lines.append("## Детали топ-видео")
    lines.append("")

    for i, v in enumerate(videos, 1):
        url = f"https://youtube.com/watch?v={v['video_id']}"
        lines.append(f"### {i}. {v['title']}")
        lines.append(f"- **Запрос:** {v.get('query', '—')}")
        lines.append(f"- **Канал:** {v['channel_title']} ({v['subscribers']:,} subs)")
        lines.append(f"- **Views:** {v['views']:,} | **Likes:** {v['likes']:,} | **Comments:** {v['comments']:,}")
        lines.append(f"- **VSR:** {v['vsr']:.1f}x | **VPD:** {v['vpd']:,.0f} | **Engagement:** {v['engagement']:.2%}")
        lines.append(f"- **Длина:** {v['duration_fmt']} | **Опубликовано:** {v['published']} ({v['days_age']} дней назад)")
        lines.append(f"- **Score:** {v['score']:.1f}/10 (freshness={v['freshness']}, duration_fit={v['duration_fit']})")
        lines.append(f"- **Ссылка:** {url}")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nSaved: {md_path}")
    print(f"Cache: {CACHE_PATH}")
    return md_path


def print_top(videos):
    """Print top results to console."""
    if not videos:
        print("\nNo results found.")
        return

    print(f"\n{'='*120}")
    print(f"{'#':>3} {'Score':>5} {'VSR':>6} {'VPD':>8} {'Views':>10} {'Dur':>7} {'Channel':>20} {'Query':>20} | Title")
    print("-" * 120)

    for i, v in enumerate(videos, 1):
        query = v.get("query", "")[:20]
        print(
            f"{i:>3} {v['score']:>5.1f} {v['vsr']:>5.1f}x {v['vpd']:>8,.0f} "
            f"{v['views']:>10,} {v['duration_fmt']:>7} {v['channel_title'][:20]:>20} "
            f"{query:>20} | {v['title'][:45]}"
        )


def main():
    parser = argparse.ArgumentParser(description="YouTube Ideas Discovery")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--discover", action="store_true", help="Scan competitor channels")
    group.add_argument("--topic", type=str, help="Search by topic")

    parser.add_argument("--months", type=int, default=6, help="Max age in months (discover mode, default: 6)")
    parser.add_argument("--max-duration", type=int, default=25, help="Max video duration in minutes (default: 25)")
    parser.add_argument("--top", type=int, default=10, help="Number of top results (default: 10)")

    args = parser.parse_args()

    creds = get_credentials()
    yt = build("youtube", "v3", credentials=creds)

    if args.discover:
        top, total, ch_count = discover_mode(yt, args.months, args.max_duration, args.top)
        mode = "discover"
        topic = None
    else:
        top, total, ch_count = topic_mode(yt, args.topic, args.max_duration, args.top)
        mode = "topic"
        topic = args.topic

    print_top(top)
    md_path = save_results(top, mode, topic, total, ch_count)

    print(f"\nDone! Top {len(top)} ideas saved.")


if __name__ == "__main__":
    main()
