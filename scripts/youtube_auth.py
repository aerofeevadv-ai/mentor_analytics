"""
YouTube OAuth 2.0 — получение refresh_token.

Запуск:
    python3 scripts/youtube_auth.py

Что делает:
    1. Открывает браузер для авторизации Google-аккаунта
    2. Получает access_token + refresh_token
    3. Сохраняет токены в .secrets/youtube_token.json

Примечание: комментарии публикуются от имени «Алексей Ерофеев»
(личный аккаунт UCiN9Mg6tU3Q-wiKpRoeiTKQ), т.к. Brand Account
«Аналитика без воды» не поддерживает OAuth для YouTube API
(только для YouTube Content Partners).

После авторизации файл youtube_token.json используется скриптами
для записи в YouTube API (обновление тегов, описаний и т.д.).
"""

import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET = os.path.join(BASE_DIR, ".secrets", "youtube_client_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, ".secrets", "youtube_token.json")


def main():
    if not os.path.exists(CLIENT_SECRET):
        print(f"Файл не найден: {CLIENT_SECRET}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True, prompt="consent")

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"Токен сохранён: {TOKEN_PATH}")
    print(f"Refresh token: {creds.refresh_token[:20]}...")


if __name__ == "__main__":
    main()
