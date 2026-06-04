"""Render today's digest as a single static HTML file (digest.html).

Reads:
  - all_content.json (for input stats)
  - clusters.json (for cluster items and metadata)
  - Imports ranking logic + MANUAL_SUMMARIES from digest_top5.py so the
    summary text never diverges from the markdown digest.

Output:
  - digest.html (no server needed — open by double-clicking in a browser)

Pure HTML + inline CSS, no external JS, no Google Fonts, no build step.
"""

import html
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from digest_top5 import (
    TOP_N,
    rank_clusters,
    summarize_cluster,
    confidence_tag,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
ALL_CONTENT_PATH = ROOT / "all_content.json"
CLUSTERS_PATH = ROOT / "clusters.json"
OUTPUT_PATH = ROOT / "digest.html"


CSS = """
:root {
  --accent: #2563eb;
  --ink: #1f2937;
  --ink-muted: #6b7280;
  --bg: #ffffff;
  --card-bg: #ffffff;
  --border: #e5e7eb;
  --chip-bg: #f3f4f6;
  --muted-bg: #f9fafb;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, "Apple SD Gothic Neo",
               "Malgun Gothic", "Noto Sans KR", sans-serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.55;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 48px 24px 64px;
}
header h1 {
  margin: 0 0 6px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
}
header .date {
  color: var(--ink-muted);
  font-size: 14px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 32px 0 48px;
}
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}
.stat-card .label {
  font-size: 11px;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 8px;
  font-weight: 600;
}
.stat-card .value {
  font-size: 26px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.1;
}
.stat-card .sub {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 4px;
}

section.top > h2 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--ink-muted);
  margin: 0 0 16px;
  font-weight: 700;
}

.cluster-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 18px;
  background: var(--card-bg);
}
.cluster-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.rank {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-muted);
  min-width: 28px;
  line-height: 1.2;
}
.topic {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
}
.badges {
  display: flex;
  gap: 6px;
  margin: 14px 0 0 42px;
  flex-wrap: wrap;
}
.badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.badge.spread {
  background: var(--accent);
  color: white;
}
.badge.single {
  background: transparent;
  color: var(--ink-muted);
  border: 1px solid var(--border);
}
.badge.items {
  background: var(--chip-bg);
  color: var(--ink);
}
.sources {
  margin: 14px 0 0 42px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.source-chip {
  font-size: 11px;
  background: var(--chip-bg);
  color: var(--ink);
  padding: 4px 9px;
  border-radius: 4px;
  font-weight: 500;
}
.source-chip .origin {
  color: var(--ink-muted);
  font-weight: 700;
  margin-right: 6px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.summary {
  margin: 18px 0 0 42px;
  font-size: 15px;
  color: var(--ink);
  line-height: 1.65;
}

.limitations {
  background: var(--muted-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  color: var(--ink-muted);
  margin-top: 36px;
}
.limitations h2 {
  margin: 0 0 14px;
  color: var(--ink);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 700;
}
.limitations ul {
  margin: 0;
  padding-left: 18px;
}
.limitations li {
  margin-bottom: 10px;
  font-size: 14px;
  line-height: 1.6;
}
.limitations li:last-child { margin-bottom: 0; }
.limitations strong { color: var(--ink); }

footer {
  text-align: center;
  color: var(--ink-muted);
  font-size: 12px;
  margin-top: 32px;
}
"""


def compute_stats(items, clusters):
    by_origin = Counter(item["origin"] for item in items)
    return {
        "total_items": len(items),
        "gmail_items": by_origin.get("gmail", 0),
        "telegram_items": by_origin.get("telegram", 0),
        "distinct_sources": len({item["source"] for item in items}),
        "total_clusters": len(clusters),
        "multi_source": sum(1 for c in clusters if c["spread_score"] >= 2),
        "singleton": sum(1 for c in clusters if c["spread_score"] == 1),
    }


def distinct_sources_for_cluster(cluster):
    """Return ordered list of (origin, source) pairs for chip rendering."""
    seen = []
    for item in cluster["items"]:
        key = (item["origin"], item["source"])
        if key not in seen:
            seen.append(key)
    return seen


def short_source(name, max_len=40):
    """Trim long Gmail sender strings like 'Name <addr@x>' for chips."""
    if len(name) <= max_len:
        return name
    return name[:max_len - 1] + "..."


def render_html(today_str, ts_str, stats, top):
    e = html.escape
    out = []
    out.append("<!DOCTYPE html>")
    out.append('<html lang="en">')
    out.append("<head>")
    out.append('<meta charset="UTF-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    out.append("<title>Daily Digest</title>")
    out.append(f"<style>{CSS}</style>")
    out.append("</head>")
    out.append("<body>")
    out.append('<div class="container">')

    # Header
    out.append("<header>")
    out.append("<h1>Daily Digest</h1>")
    out.append(f'<div class="date">{e(today_str)}</div>')
    out.append("</header>")

    # Stats strip
    stat_cards = [
        ("Total items", stats["total_items"], "analyzed"),
        ("Gmail", stats["gmail_items"], "newsletters"),
        ("Telegram", stats["telegram_items"], "messages"),
        ("Distinct sources", stats["distinct_sources"], "channels + senders"),
        ("Total clusters", stats["total_clusters"], "formed"),
        ("Multi-source", stats["multi_source"], "spread &ge; 2"),
        ("Singletons", stats["singleton"], "spread = 1"),
    ]
    out.append('<div class="stats">')
    for label, value, sub in stat_cards:
        out.append('<div class="stat-card">')
        out.append(f'<div class="label">{e(label)}</div>')
        out.append(f'<div class="value">{value}</div>')
        out.append(f'<div class="sub">{sub}</div>')
        out.append("</div>")
    out.append("</div>")

    # Top 5
    out.append('<section class="top">')
    out.append(f"<h2>Top {len(top)} by cross-source spread</h2>")
    for rank, c in enumerate(top, start=1):
        out.append('<div class="cluster-card">')
        out.append('<div class="cluster-header">')
        out.append(f'<div class="rank">{rank}.</div>')
        out.append(f'<div class="topic">{e(c["topic_label_en"])}</div>')
        out.append("</div>")

        out.append('<div class="badges">')
        if c["spread_score"] >= 2:
            out.append(
                f'<span class="badge spread">Cross-source &middot; '
                f'spread {c["spread_score"]}</span>'
            )
        else:
            out.append(
                '<span class="badge single">Single-source &middot; '
                'low confidence</span>'
            )
        out.append(f'<span class="badge items">{c["item_count"]} items</span>')
        out.append("</div>")

        out.append('<div class="sources">')
        for origin, source in distinct_sources_for_cluster(c):
            out.append(
                '<span class="source-chip">'
                f'<span class="origin">{e(origin)}</span>'
                f'{e(short_source(source))}'
                "</span>"
            )
        out.append("</div>")

        summary_text = summarize_cluster(c)
        out.append(f'<div class="summary">{e(summary_text)}</div>')
        out.append("</div>")
    out.append("</section>")

    # Limitations
    out.append('<div class="limitations">')
    out.append("<h2>Limitations</h2>")
    out.append("<ul>")
    out.append(
        f"<li>Total clusters in this run: <strong>{stats['total_clusters']}</strong>, "
        f"of which <strong>{stats['singleton']}</strong> are spread=1 (covered by a "
        f"single source). The hypothesis under test &mdash; cross-source spread = "
        f"importance &mdash; is only meaningful for the small minority of "
        f"multi-source clusters.</li>"
    )
    out.append(
        "<li>When fewer than 5 multi-source clusters exist on a given day, "
        "lower-ranked slots fall back to single-source clusters and are marked "
        "as low-confidence.</li>"
    )
    out.append(
        "<li>This digest uses Claude Code (manual trigger) for both clustering "
        "and per-cluster summarization. The pipeline is designed to swap in an "
        "API-based automated version (embedding-based clustering + LLM "
        "summarization calls) in the future.</li>"
    )
    out.append("</ul>")
    out.append("</div>")

    # Footer
    out.append(f"<footer>Generated {e(ts_str)}</footer>")

    out.append("</div>")
    out.append("</body>")
    out.append("</html>")
    return "\n".join(out)


def main():
    with open(ALL_CONTENT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    with open(CLUSTERS_PATH, "r", encoding="utf-8") as f:
        clusters = json.load(f)

    stats = compute_stats(items, clusters)
    ranked = rank_clusters(clusters)
    top = ranked[:TOP_N]

    now = datetime.now()
    today_str = now.strftime("%B %d, %Y")
    ts_str = now.strftime("%Y-%m-%d %H:%M")

    page = render_html(today_str, ts_str, stats, top)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Wrote {OUTPUT_PATH.name}")
    print(f"  Items:    {stats['total_items']} ({stats['gmail_items']} gmail, "
          f"{stats['telegram_items']} telegram)")
    print(f"  Sources:  {stats['distinct_sources']} distinct")
    print(f"  Clusters: {stats['total_clusters']} total, "
          f"{stats['multi_source']} multi-source, {stats['singleton']} singletons")
    print(f"  Top {len(top)}:    " +
          ", ".join(f"#{c['cluster_id']}" for c in top))


if __name__ == "__main__":
    main()
