# MN News Today Bot

Experimental news preview generator. **DRY RUN ONLY**: no Instagram publishing yet.

## Setup
1. Settings → Secrets and variables → Actions → New repository secret: `GEMINI_API_KEY` (keep private).
2. Actions → MN News Bot → Run workflow.
3. Download the `news-preview` artifact containing `latest.jpg` and `caption.txt`.

Uses RSS feeds, optional Gemini free-tier captions, and Pillow graphics. Fact-check before publishing. Free quota is not guaranteed. Live publishing and Pages hosting are not yet configured.
