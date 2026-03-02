#!/bin/bash
# Двойной пуш изменений курса:
# 1. guide/ → courses_share (для учеников)
# 2. mentor_analytics/ → mentor_analytics (личный архив)
#
# Использование: ./scripts/push_course.sh "сообщение коммита"

set -e

MSG="${1:-update course content}"

MENTOR_ROOT="/Users/aleksejerofeev/mentor_analytics"
GUIDE_ROOT="$MENTOR_ROOT/courses/product_section/guide"

echo "=== 1/2 Пушим в courses_share (ученики) ==="
cd "$GUIDE_ROOT"
git add -A
git commit -m "$MSG" || echo "Нечего коммитить в guide/"
git push

echo ""
echo "=== 2/2 Пушим в mentor_analytics (архив) ==="
cd "$MENTOR_ROOT"
git add -A
git commit -m "$MSG" || echo "Нечего коммитить в mentor_analytics/"
git push

echo ""
echo "✓ Готово. Оба репозитория обновлены."
