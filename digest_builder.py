# Daily digest builder - CS 153 Frontier Systems
#
# Reads the informational newsletters saved in newsletters.json,
# selects the most important items, summarizes them, and writes a
# short daily digest to the console and to digest.md.
#
# How selection + summarization works right now:
#   Current: manual trigger via Claude Code / Future: API automation
#
# The selection and summarization step is isolated in build_digest()
# so it can be swapped out later. Today, Claude Code reads the
# newsletter bodies in newsletters.json, applies the exclusion rules
# (receipts, order confirmations, event-registration solicitations),
# picks the top items, and writes the summaries - the curated result
# is encoded in build_digest() below. In the future, build_digest()
# will instead call the Claude API with the newsletter bodies and
# return the same dict structure, leaving load/render/main unchanged.

import datetime
import json
import sys

# Windows consoles often default to cp1252; force UTF-8 so any
# non-ASCII characters in the digest print without crashing.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INPUT_FILE = "newsletters.json"
OUTPUT_FILE = "digest.md"


def load_newsletters(path):
    """Load the list of informational newsletters from a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_digest(newsletters):
    """Select the most important newsletters and summarize them.

    Returns a dict with: the number of newsletters scanned, the items
    excluded as non-informational, and the top picks (each with a
    title, source, selection reason, and summary).

    Current: manual trigger via Claude Code / Future: API automation.
    The curated content below was produced by Claude Code reading the
    bodies in newsletters.json. To automate, replace the body of this
    function with a Claude API call that returns the same dict shape.
    """
    return {
        "total_scanned": len(newsletters),
        "excluded": [
            "Heisenberg membership - order/payment confirmation (receipt)",
            "Forbes 'Register Now' - member-event registration solicitation",
            "Substack 'posted new notes' - social activity notification, "
            "not curated content",
        ],
        "top_items": [
            {
                "title": "The Sunday Times - Editor's Choice",
                "source": "The Sunday Times "
                          "<noreply@newsletter.thetimes.com>",
                "reason": "The only hard-news current-affairs briefing in "
                          "today's batch - the fastest way to stay current "
                          "on major UK and world developments.",
                "summary": (
                    "The Sunday Times editor's briefing leads on UK Prime "
                    "Minister Keir Starmer, whose premiership nearly "
                    "collapsed last week but who has held on - at the cost "
                    "of Greater Manchester mayor Andy Burnham preparing to "
                    "run for parliament and challenge for the leadership. "
                    "Former health secretary Wes Streeting has also said he "
                    "would stand in any leadership contest, calling for the "
                    "UK to rejoin the EU. The issue publishes the annual "
                    "Sunday Times Rich List, reporting that a growing number "
                    "of the super-wealthy are leaving Britain. Other "
                    "features include a renewed UK-US dispute over the "
                    "Falkland Islands and an investigation tied to the 2019 "
                    "death of Zac Brettler."
                ),
            },
            {
                "title": "Road To Carry - Bain's Play in Road Safety",
                "source": "Road To Carry Newsletter "
                          "<roadtocarrynewsletter@mail.beehiiv.com>",
                "reason": "A substantive private-equity deal analysis "
                          "showing how investors create value in "
                          "overlooked, fragmented markets - high signal for "
                          "a finance-oriented reader.",
                "summary": (
                    "This Road To Carry issue is a reshared deep-dive into "
                    "private equity's expansion into unglamorous "
                    "infrastructure niches, built around Bain Capital "
                    "putting serious money into a company that literally "
                    "paints lines on highways. It argues that 'frontline "
                    "road safety' is an attractive, highly fragmented "
                    "industry well suited to a PE roll-up strategy, and "
                    "walks through the acquisition thesis for it. It is a "
                    "useful illustration of how sophisticated investors find "
                    "returns in low-glamour, overlooked markets. The issue "
                    "also contains a promotional block for RTC's June "
                    "'Accelerator' program, which is a course solicitation "
                    "rather than news."
                ),
            },
            {
                "title": "Not Boring - Cowboy Space Corporation",
                "source": "Not Boring <notboring@substack.com>",
                "reason": "A timely startup case study (a $200M raise this "
                          "week) on differentiation and storytelling - "
                          "directly useful for anyone building or pitching "
                          "a company.",
                "summary": (
                    "Not Boring's Packy McCormick breaks down 'Cowboy Space "
                    "Corporation,' a rebrand of Robinhood co-founder Baiju "
                    "Bhatt's startup Aetherflux, which has raised over $200 "
                    "million to build rockets whose upper stages unfold into "
                    "solar-powered, foldable data centers in orbit. He uses "
                    "it as a case study in differentiation and storytelling, "
                    "arguing that the company's deliberately strange "
                    "branding - cowboy hats, tumbleweeds, 'The High "
                    "Frontier' - is itself a competitive strategy in a "
                    "launch market dominated by SpaceX. The takeaway is that "
                    "how a company tells its story can matter as much as its "
                    "technology, especially when challenging an entrenched "
                    "incumbent. It is a short, informal piece following up "
                    "on his earlier essay 'The Great Differentiation.'"
                ),
            },
        ],
    }


def render_digest(digest):
    """Render the digest dict as Markdown text (English)."""
    today = datetime.date.today().isoformat()
    lines = [
        f"# Today's Digest - {today}",
        "",
        f"_Built from {digest['total_scanned']} newsletters in {INPUT_FILE} "
        f"({len(digest['excluded'])} excluded as non-informational, "
        f"{len(digest['top_items'])} selected)._",
        "",
        "## Top 3 to read today",
        "",
    ]
    for i, item in enumerate(digest["top_items"], 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append("")
        lines.append(f"**Source:** {item['source']}")
        lines.append("")
        lines.append(f"**Why read it:** {item['reason']}")
        lines.append("")
        lines.append(item["summary"])
        lines.append("")
    lines.append("## Excluded as non-informational")
    lines.append("")
    for note in digest["excluded"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main():
    newsletters = load_newsletters(INPUT_FILE)
    digest = build_digest(newsletters)
    text = render_digest(digest)

    print(text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved digest to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
