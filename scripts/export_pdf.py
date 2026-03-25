#!/usr/bin/env python3
"""
Конвертация MD → PDF для видео-пакетов.

Использование:
    python3 scripts/export_pdf.py content/youtube/productions/da-vs-ds-vs-de/
    python3 scripts/export_pdf.py content/youtube/productions/da-vs-ds-vs-de/script.md

Зависимости: pandoc (brew install pandoc)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def check_pandoc():
    """Проверить, что pandoc установлен."""
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Ошибка: pandoc не установлен.")
        print("Установите: brew install pandoc")
        sys.exit(1)


def find_pdf_engine():
    """Определить доступный PDF-движок."""
    # Стандартные пути macOS для TeX (basictex)
    tex_paths = ["/Library/TeX/texbin/xelatex", "/Library/TeX/texbin/pdflatex"]
    candidates = ["xelatex", "pdflatex", "wkhtmltopdf"] + tex_paths
    for engine in candidates:
        try:
            subprocess.run([engine, "--version"], capture_output=True)
            return engine
        except FileNotFoundError:
            continue
    return None


def convert_md_to_pdf(md_path: Path, output_dir: Path, engine: str | None):
    """Конвертировать один MD-файл в PDF."""
    pdf_name = md_path.stem + ".pdf"
    pdf_path = output_dir / pdf_name

    engine_name = Path(engine).name if engine else None
    if engine_name in ("xelatex", "pdflatex"):
        cmd = [
            "pandoc", str(md_path), "-o", str(pdf_path),
            f"--pdf-engine={engine}",
            "-V", "geometry:margin=2cm",
            "-V", "fontsize=11pt",
        ]
        if engine_name == "xelatex":
            cmd.extend(["-V", "mainfont=Arial"])
    elif engine_name == "wkhtmltopdf":
        cmd = [
            "pandoc", str(md_path), "-o", str(pdf_path),
            "--pdf-engine=wkhtmltopdf",
        ]
    else:
        # Fallback: pandoc → HTML, потом конвертируем через встроенный
        html_path = output_dir / (md_path.stem + ".html")
        cmd = ["pandoc", str(md_path), "-o", str(html_path), "--standalone"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ {md_path.name} → {html_path.name} (HTML, нет PDF-движка)")
                return True
        except Exception:
            pass
        print(f"  ✗ {md_path.name}: нет PDF-движка (установите: brew install basictex)")
        return False

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ {md_path.name}: {result.stderr.strip()}")
            return False
        print(f"  ✓ {md_path.name} → {pdf_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ {md_path.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Конвертация MD → PDF")
    parser.add_argument("path", help="Путь к папке пакета или конкретному .md файлу")
    args = parser.parse_args()

    check_pandoc()
    engine = find_pdf_engine()
    if engine:
        print(f"PDF-движок: {engine}")
    else:
        print("PDF-движок не найден, будет экспорт в HTML")
        print("Для PDF установите: brew install basictex")

    path = Path(args.path)

    if path.is_file() and path.suffix == ".md":
        # Один файл
        output_dir = path.parent / "pdf"
        output_dir.mkdir(exist_ok=True)
        print(f"Конвертация: {path.name}")
        convert_md_to_pdf(path, output_dir, engine)
    elif path.is_dir():
        # Папка — конвертировать все .md файлы
        md_files = sorted(f for f in path.glob("*.md"))
        # Также включить файлы из refs/
        refs_dir = path / "refs"
        if refs_dir.is_dir():
            md_files.extend(sorted(refs_dir.glob("*.md")))

        if not md_files:
            print(f"Нет .md файлов в {path}")
            sys.exit(1)

        output_dir = path / "pdf"
        output_dir.mkdir(exist_ok=True)

        print(f"Конвертация {len(md_files)} файлов → {output_dir}/")
        success = 0
        for md_file in md_files:
            if convert_md_to_pdf(md_file, output_dir, engine):
                success += 1

        print(f"\nГотово: {success}/{len(md_files)} файлов сконвертировано")
    else:
        print(f"Ошибка: {path} — не файл .md и не директория")
        sys.exit(1)


if __name__ == "__main__":
    main()
