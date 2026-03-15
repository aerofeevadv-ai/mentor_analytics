#!/usr/bin/env python3
"""
Генерация изображений через Polza.ai API (Gemini Flash Image)

Использование:
    python generate_image.py "описание изображения"
    python generate_image.py --photo photo.jpg "описание изображения"
    python generate_image.py --photo photo.jpg --name output_name "описание"
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
MAX_PHOTO_SIZE = 1280  # ресайз фото до этого размера по длинной стороне


def get_api_key():
    key = os.environ.get("POLZA_AI_KEY")
    if not key:
        print("Ошибка: переменная окружения POLZA_AI_KEY не задана")
        print("Добавь в ~/.zshrc: export POLZA_AI_KEY='твой_ключ'")
        sys.exit(1)
    return key


def resize_and_encode(photo_path: str) -> str:
    """Ресайз фото и кодирование в base64 data URL."""
    from PIL import Image
    import io

    img = Image.open(photo_path)
    img.thumbnail((MAX_PHOTO_SIZE, MAX_PHOTO_SIZE), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def generate_image(prompt: str, photo_path: str = None) -> str:
    api_key = get_api_key()
    print(f"Генерирую: {prompt[:80]}...")

    if photo_path:
        print(f"Референс: {photo_path}")
        image_url = resize_and_encode(photo_path)
        content = [
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            },
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
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
    args = sys.argv[1:]
    photo_path = None
    output_name = None

    # Парсинг аргументов
    while args:
        if args[0] == "--photo" and len(args) > 1:
            photo_path = args[1]
            args = args[2:]
        elif args[0] == "--name" and len(args) > 1:
            output_name = args[1]
            args = args[2:]
        else:
            break

    if not args:
        print("Использование:")
        print("  python generate_image.py 'описание'")
        print("  python generate_image.py --photo photo.jpg 'описание'")
        sys.exit(1)

    prompt = " ".join(args)

    try:
        path = generate_image(prompt, photo_path)
        if output_name:
            new_path = OUTPUT_DIR / f"{output_name}.png"
            Path(path).rename(new_path)
            path = str(new_path)
        print(f"Сохранено: {path}")
        subprocess.run(["open", path])  # macOS Preview
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
