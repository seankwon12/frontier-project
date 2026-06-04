"""Run the full daily-digest pipeline end-to-end.

Steps (executed in order):
  1. newsletter_filter.py   - fetch + classify + extract Gmail bodies
  2. telegram_fetch.py      - fetch last 24h of configured Telegram channels
  3. merge_sources.py       - combine sources into all_content.json
  4. cluster_content.py     - manual-trigger clustering by Claude Code
  5. digest_top5.py         - rank by spread, summarize, write digest_top5.md
  6. build_digest_html.py   - render digest.html

Fails LOUDLY on any non-zero exit code. Does NOT silently fall back to
cached data - cached data can hide real problems (expired OAuth tokens,
network issues, channels that stopped working) that would otherwise
silently degrade the pipeline.

For step 1 (newsletter_filter) failures, prints an explicit re-auth hint
since OAuth token expiry is the most common failure mode.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

STEPS = [
    ("newsletter_filter.py", "Gmail fetch + classify + extract bodies"),
    ("telegram_fetch.py",    "Telegram last 24h fetch"),
    ("merge_sources.py",     "Merge Gmail + Telegram into all_content.json"),
    ("cluster_content.py",   "Cluster items (manual trigger via Claude Code)"),
    ("digest_top5.py",       "Rank by spread, summarize, write digest_top5.md"),
    ("build_digest_html.py", "Render digest.html"),
]


def header(text):
    bar = "=" * 72
    return f"\n{bar}\n{text}\n{bar}"


def loud_failure_banner(step_num, total, script, returncode):
    bar = "!" * 72
    print()
    print(bar)
    print(f"!! PIPELINE FAILED at step {step_num}/{total}: {script}")
    print(f"!! Script exited with code {returncode}")
    print(f"!! No fallback - subsequent steps will NOT run.")
    print(bar)


def main():
    total = len(STEPS)
    for i, (script, desc) in enumerate(STEPS, start=1):
        print(header(f"[STEP {i}/{total}: {script}]  {desc}"))

        script_path = ROOT / script
        if not script_path.exists():
            loud_failure_banner(i, total, script, -1)
            print(f"Script not found at: {script_path}")
            sys.exit(1)

        # Inherit stdout/stderr so the user sees live progress and any
        # traceback from the failing script in real time.
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
        )

        if result.returncode != 0:
            loud_failure_banner(i, total, script, result.returncode)

            if script == "newsletter_filter.py":
                print()
                print("If this is an OAuth/token issue (expired or revoked "
                      "token, common after ~7 days), re-authenticate:")
                print()
                print("    del token.json")
                print("    python newsletter_filter.py")
                print()
                print("This deletes the cached token and forces a fresh "
                      "browser OAuth flow.")

            sys.exit(result.returncode)

    print(header("Pipeline complete. Open digest.html."))


if __name__ == "__main__":
    main()
