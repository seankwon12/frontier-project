# Daily Digest Agent

A daily digest agent that reads my Gmail newsletters and Telegram channels, finds topics multiple sources cover, and produces a Top 5 HTML digest. CS 153: Frontier Systems (Stanford, Spring 2026) — final project.

## What it does

Pulls the last 24 hours of informational mail from Gmail and the last 24 hours of messages from 9 Telegram channels I follow. Groups the combined feed by semantic topic across both languages (most Telegram content is Korean). Ranks clusters strictly by how many distinct sources covered each one, picks the Top 5, and writes a single static `digest.html` I can double-click. The hypothesis under test: if multiple independent sources cover the same thing on the same day, that thing is probably what matters today.

## Pipeline

- `newsletter_filter.py` — fetch Gmail, rule-based classify, extract bodies → `newsletters.json`
- `telegram_fetch.py` — fetch last 24h from 9 configured channels via Telethon → `telegram_messages.json`
- `merge_sources.py` — unify into a single list with `origin` tagged → `all_content.json`
- `cluster_content.py` — group items by semantic topic (manual trigger via Claude Code) → `clusters.json`
- `digest_top5.py` — rank by cross-source spread, attach per-cluster summary (manual trigger via Claude Code) → `digest_top5.md`
- `build_digest_html.py` — render the static HTML page → `digest.html`

`cluster_content.py` and `digest_top5.py` are the AI steps. They currently run as manual triggers via Claude Code: the clustering decisions and per-cluster summaries are authored against each run's data and baked into the scripts as constants. The pipeline is structured so each AI step can be swapped for an Anthropic API call without changing the rest. `run_all.py` runs all six stages in order and fails loudly on any error (no silent fallback to cached data).

## How to run

Prerequisites: Python 3.14, a Gmail account with the Gmail API enabled (OAuth desktop client), and a Telegram `api_id` / `api_hash` from [my.telegram.org](https://my.telegram.org).

Install:
```
pip install -r requirements.txt
```

Create these two credentials files in the project root — both are git-ignored:

- `credentials.json` — Gmail OAuth desktop client downloaded from Google Cloud Console.
- `telegram_credentials.json` — `{"api_id": 1234567, "api_hash": "0123456789abcdef0123456789abcdef"}`

Run:
```
python run_all.py
```

Open `digest.html` by double-clicking. No server needed.

## Limitations

- The Gmail classifier is rule-based v1 (sender + keyword heuristics). It still lets some receipts and event-registration mail through.
- Clustering and summarization run as manual triggers via Claude Code, not as autonomous API calls. The architecture supports a swap; the swap isn't done.
- The "spread = importance" hypothesis only meaningfully applies when multiple sources exist. On thin days the lower slots fall back to single-source clusters, marked `Single-source · low confidence` in the HTML so the reader can tell the slot isn't justified by the hypothesis.
- Two AI-introduced bugs surfaced during development and were caught by hand-reviewing the output, not by automated tests: cluster-index drift between runs (clusters silently grouped wrong items after the data window shifted), and per-cluster summary text staying cached from prior runs with different source counts ("Three channels..." shown over a `spread=2` badge). Both are fixed; both are a reminder that AI output can look correct on the surface while being wrong underneath.

## What's next

- Move clustering and summarization to an Anthropic API call so the pipeline runs autonomously on a schedule. The Claude Max plan used to build this project does not include API access; this is pending sponsored compute or separate API credentials.
- Replace the rule-based Gmail classifier with an AI step once API access is available.
- Add RSS feeds for news / podcasts and evaluate adding more Telegram channels.

## AI usage

Built end-to-end in one extended session using Claude Code (Claude Max subscription) as a pair programmer. The author had no prior coding experience before this project. Claude Code wrote most of the code; the author made all architecture and design decisions, made all credentials and `.gitignore` choices, reviewed every change, and caught and corrected multiple AI-introduced bugs — including the two data-integrity issues noted above.
