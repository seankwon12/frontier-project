"""Minimal Telegram connection test.

On first run, Telethon prompts in the terminal for:
  1. Your phone number (international format, e.g. +821012345678)
  2. The 5-digit login code Telegram sends to your app
  3. Optionally, a 2FA password if you have one enabled

After successful login, Telethon writes telegram_session.session next to
this script so subsequent runs do not require re-entering the code.

This script only lists the 5 most recent dialogs (title + id). It does
NOT fetch any message content yet.
"""

import sys

from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat, User

from telegram_auth import SESSION_NAME, load_credentials


def dialog_type(entity):
    """Classify a dialog entity as Channel, Group, or User."""
    if isinstance(entity, User):
        return "User"
    if isinstance(entity, Chat):
        return "Group"
    if isinstance(entity, Channel):
        # broadcast=True is a one-way channel; otherwise it's a megagroup.
        return "Channel" if getattr(entity, "broadcast", False) else "Group"
    return "Unknown"

# Force UTF-8 on stdout so non-ASCII dialog titles (e.g. Korean) render
# correctly on Windows consoles that default to cp949.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def main():
    api_id, api_hash = load_credentials()

    print("Connecting to Telegram...")
    print("(First run will prompt for phone number and 5-digit login code.)")

    with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        me = client.get_me()
        print(f"\nLogged in as: {me.first_name} (@{me.username}) [id={me.id}]")

        print("\n30 most recent dialogs:")
        print("-" * 70)
        for i, dialog in enumerate(client.iter_dialogs(limit=30), start=1):
            dtype = dialog_type(dialog.entity)
            print(f"{i:>2}. [{dtype:<7}] {dialog.name}")
            print(f"     id: {dialog.id}")
        print("-" * 70)
        print("\nConnection test successful.")


if __name__ == "__main__":
    main()
