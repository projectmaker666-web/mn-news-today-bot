# MN News Today Bot 🇲🇳

Free-tier-oriented Instagram news automation: RSS -> optional Gemini text editor -> original Pillow graphics -> Meta Instagram API.

**Safe by default:** `DRY_RUN=true` (no Instagram posts). All AI output is constrained to a supplied source headline/summary, but automated verification is imperfect. Review before enabling live publishing.

## Setup
1. GitHub repository **Settings > Secrets and variables > Actions**: add `GEMINI_API_KEY` (optional for dry run), `IG_ACCESS_TOKEN`, `IG_USER_ID` (Instagram professional account ID), when ready.
2. **Settings > Variables > Actions**: set `DRY_RUN=true`; optionally `GEMINI_MODEL=gemini-2.5-flash-lite`. The workflow defaults to dry-run even without the variable.
3. **Actions > MN News Bot > Run workflow** to test. Download the `news-preview` artifact for the image and caption. No token is needed to test a dry run.
4. Before live publishing, make repository **Public** (GitHub Pages on GitHub Free requires public repos), then **Settings > Pages > Source: GitHub Actions**. Set repository variable `DRY_RUN=false`. A live job first deploys its generated image to Pages, then publishes it using the Instagram API. Ensure `instagram_business_content_publish` permission and a valid Instagram token.
5. Keep Instagram and Gemini keys in **Secrets**, never in source code.

The hourly cron is UTC (GitHub schedule may be delayed). Categories rotate by Mongolia local hour. Posts are skipped when no suitable fresh story is found, when an item is already used, or when a required credential is absent. There is no guarantee of 24 posts/day or fully verified facts.

## Limitations
- Google News RSS and publisher feeds can change; publisher rights and platform rules still apply. Graphics are original and do not copy article images.
- Gemini free quotas are project/model-dependent; failures fall back to conservative source-based captions.
- GitHub Actions schedule can be delayed or disabled after inactivity. Token expiration/refresh must be managed.
- This project is not a replacement for editorial fact-checking. Live publishing is at your own risk.
