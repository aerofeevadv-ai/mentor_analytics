#!/usr/bin/env python3
"""
Генерация retention-кривых для курса продуктовых метрик.
Сохраняет два PNG в courses/product_section/guide/module_1/images/
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

OUTPUT_DIR = Path(__file__).parent.parent / "courses" / "product_section" / "guide" / "module_1" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DAYS = [0, 1, 7, 14, 30]
DAY_LABELS = ["D0", "D1", "D7", "D14", "D30"]

STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#EEEEEE",
    "grid.linewidth": 0.8,
    "font.family": "sans-serif",
    "font.size": 12,
}


def save(fig, name):
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"Сохранено: {path}")
    plt.close(fig)


def chart_with_plateau():
    retention = [100, 45, 28, 22, 20]

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 4.5))

        ax.plot(DAYS, retention, color="#2563EB", linewidth=2.5,
                marker="o", markersize=6, zorder=3)

        # Плато — штриховая линия
        plateau_y = 20
        ax.axhline(plateau_y, color="#2563EB", linewidth=1.2,
                   linestyle="--", alpha=0.5, zorder=2)
        ax.annotate(
            "плато ~20%",
            xy=(20, plateau_y),
            xytext=(20, plateau_y + 8),
            fontsize=11, color="#2563EB",
            arrowprops=dict(arrowstyle="-", color="#2563EB", lw=1),
        )

        ax.set_xticks(DAYS)
        ax.set_xticklabels(DAY_LABELS)
        ax.set_yticks(range(0, 101, 20))
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax.set_ylim(0, 110)
        ax.set_xlim(-1, 32)
        ax.set_xlabel("День после первого визита", fontsize=11, labelpad=8)
        ax.set_ylabel("% вернувшихся", fontsize=11)
        ax.set_title("Продукт с плато — можно масштабировать",
                     fontsize=13, fontweight="bold", pad=14)

        fig.tight_layout()
        save(fig, "retention_plateau.png")


def chart_no_plateau():
    retention = [100, 60, 20, 10, 4]

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 4.5))

        ax.plot(DAYS, retention, color="#DC2626", linewidth=2.5,
                marker="o", markersize=6, zorder=3)

        ax.axhline(0, color="#DC2626", linewidth=1.2,
                   linestyle="--", alpha=0.4, zorder=2)
        ax.annotate(
            "плато → 0%",
            xy=(25, 4),
            xytext=(15, 18),
            fontsize=11, color="#DC2626",
            arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1),
        )

        ax.set_xticks(DAYS)
        ax.set_xticklabels(DAY_LABELS)
        ax.set_yticks(range(0, 101, 20))
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax.set_ylim(0, 110)
        ax.set_xlim(-1, 32)
        ax.set_xlabel("День после первого визита", fontsize=11, labelpad=8)
        ax.set_ylabel("% вернувшихся", fontsize=11)
        ax.set_title("Продукт без плато — сначала чинить продукт",
                     fontsize=13, fontweight="bold", pad=14)

        fig.tight_layout()
        save(fig, "retention_no_plateau.png")


if __name__ == "__main__":
    chart_with_plateau()
    chart_no_plateau()
    print("Готово.")
