#!/usr/bin/env python3
"""
Генерация изображений через Polza.ai API (Gemini Flash Image)
Использование: python generate_image.py "описание изображения"
"""

import os
import sys
import json
import base64
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

# Настройки
CHAT_URL = "https://polza.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash-image"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "images"


def get_api_key():
    key = os.environ.get("POLZA_AI_KEY")
    if not key:
        print("Ошибка: переменная окружения POLZA_AI_KEY не задана")
        print("Добавь в ~/.zshrc: export POLZA_AI_KEY='твой_ключ'")
        sys.exit(1)
    return key


def generate_image(prompt: str) -> str:
    api_key = get_api_key()
    print(f"Генерирую: {prompt[:80]}...")

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        CHAT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    image_b64 = None
    with urllib.request.urlopen(req) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            try:
                chunk = json.loads(line[6:])
            except json.JSONDecodeError:
                continue

            delta = chunk.get("choices", [{}])[0].get("delta", {})
            images = delta.get("images", [])
            if images:
                url = images[0].get("image_url", {}).get("url", "")
                if url.startswith("data:image"):
                    # data:image/png;base64,<data>
                    image_b64 = url.split(",", 1)[1]
                    break

    if not image_b64:
        print("Ошибка: изображение не получено из ответа API")
        sys.exit(1)

    image_bytes = base64.b64decode(image_b64)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = OUTPUT_DIR / f"{timestamp}.png"
    output_path.write_bytes(image_bytes)

    return str(output_path)


def main():
    if len(sys.argv) < 2:
        print("Использование: python generate_image.py 'описание изображения'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    try:
        path = generate_image(prompt)
        print(f"Сохранено: {path}")
        subprocess.run(["open", path])  # macOS Preview
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
