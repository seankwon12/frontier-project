# Gmail connection test - CS 153 Frontier Systems
# Fetches the 10 most recent inbox messages and prints just the
# sender and subject of each, to confirm OAuth + Gmail API work.
#
# Run:  python gmail_test.py
# First run opens a browser to log in; later runs reuse token.json.

import sys

from gmail_auth import get_gmail_service

# Windows consoles often default to a non-UTF-8 code page (cp1252),
# which crashes when printing Korean text or emoji in mail subjects.
# Force UTF-8 output so any character prints safely.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def header(message, name):
    """Return the value of a named header, or '(none)' if missing."""
    for h in message.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return "(none)"


def main():
    service = get_gmail_service()

    # Get the 10 most recent message IDs from the inbox.
    result = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=10)
        .execute()
    )
    messages = result.get("messages", [])

    if not messages:
        print("No messages found in the inbox.")
        return

    print(f"=== {len(messages)} most recent inbox messages ===\n")
    for i, ref in enumerate(messages, 1):
        # Fetch only the headers we need, not the full body.
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"],
            )
            .execute()
        )
        sender = header(msg, "From")
        subject = header(msg, "Subject")
        print(f"{i}. From:    {sender}")
        print(f"   Subject: {subject}\n")


if __name__ == "__main__":
    main()
