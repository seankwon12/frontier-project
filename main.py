# Daily Digest Agent - CS 153 Frontier Systems
# Goal: read my own subscribed information sources, remove duplicate
# stories, rank by importance, and deliver only the day's key items.
#
# Status: early scaffold. Dedup + ranking logic below actually runs.
# Source connectors (Gmail, RSS) and AI summarization are structured
# but not yet connected - sponsored compute pending (see Q6).


def fetch_items():
    """Return raw items from connected sources.

    NOTE: Real connectors (Gmail API, podcast/news RSS) are a
    planned next step - see Q4. For now this returns sample items
    so the dedup + ranking pipeline can be developed and tested.
    """
    return [
        {"source": "newsletter", "title": "Chip export rules tighten", "importance": 5},
        {"source": "rss_news", "title": "Chip export rules tighten",   "importance": 4},
        {"source": "podcast",   "title": "Weekly market recap",        "importance": 2},
        {"source": "newsletter", "title": "New foundation model released", "importance": 5},
    ]


def remove_duplicates(items):
    """Drop items whose titles repeat across sources, keeping the
    highest-importance copy. This part actually works."""
    best = {}
    for item in items:
        key = item["title"].strip().lower()
        if key not in best or item["importance"] > best[key]["importance"]:
            best[key] = item
    return list(best.values())


def rank_by_importance(items):
    """Sort items so the most important appear first. Works now."""
    return sorted(items, key=lambda x: x["importance"], reverse=True)


def summarize(items):
    """Turn the ranked items into a short daily digest using an AI model.

    NOTE: Not connected yet. Sponsored course compute (Cloudflare
    Workers AI) is still pending - see Q6. Function is structured
    and ready; only the model call needs to be filled in.
    """
    # TODO: connect to course-sponsored model here
    return "[AI summary not generated yet - compute access pending]"


if __name__ == "__main__":
    raw = fetch_items()
    deduped = remove_duplicates(raw)
    ranked = rank_by_importance(deduped)

    print("=== TODAY'S DIGEST (scaffold) ===")
    for i, item in enumerate(ranked, 1):
        print(f"{i}. [{item['source']}] {item['title']}")

    print("\nAI summary:", summarize(ranked))