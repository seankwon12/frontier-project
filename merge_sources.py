"""Merge Gmail newsletters and Telegram messages into a single content list.

Pure data shuffling - no AI involved. Reads:
  - newsletters.json (Gmail pipeline output, uses 'sender' field)
  - telegram_messages.json (Telegram pipeline output, uses 'source' field)

Writes all_content.json with unified shape:
    [{ "source": ..., "subject": ..., "body": ..., "origin": "gmail"|"telegram" }]
"""

import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
NEWSLETTERS_PATH = ROOT / "newsletters.json"
TELEGRAM_PATH = ROOT / "telegram_messages.json"
OUTPUT_PATH = ROOT / "all_content.json"


def load_gmail():
    """Gmail items use 'sender' as the source identifier. Map to 'source'."""
    if not NEWSLETTERS_PATH.exists():
        print(f"[WARN] {NEWSLETTERS_PATH.name} not found, skipping Gmail.")
        return []
    with open(NEWSLETTERS_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    return [
        {
            "source": item.get("sender", "unknown"),
            "subject": item.get("subject", ""),
            "body": item.get("body", ""),
            "origin": "gmail",
        }
        for item in items
    ]


def load_telegram():
    """Telegram items already use 'source'. Just tag origin."""
    if not TELEGRAM_PATH.exists():
        print(f"[WARN] {TELEGRAM_PATH.name} not found, skipping Telegram.")
        return []
    with open(TELEGRAM_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    return [
        {
            "source": item.get("source", "unknown"),
            "subject": item.get("subject", ""),
            "body": item.get("body", ""),
            "origin": "telegram",
        }
        for item in items
    ]


def main():
    gmail_items = load_gmail()
    telegram_items = load_telegram()
    all_items = gmail_items + telegram_items

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"Total items: {len(all_items)}")
    print(f"  Gmail:    {len(gmail_items)}")
    print(f"  Telegram: {len(telegram_items)}")

    print("\nPer-source breakdown:")
    by_source = Counter((item["origin"], item["source"]) for item in all_items)
    for (origin, source), count in sorted(by_source.items(), key=lambda x: (-x[1], x[0])):
        print(f"  [{origin:<8}] {count:>3}  {source}")

    print(f"\nSaved to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
