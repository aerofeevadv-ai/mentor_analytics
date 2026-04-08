PYTHON ?= python3
PIP ?= pip
VENV ?= .venv

.PHONY: help venv install check-env yt-auth yt-comments yt-comments-30 yt-ideas-discover yt-ideas-topic yt-titles-dry yt-tags-dry transcribe pdf

help:
	@echo "Available targets:"
	@echo "  make venv                 Create local virtualenv"
	@echo "  make install              Install Python dependencies into the active env"
	@echo "  make check-env            Show expected local secrets and tools"
	@echo "  make yt-auth              Run YouTube OAuth flow"
	@echo "  make yt-comments          Export unanswered comments to Google Sheets"
	@echo "  make yt-comments-30       Same, but only for last 30 days"
	@echo "  make yt-ideas-discover    Discover viral ideas from tracked channels"
	@echo "  make yt-ideas-topic TOPIC='product metrics'"
	@echo "  make yt-titles-dry        Dry-run title updates"
	@echo "  make yt-tags-dry          Dry-run tag updates"
	@echo "  make transcribe FILE=video.mp4"
	@echo "  make pdf PATH=content/youtube/productions/some-slug/"

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(PIP) install -r requirements.txt

check-env:
	@echo "Expected local files:"
	@echo "  .secrets/youtube_client_secret.json"
	@echo "  .secrets/youtube_token.json"
	@echo "  .secrets/comments_sheet_id.txt (created on first Sheets sync)"
	@echo ""
	@echo "Expected env vars:"
	@echo "  POLZA_AI_KEY"
	@echo ""
	@echo "Optional local tools:"
	@echo "  pandoc"

yt-auth:
	$(PYTHON) scripts/youtube_auth.py

yt-comments:
	$(PYTHON) scripts/youtube_comments_to_sheets.py

yt-comments-30:
	$(PYTHON) scripts/youtube_comments_to_sheets.py --days 30

yt-ideas-discover:
	$(PYTHON) scripts/youtube_find_ideas.py --discover

yt-ideas-topic:
	$(PYTHON) scripts/youtube_find_ideas.py --topic "$(TOPIC)"

yt-titles-dry:
	$(PYTHON) scripts/youtube_update_titles.py

yt-tags-dry:
	$(PYTHON) scripts/youtube_update_tags.py

transcribe:
	$(PYTHON) scripts/transcribe_video.py "$(FILE)"

pdf:
	$(PYTHON) scripts/export_pdf.py "$(PATH)"
