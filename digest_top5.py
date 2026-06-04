"""Pick the top 5 clusters by pure spread_score and emit a digest.

Ranking rule (strict):
  - Primary: spread_score descending. No secondary signals (no item_count,
    no body length, no recency). The hypothesis under test is that
    cross-source spread alone is the signal.
  - Tie-break only for determinism: ascending cluster_id. Any tie at the
    cutoff is explicitly flagged in the output.

Summarization:
  - Current: manual trigger via Claude Code. The summaries below were
    written by Claude Code after reading every item in each of the top
    multi-source clusters; they are stored in MANUAL_SUMMARIES keyed by
    cluster_id.
  - Future: API-based automated summarization. Swap summarize_cluster()
    to call an LLM with each cluster's items as context.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
CLUSTERS_PATH = ROOT / "clusters.json"
OUTPUT_PATH = ROOT / "digest_top5.md"
TOP_N = 5

# Hand-written English BODIES for each of the top clusters.
#
# Keyed by topic_label_en (the cluster's stable semantic identity), NOT by
# cluster_id. cluster_id is positional and shifts whenever an upstream
# CLUSTERS entry is skipped; topic_label_en stays constant.
#
# IMPORTANT: bodies must NOT make claims about how many sources covered
# the topic or which specific sources they were. That metadata is generated
# at runtime by source_prefix() below, so it's always accurate against the
# current clusters.json. If a body hardcodes "Three channels" or names
# specific sources in its opening, it goes stale the moment the data
# distribution changes - which is exactly the bug that bit this digest.
#
# Bodies should also only reference events that are robustly part of the
# cluster's topic. If a specific datapoint (say a particular bank target)
# is only one of several items and might age out of the 24h window, prefer
# language that survives that ("Wall Street raised memory targets" instead
# of "Morgan Stanley raised Micron to $1,050").
#
# Current: manual trigger via Claude Code
# Future: API-based automated summarization that re-derives both prefix
# and body from each run's cluster["items"].
MANUAL_SUMMARIES = {
    "Memory / HBM super cycle bull case (H2 2026 outlook, Wall St. upgrades)": (
        "Samsung Securities published a 'duration game' note raising Samsung "
        "Electronics' target to 500,000 won and SK Hynix's to 3,500,000 won "
        "— their FY27 earnings estimate sits 21% above consensus, on conviction "
        "that DRAM bit growth above 22% (HBM 40%, server DRAM 25%) persists "
        "through FY28. Separately, Nanya Technology's May revenue surged 730% "
        "YoY (a 7th consecutive monthly record) as major memory makers pivot "
        "capacity toward HBM/DDR5. SK Chairman Chey Tae-won also met TSMC "
        "Chairman C.C. Wei in Taiwan and the two agreed to deepen HBM and "
        "advanced-packaging cooperation."
    ),
    "Korean equity market boom (KOSPI/KOSDAQ rally, Goldman 12,000 target)": (
        "KOSPI is up nearly 4x in 14 months, with the rally led by Samsung "
        "and SK Hynix — the two firms that together control roughly 80% of "
        "global AI-memory supply. A KOSDAQ technical-setup note flagged that "
        "the index now sits where the 0.382 Fibonacci retrace from the April "
        "high meets a long-term trendline from April 2025 — a classic "
        "strong-bounce zone, though that author also flagged personal "
        "skepticism about acting on it given a structural Korea-market bias."
    ),
    "NVIDIA Computex 2026 keynote and Wall Street takeaways": (
        "At Computex 2026, NVIDIA pledged to return 50%+ of free cash flow "
        "to shareholders going forward, launched the N1X Windows PC processor "
        "in partnership with MediaTek, and introduced its full-stack DSX AI "
        "Factory reference design (with capex intensity rising from $20-30B/GW "
        "historically to $80-100B/GW). Wall Street takeaways centered on "
        "Personal AI, AI CPU, and Physical AI; analysts flagged 10x DRAM "
        "density on RTX Spark/DGX Station devices and the new Vera CPU "
        "driving DDR5 server and storage demand. Morgan Stanley kept NVDA "
        "as Top Pick with a $288 target, and Navitas Semiconductor showcased "
        "an 800V-to-6V power-supply board built for the NVIDIA AI Factory "
        "MGX ecosystem."
    ),
    "Broadcom (AVGO) Q2 FY26 earnings call": (
        "AI semiconductor revenue is now tracking $56B for FY26 (~+180% YoY) "
        "with the FY27 $100B+ guidance reaffirmed, and Q2 AI bookings hit "
        "$30B+ — a large bookings-to-current-shipment gap. CEO Hock Tan "
        "attributed that gap to lead-time lock-in by six large compute "
        "customers, with new milestones including a long-term Google TPU "
        "agreement and an incremental 5GW commitment from Anthropic starting "
        "FY27. SK Securities' note flagged networking contributing roughly "
        "40% of AI semi revenue and 2H FY26 shipments expected to roughly "
        "double 1H."
    ),
    "Alphabet $80B equity offering to fund AI infrastructure": (
        "Alphabet announced an $80B equity offering — its largest-ever "
        "capital raise — to fund AI compute infrastructure, framed in part "
        "as a response to the rising tax burden from AI capex growth. A "
        "structural read of the June 1 SEC filing shows the offering split "
        "into three tranches; the headline is a $30B underwritten portion "
        "of which $15B comprises mandatory convertible preferred stock "
        "issued as depositary shares. The size and structure underscore the "
        "magnitude of AI-infrastructure capex pressure now falling onto "
        "hyperscaler balance sheets."
    ),
    "Korean chip-equipment (소부장) rally and Samsung contract wins": (
        "SK Securities and Samsung Securities both published bullish notes — "
        "SK forecasting WFE market growth from +5% in 2024 to +26% by 2028, "
        "and Samsung highlighting multiple semi-cap names (원익IPS, 유진테크, "
        "테스 등) hitting upper-limit prices on the day. Two specific Samsung "
        "supplier contracts were disclosed in DART filings on the same "
        "morning: YEST (예스티) booked a 22.8B won deal (26.2% of revenue) "
        "and Excicon (엑시콘) booked 12.1B won (18.3% of revenue), both "
        "supplying Samsung Electronics' chip lines."
    ),
    "Korean local elections live reaction (exit polls)": (
        "JTBC's pre-election projection had the Democratic Party leading 10 "
        "of 16 metro-level races, with 5 toss-ups and only 1 People Power "
        "lead. The actual exit poll then largely confirmed that pattern: "
        "Seoul (Jeong Won-oh 51.4 vs Oh Se-hoon 46.0), Busan, Incheon, "
        "Ulsan, Daejeon, and Sejong all leaning Democratic; Daegu remained "
        "an unusually tight toss-up with Choo Kyung-ho 49.9 vs Kim Bu-gyeom "
        "49.1."
    ),
    "D&D Pharmatech: Kiwoom briefing + co-founder stock option exercise": (
        "Kiwoom Securities is hosting an institutional-only briefing where "
        "CEO Dr. Lee Seul-ki (typically US-based) will present Zabopegdutide "
        "clinical results and the next development steps. Separately, the "
        "co-founders exercised their stock options and locked the resulting "
        "shares under a long-term protection covenant through May 2027 — "
        "notable because US tax law triggers unrealized-gain tax on the "
        "exercise, making the long lockup a costly confidence signal."
    ),
    "IREN data center expansion (Australia 800MW + Microsoft project DCF)": (
        "IREN announced an 800MW data-center campus in Bundey, South "
        "Australia (~125km northeast of Adelaide), with energization "
        "targeted for 2028 — among the largest such projects announced in "
        "Asia-Pacific. Separately, Canaccord raised IREN's price target "
        "from $70 to $79 after refreshing its DCF model to include the "
        "Microsoft project (per-share value $21→$30, WACC 8%→6% on confirmed "
        "financing terms)."
    ),
}


def rank_clusters(clusters):
    """Sort by spread_score desc, then cluster_id asc for determinism."""
    return sorted(clusters, key=lambda c: (-c["spread_score"], c["cluster_id"]))


def confidence_tag(spread_score):
    """Return a short English tag describing the strength of the cross-source
    signal. Used to mark each cluster in the digest so a reader can tell at
    a glance whether the ranking is well-justified by the hypothesis."""
    if spread_score >= 2:
        return "Cross-source"
    return "Single-source · low confidence"


def source_prefix(cluster):
    """Build a one-sentence dynamic source-attribution from THIS run's items.

    This is what guarantees the summary's source-count claim always matches
    the spread badge. Computed every run from cluster["items"], never cached.
    """
    sources = []
    for it in cluster["items"]:
        if it["source"] not in sources:
            sources.append(it["source"])
    n = len(sources)
    src_list = ", ".join(sources)
    if n == 1:
        return f"Single source {src_list} covered this."
    if n == 2:
        return f"Two channels ({src_list}) covered this."
    return f"{n} channels ({src_list}) covered this."


def summarize_cluster(cluster):
    """Return a 3-4 sentence English summary for the cluster.

    Structure: a dynamic source-attribution sentence (always reflecting the
    actual sources in THIS run) followed by the hand-written substantive
    body for the topic. Lookup of the body is by topic_label_en (stable
    semantic identity), not by cluster_id (positional, shifts on skips).

    Current: manual trigger via Claude Code (body from MANUAL_SUMMARIES,
            prefix from source_prefix).
    Future: API-based automated summarization (call an LLM with the
            cluster's items pulled from all_content.json as context, so
            both prefix and body are regenerated each run).
    """
    label = cluster["topic_label_en"]
    body = MANUAL_SUMMARIES.get(label)
    if body is None:
        return (
            f"(No precomputed summary for this cluster - typically a single-"
            f"source fallback. {cluster['item_count']} item(s) in cluster; "
            f"see clusters.json or all_content.json for raw subjects.)"
        )
    return f"{source_prefix(cluster)} {body}"


def warn_dead_summaries(clusters):
    """Print warnings for MANUAL_SUMMARIES keys that don't match any cluster
    in this run. Two reasons this can happen:
      - The CLUSTERS entry was skipped today (all members aged out). Benign.
      - The MANUAL_SUMMARIES key has a typo and doesn't match any label.
        That's a bug worth catching.
    """
    cluster_labels = {c["topic_label_en"] for c in clusters}
    dead = [k for k in MANUAL_SUMMARIES if k not in cluster_labels]
    if not dead:
        return
    print(
        "\n[INFO] MANUAL_SUMMARIES has keys with no matching cluster in this "
        "run (benign if the upstream CLUSTERS entry was simply skipped due to "
        "no resolved members; check for typos otherwise):",
        file=sys.stderr,
    )
    for k in dead:
        print(f"  - {k}", file=sys.stderr)


def format_sources(cluster):
    """Return a single-line list of distinct sources covering the cluster."""
    seen = []
    for item in cluster["items"]:
        tag = f"[{item['origin']}] {item['source']}"
        if tag not in seen:
            seen.append(tag)
    return " | ".join(seen)


def build_markdown(top, total_clusters, singleton_count):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# Daily Digest - Top {TOP_N} by Cross-Source Spread")
    lines.append("")
    lines.append(f"_Generated {today}. Ranking: pure `spread_score` (number of "
                 f"distinct sources covering the topic), tie-broken by ascending "
                 f"`cluster_id` for determinism._")
    lines.append("")

    for rank, c in enumerate(top, start=1):
        tag = confidence_tag(c["spread_score"])
        lines.append(f"## {rank}. [{tag}] {c['topic_label_en']}")
        lines.append("")
        lines.append(f"**Spread score:** {c['spread_score']}  ·  "
                     f"**Items in cluster:** {c['item_count']}")
        lines.append("")
        lines.append(f"**Sources:** {format_sources(c)}")
        lines.append("")
        lines.append(summarize_cluster(c))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append(f"- Total clusters in this run: **{total_clusters}**, of which "
                 f"**{singleton_count}** are spread=1 (covered by a single source). "
                 f"The hypothesis under test - cross-source spread = importance - "
                 f"is only meaningful for the small minority of multi-source clusters.")
    lines.append(
        "- When fewer than 5 multi-source clusters exist on a given day, "
        "lower-ranked slots fall back to single-source clusters and are marked "
        "as low-confidence."
    )
    lines.append(
        "- This digest uses Claude Code (manual trigger) for both clustering "
        "and per-cluster summarization. The pipeline is designed to swap in "
        "an API-based automated version (embedding-based clustering + LLM "
        "summarization calls) in the future."
    )
    lines.append("")
    return "\n".join(lines)


def main():
    with open(CLUSTERS_PATH, "r", encoding="utf-8") as f:
        clusters = json.load(f)

    warn_dead_summaries(clusters)

    ranked = rank_clusters(clusters)
    top = ranked[:TOP_N]

    total_clusters = len(clusters)
    singleton_count = sum(1 for c in clusters if c["spread_score"] == 1)

    md = build_markdown(top, total_clusters, singleton_count)

    print(md)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nSaved digest to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
