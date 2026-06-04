"""Fetch the last 24 hours of messages from configured Telegram channels.

Loads:
  - api_id / api_hash from telegram_credentials.json (via telegram_auth)
  - channel list from telegram_channels.json

For each channel, iterates messages newer than (now - 24h), keeps any message
that has readable text (plain text or media caption), and writes the result
to telegram_messages.json with the same shape as newsletters.json:
    [{ "source": ..., "subject": ..., "body": ... }, ...]

Pure-media messages with no caption are skipped.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telethon.sync import TelegramClient

from telegram_auth import SESSION_NAME, load_credentials

# Force UTF-8 on stdout so Korean channel/message text renders on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

CHANNELS_PATH = Path(__file__).parent / "telegram_channels.json"
OUTPUT_PATH = Path(__file__).parent / "telegram_messages.json"
LOOKBACK_HOURS = 24
SUBJECT_MAX_CHARS = 80


def load_channels():
    with open(CHANNELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_subject(text):
    """Take the first line, then cap at SUBJECT_MAX_CHARS."""
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    if len(first_line) > SUBJECT_MAX_CHARS:
        return first_line[:SUBJECT_MAX_CHARS].rstrip() + "..."
    return first_line


def preview(text, lines=2):
    """Return the first N lines of text, with each line truncated for display."""
    out_lines = []
    for line in text.strip().splitlines()[:lines]:
        if len(line) > 100:
            line = line[:100] + "..."
        out_lines.append(line)
    return "\n".join(out_lines)


def main():
    api_id, api_hash = load_credentials()
    channels = load_channels()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    print(f"Fetching messages since {cutoff.isoformat()} (last {LOOKBACK_HOURS}h)")
    print(f"Channels configured: {len(channels)}\n")

    results = []

    with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        for ch in channels:
            ch_id = ch["id"]
            ch_title = ch["title"]
            print(f"== {ch_title} (id={ch_id}) ==")

            kept = 0
            skipped_no_text = 0
            try:
                # iter_messages walks newest -> oldest; stop once we pass cutoff.
                for msg in client.iter_messages(ch_id):
                    if msg.date < cutoff:
                        break
                    text = (msg.message or "").strip()
                    if not text:
                        skipped_no_text += 1
                        continue

                    subject = build_subject(text)
                    results.append({
                        "source": ch_title,
                        "subject": subject,
                        "body": text,
                    })
                    kept += 1
                    print(f"  [{msg.date.astimezone().strftime('%m-%d %H:%M')}] {preview(text)}")
            except Exception as e:
                print(f"  ERROR while reading channel: {e}")
                continue

            print(f"  -> kept: {kept}, skipped (no text): {skipped_no_text}\n")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} messages to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
