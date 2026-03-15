"""
Обновление заголовков видео YouTube-канала @analytic_offers.

Запуск:
    python3 scripts/youtube_update_titles.py          # dry-run (только показать)
    python3 scripts/youtube_update_titles.py --apply   # применить изменения
"""

import json
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")

# ── Новые заголовки ──────────────────────────────────────────────────
TITLES = {
    # ТЗ #4: было «Где в IT РЕАЛЬНО платят: ТОП 5 профессий с ВЫСОКИМИ зарплатами» (67 сим)
    "p37_JzZdXc8": "Где в IT платят 300 000+ ₽: ТОП-5 профессий",

    # ТЗ #5: было «Вот что на самом деле используют аналитики: ТОП-6 нужных инструментов» (72 сим)
    "pZLij7bl8Tc": "ТОП-6 инструментов аналитика в 2026",
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

    video_ids = list(TITLES.keys())
    batch = ",".join(video_ids)
    resp = yt.videos().list(part="snippet", id=batch).execute()

    videos = {item["id"]: item for item in resp["items"]}

    updated = 0
    for vid, new_title in TITLES.items():
        if vid not in videos:
            print(f"[SKIP] {vid} — не найдено")
            continue

        item = videos[vid]
        old_title = item["snippet"]["title"]

        print(f"[{'UPDATE' if apply else 'WOULD'}] {vid}")
        print(f"  Было:  {old_title}")
        print(f"  Будет: {new_title}")
        print()

        if apply:
            try:
                item["snippet"]["title"] = new_title
                yt.videos().update(
                    part="snippet",
                    body={"id": vid, "snippet": item["snippet"]},
                ).execute()
                updated += 1
                print(f"  ✓ OK\n")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ ERROR: {e}\n")

    print(f"=== Итого: {updated} обновлено ===")
    if not apply:
        print("Запустите с --apply для применения изменений.")


if __name__ == "__main__":
    main()
