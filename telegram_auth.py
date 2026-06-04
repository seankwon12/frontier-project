"""Load Telegram API credentials from a local JSON file.

Credentials must NEVER be hardcoded. The user creates
telegram_credentials.json manually with their real api_id and api_hash
obtained from https://my.telegram.org (Desktop app type).
"""

import json
import sys
from pathlib import Path

CREDENTIALS_PATH = Path(__file__).parent / "telegram_credentials.json"
SESSION_NAME = "telegram_session"


def load_credentials():
    """Return (api_id, api_hash) read from telegram_credentials.json."""
    if not CREDENTIALS_PATH.exists():
        print(
            f"[ERROR] {CREDENTIALS_PATH.name} not found.\n"
            "Create it next to this script with the following shape:\n"
            '{\n'
            '  "api_id": 1234567,\n'
            '  "api_hash": "0123456789abcdef0123456789abcdef"\n'
            '}\n'
            "Get these values from https://my.telegram.org (Desktop app type)."
        )
        sys.exit(1)

    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_id = data.get("api_id")
    api_hash = data.get("api_hash")

    if api_id is None or api_hash is None:
        print("[ERROR] telegram_credentials.json must contain 'api_id' and 'api_hash'.")
        sys.exit(1)

    if not isinstance(api_id, int):
        print("[ERROR] 'api_id' must be an integer (no quotes).")
        sys.exit(1)

    return api_id, api_hash
