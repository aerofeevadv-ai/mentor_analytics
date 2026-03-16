"""
Транскрибация YouTube-видео по ID или URL.

Запуск:
    python3 scripts/youtube_transcript.py VIDEO_ID_OR_URL [--lang ru,en] [--output FILE]

Примеры:
    python3 scripts/youtube_transcript.py kbKty5ZVKMY
    python3 scripts/youtube_transcript.py https://youtube.com/watch?v=kbKty5ZVKMY --lang en
    python3 scripts/youtube_transcript.py kbKty5ZVKMY --output transcript.md
"""

import argparse
import os
import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id):
    """Extract video ID from URL or return as-is if already an ID."""
    # Already an ID (11 chars, alphanumeric + - _)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id

    # youtube.com/watch?v=ID
    m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)

    # youtu.be/ID
    m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)

    # youtube.com/shorts/ID
    m = re.search(r"shorts/([a-zA-Z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)

    return url_or_id


def format_timestamp(seconds):
    """Format seconds to HH:MM:SS or MM:SS."""
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def fetch_transcript(video_id, languages):
    """Fetch transcript, return list of segments."""
    api = YouTubeTranscriptApi()

    # Try requested languages first
    try:
        transcript = api.fetch(video_id, languages=languages)
        segments = list(transcript)
        if segments:
            return segments
    except Exception:
        pass

    # Fallback: try any available language
    try:
        transcript = api.fetch(video_id)
        return list(transcript)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def format_as_text(segments):
    """Format segments as plain text with timestamps."""
    lines = []
    for seg in segments:
        ts = format_timestamp(seg.start)
        text = seg.text.replace("\n", " ").strip()
        if text:
            lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


def format_as_markdown(segments, video_id):
    """Format segments as markdown with grouped paragraphs."""
    url = f"https://youtube.com/watch?v={video_id}"
    duration = format_timestamp(segments[-1].start + segments[-1].duration) if segments else "0:00"

    lines = [
        f"# Транскрипт: {url}",
        f"**Длительность:** {duration} | **Сегментов:** {len(segments)}",
        "",
        "---",
        "",
    ]

    # Group segments into ~30-second paragraphs
    paragraph = []
    paragraph_start = 0

    for seg in segments:
        text = seg.text.replace("\n", " ").strip()
        if not text:
            continue

        if not paragraph:
            paragraph_start = seg.start

        paragraph.append(text)

        # New paragraph every ~30 seconds
        if seg.start - paragraph_start >= 30 and paragraph:
            ts = format_timestamp(paragraph_start)
            lines.append(f"**[{ts}]** {' '.join(paragraph)}")
            lines.append("")
            paragraph = []

    # Flush remaining
    if paragraph:
        ts = format_timestamp(paragraph_start)
        lines.append(f"**[{ts}]** {' '.join(paragraph)}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube video transcript")
    parser.add_argument("video", help="Video ID or URL")
    parser.add_argument("--lang", type=str, default="ru,en",
                        help="Languages priority, comma-separated (default: ru,en)")
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["text", "markdown"], default="markdown",
                        help="Output format (default: markdown)")

    args = parser.parse_args()

    video_id = extract_video_id(args.video)
    languages = [l.strip() for l in args.lang.split(",")]

    print(f"Fetching transcript for {video_id} (languages: {languages})...", file=sys.stderr)

    segments = fetch_transcript(video_id, languages)
    if not segments:
        print("No transcript available for this video.", file=sys.stderr)
        sys.exit(1)

    print(f"Got {len(segments)} segments", file=sys.stderr)

    if args.format == "markdown":
        output = format_as_markdown(segments, video_id)
    else:
        output = format_as_text(segments)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
