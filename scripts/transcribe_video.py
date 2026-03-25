#!/usr/bin/env python3
"""
Транскрибация локальных видео (.mkv и др.) с таймкодами.
Использует faster-whisper (локально, без API).

Использование:
    python3 scripts/transcribe_video.py VIDEO.mkv
    python3 scripts/transcribe_video.py /path/to/folder/        # все .mkv в папке
    python3 scripts/transcribe_video.py VIDEO.mkv -m large-v3   # другая модель
    python3 scripts/transcribe_video.py VIDEO.mkv -o output.md  # свой путь вывода
"""

import argparse
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    """Секунды → HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def transcribe_file(model: WhisperModel, video_path: Path, output_path: Path | None = None):
    """Транскрибировать один файл."""
    if output_path is None:
        output_path = video_path.with_suffix(".md")

    print(f"\n{'='*60}")
    print(f"Файл: {video_path.name}")
    print(f"Вывод: {output_path}")
    print(f"{'='*60}")

    start_time = time.time()

    segments, info = model.transcribe(
        str(video_path),
        language="ru",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    print(f"Язык: {info.language} (вероятность {info.language_probability:.1%})")
    print(f"Длительность: {format_timestamp(info.duration)}")
    print("Транскрибация...", flush=True)

    lines = []
    full_text_parts = []

    for segment in segments:
        ts = format_timestamp(segment.start)
        text = segment.text.strip()
        lines.append(f"**[{ts}]** {text}")
        full_text_parts.append(text)

    elapsed = time.time() - start_time
    ratio = info.duration / elapsed if elapsed > 0 else 0

    # Формируем markdown
    md_parts = [
        f"# Транскрипция: {video_path.name}\n",
        f"- **Длительность:** {format_timestamp(info.duration)}",
        f"- **Модель:** {model.model_size_or_path}",
        f"- **Время обработки:** {format_timestamp(elapsed)} ({ratio:.1f}x realtime)\n",
        "---\n",
        "## Транскрипция с таймкодами\n",
    ]
    md_parts.extend(lines)
    md_parts.append("\n---\n")
    md_parts.append("## Полный текст (без таймкодов)\n")
    md_parts.append(" ".join(full_text_parts))
    md_parts.append("")

    output_path.write_text("\n".join(md_parts), encoding="utf-8")

    print(f"Готово за {format_timestamp(elapsed)} ({ratio:.1f}x realtime)")
    print(f"Сохранено: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Транскрибация видео с таймкодами")
    parser.add_argument("input", help="Видео файл или папка с видео")
    parser.add_argument("-m", "--model", default="medium", help="Модель whisper (tiny/base/small/medium/large-v3). Default: medium")
    parser.add_argument("-o", "--output", help="Путь для вывода (только для одного файла)")
    args = parser.parse_args()

    input_path = Path(args.input)
    video_extensions = {".mkv", ".mp4", ".mov", ".avi", ".webm", ".flv", ".wmv"}

    # Собираем файлы
    if input_path.is_dir():
        files = sorted(p for p in input_path.iterdir() if p.suffix.lower() in video_extensions)
        if not files:
            print(f"Нет видеофайлов в {input_path}")
            sys.exit(1)
        print(f"Найдено {len(files)} видео в {input_path}")
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"Не найдено: {input_path}")
        sys.exit(1)

    if args.output and len(files) > 1:
        print("--output можно использовать только для одного файла")
        sys.exit(1)

    # Загружаем модель (один раз)
    print(f"Загружаю модель '{args.model}'... (первый раз скачает ~1.5 ГБ)")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    print("Модель загружена.")

    # Транскрибация
    output = Path(args.output) if args.output else None
    results = []
    for f in files:
        result = transcribe_file(model, f, output)
        results.append(result)

    print(f"\n{'='*60}")
    print(f"Обработано файлов: {len(results)}")
    for r in results:
        print(f"  → {r}")


if __name__ == "__main__":
    main()
