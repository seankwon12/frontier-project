"""Group all_content.json items into clusters by semantic topic.

Current: manual clustering via Claude Code reasoning. The CLUSTERS constant
below was hand-built by Claude Code after reading every item in
all_content.json.

Items are identified by (source, subject_prefix) - NOT by raw index - so
the clustering survives content shifts across runs. When an old item ages
out of the 24h Telegram window or a new one appears, the remaining
manually-grouped items still resolve correctly. Missing members produce
a stderr warning rather than a silent miss.

Future: automated via embedding API + clustering (e.g., embed each item
with sentence-transformers or an Anthropic/OpenAI embedding endpoint,
then run agglomerative clustering or HDBSCAN on the resulting vectors).

Output schema (clusters.json):
    [
      {
        "cluster_id": int,
        "topic_label_en": str,
        "spread_score": int,   # distinct sources covering the topic
        "item_count": int,
        "items": [{ "index": int, "source": str, "origin": str,
                    "subject_snippet": str }, ...]
      },
      ...
    ]
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
INPUT_PATH = ROOT / "all_content.json"
OUTPUT_PATH = ROOT / "clusters.json"

# Multi-item clusters discovered by Claude Code.
#
# Each member is (source, subject_prefix). The prefix is matched with
# str.startswith() against the actual subject in all_content.json after
# whitespace normalization. This is stable against:
#   - items being reordered between runs
#   - subject trailing/leading whitespace differences
#   - new items appearing or old ones aging out of the 24h window
#
# Items not matched by any cluster member become singleton clusters.
CLUSTERS = [
    {
        "label": "Memory / HBM super cycle bull case (H2 2026 outlook, Wall St. upgrades)",
        "members": [
            ("선진짱 주식공부방", "삼성전자-하이닉스 해외 실시간 추정가"),
            ("루팡", "SK하이닉스, TSMC 회장, HBM 및 첨단 패키징"),
            ("루팡", "난야 테크놀로지(Nanya Technology) 5월 매출"),
            ("루팡", "하반기 메모리 전망: 듀레이션 게임"),
            ("루팡", "모건스탠리(Morgan Stanley),  마이크론(Micron)과 샌디스크"),
            ("IT의 신 이형수", "하반기 메모리 전망: 듀레이션 게임"),
            ("IT의 신 이형수", "JP모건) 메모리 시장 업데이트; NVDA 컴퓨텍스"),
        ],
    },
    {
        "label": "Korean equity market boom (KOSPI/KOSDAQ rally, Goldman 12,000 target)",
        "members": [
            ("제약/바이오/미용 원리버", "$KOSDAQ"),
            ("텔레그램 코인 방,채널 - CEN", "한국 주식 시장이 14개월 만에"),
            ("텔레그램 코인 방,채널 - CEN", "기술 붐으로 한국이 세계 6위 주식 시장으로 부상"),
            ("IT의 신 이형수", "KOSPI 12m target to 12,000"),
        ],
    },
    {
        "label": "NVIDIA Computex 2026 keynote and Wall Street takeaways",
        "members": [
            ("루팡", "Navitas, 컴퓨텍스 2026 NVIDIA MGX 생태계"),
            ("루팡", "모건스탠리(Morgan Stanley), 엔비디아( $NVDA)"),
            ("IT의 신 이형수", "Citi) NVIDIA 컴퓨텍스 2일차"),
            ("IT의 신 이형수", "6. 컴퓨트 랙을 넘어 풀스택 인프라로 확장"),
            ("IT의 신 이형수", "JP모건) 2026 Computex 시사점 Part 1"),
            ("IT의 신 이형수", "Citi) Computex 2026 핵심 시사점"),
        ],
    },
    {
        "label": "Broadcom (AVGO) Q2 FY26 earnings call",
        "members": [
            ("선진짱 주식공부방", "[SK증권 반도체 한동희"),
            ("선진짱 주식공부방", "브로드컴(AVGO) 실적 발표"),
            ("루팡", "브로드컴 2026 회계연도 2분기 어닝콜 중"),
        ],
    },
    {
        "label": "Alphabet $80B equity offering to fund AI infrastructure",
        "members": [
            ("텔레그램 코인 방,채널 - CEN", "구글, AI 사업 확장과 AI 인프라"),
            ("IT의 신 이형수", "$GOOG $GOOGL #유상증자"),
        ],
    },
    {
        "label": "Shared YouTube video reposted across two chip-focused channels",
        "members": [
            ("선진짱 주식공부방", "https://youtu.be/FggyQDN0qno"),
            ("IT의 신 이형수", "https://youtu.be/FggyQDN0qno"),
        ],
    },
    {
        "label": "Korean chip-equipment (소부장) rally and Samsung contract wins",
        "members": [
            ("선진짱 주식공부방", "[SK증권 반도체 소부장 이동주]"),
            ("선진짱 주식공부방", "[반.전] 소부장 상한가"),
            # The next two are DART disclosure messages, where the message
            # body starts with the filing timestamp. Timestamps are unique
            # per filing so they make stable keys.
            ("선진짱 주식공부방", "2026.06.04 10:24:06"),  # YEST 예스티 → Samsung
            ("선진짱 주식공부방", "2026.06.04 11:20:27"),  # EXICON 엑시콘 → Samsung
            ("선진짱 주식공부방", "귀국해서 바로 사무실로 갑니다"),
            ("선진짱 주식공부방", "오늘 반도체장비주 도쿄일렉트론"),
        ],
    },
    {
        "label": "Korean local elections live reaction (exit polls)",
        "members": [
            ("선진짱 주식공부방", "지방선거 실시간 상황"),
            ("선진짱 주식공부방", "@JTBC 당선 예측조사"),
            ("선진짱 주식공부방", "[출구조사 결과]"),
        ],
    },
    {
        "label": "D&D Pharmatech: Kiwoom briefing + co-founder stock option exercise",
        "members": [
            ("제약/바이오/미용 원리버", "[단독] 키움증권에서 디앤디파마텍"),
            ("제약/바이오/미용 원리버", "디앤디파마텍 공동창업자들 스톡옵션"),
        ],
    },
    {
        "label": "IREN data center expansion (Australia 800MW + Microsoft project DCF)",
        "members": [
            # First IREN announcement uses the bare ticker as its first line.
            ("루팡", "IREN"),
            ("루팡", "Canaccord, IREN $IREN"),
            ("루팡", "IREN, 호주 번디(Bundey)에 800MW"),
        ],
    },
]


def normalize(s):
    """Standardize whitespace for matching source/subject strings."""
    return (s or "").replace("\n", " ").strip()


def build_source_index(items):
    """Map normalized source -> list of (normalized_subject, index) pairs."""
    idx = defaultdict(list)
    for i, item in enumerate(items):
        idx[normalize(item.get("source"))].append(
            (normalize(item.get("subject")), i)
        )
    return idx


def find_index(source, subj_prefix, source_index):
    """Return the index of the first item whose source matches exactly and
    whose subject starts with subj_prefix. Returns None if no match."""
    candidates = source_index.get(normalize(source), [])
    prefix = normalize(subj_prefix)
    matches = [i for subj, i in candidates if subj.startswith(prefix)]
    if not matches:
        return None
    if len(matches) > 1:
        print(
            f"  [WARN] Ambiguous match for source={source!r}, "
            f"prefix={prefix!r}: {len(matches)} items match; taking first "
            f"(index={matches[0]}).",
            file=sys.stderr,
        )
    return matches[0]


def make_item_summary(items, idx):
    item = items[idx]
    subj = normalize(item.get("subject"))
    if len(subj) > 100:
        subj = subj[:100] + "..."
    return {
        "index": idx,
        "source": item["source"],
        "origin": item["origin"],
        "subject_snippet": subj,
    }


def auto_singleton_label(item):
    """Auto-derive a label for a singleton cluster from the item's subject.
    The label may be in the item's original language (often Korean) since
    we have no translation step. Singletons are not the focus of the
    'spread = importance' hypothesis, so this is acceptable."""
    subj = normalize(item.get("subject"))
    if not subj:
        return f"(no subject - item from {item['source']})"
    if len(subj) > 80:
        return subj[:80].rstrip() + "..."
    return subj


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    source_index = build_source_index(items)
    clusters_out = []
    used = set()
    cluster_id = 0
    total_missing = 0

    # Multi-item clusters first - resolve content-key members to indices.
    for c in CLUSTERS:
        resolved = []
        missing = []
        for source, subj_prefix in c["members"]:
            idx = find_index(source, subj_prefix, source_index)
            if idx is None:
                missing.append((source, subj_prefix))
            elif idx in used:
                print(
                    f"  [WARN] Item index={idx} (source={source!r}, "
                    f"prefix={subj_prefix!r}) already claimed by an earlier "
                    f"cluster; skipping in cluster {c['label']!r}.",
                    file=sys.stderr,
                )
            else:
                resolved.append(idx)
                used.add(idx)

        if missing:
            print(
                f"  [WARN] Cluster {c['label']!r}: "
                f"{len(missing)} member(s) not found in current data:",
                file=sys.stderr,
            )
            for source, subj_prefix in missing:
                print(f"    - source={source!r}, prefix={subj_prefix!r}",
                      file=sys.stderr)
            total_missing += len(missing)

        if not resolved:
            print(
                f"  [WARN] Cluster {c['label']!r} resolved to zero items "
                f"in current data; skipping cluster entirely.",
                file=sys.stderr,
            )
            continue

        cluster_id += 1
        cluster_items = [make_item_summary(items, i) for i in resolved]
        distinct_sources = {it["source"] for it in cluster_items}
        clusters_out.append({
            "cluster_id": cluster_id,
            "topic_label_en": c["label"],
            "spread_score": len(distinct_sources),
            "item_count": len(cluster_items),
            "items": cluster_items,
        })

    # Singletons - auto-label from the item's own subject.
    for idx in range(len(items)):
        if idx in used:
            continue
        cluster_id += 1
        clusters_out.append({
            "cluster_id": cluster_id,
            "topic_label_en": auto_singleton_label(items[idx]),
            "spread_score": 1,
            "item_count": 1,
            "items": [make_item_summary(items, idx)],
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(clusters_out, f, ensure_ascii=False, indent=2)

    spread_dist = Counter(c["spread_score"] for c in clusters_out)
    print(f"Total items:    {len(items)}")
    print(f"Total clusters: {len(clusters_out)}")
    if total_missing:
        print(f"  [NOTE] {total_missing} multi-cluster member(s) not found "
              f"in current data (manual labels may need refresh).")

    print("\nSpread-score distribution (distinct sources per cluster):")
    for score in sorted(spread_dist.keys()):
        print(f"  spread={score}: {spread_dist[score]} clusters")

    multi = [c for c in clusters_out if c["item_count"] > 1]
    print(f"\nMulti-item clusters ({len(multi)}), sorted by spread then item_count:")
    for c in sorted(multi, key=lambda x: (-x["spread_score"], -x["item_count"])):
        print(f"  [spread={c['spread_score']}, items={c['item_count']}]"
              f" {c['topic_label_en']}")

    print(f"\nSaved to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
