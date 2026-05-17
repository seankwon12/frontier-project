# Step 1+2: informational-newsletter filter - CS 153 Frontier Systems
#
# Step 1: fetch recent inbox messages, classify each with the
#         rule-based classifier, keep only informational newsletters.
# Step 2: for those kept, fetch the full message body, extract
#         readable text, show a preview, and save the full content
#         to newsletters.json for later AI summarization.
#
# Run:  python newsletter_filter.py

import json
import sys

from gmail_auth import get_gmail_service
from classifier import classify, CATEGORY_INFORMATIONAL
from mail_body import extract_body

# Windows consoles often default to cp1252; force UTF-8 so Korean
# text and emoji in subjects/bodies print without crashing.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# How many recent inbox messages to scan.
MAX_RESULTS = 20
# How many body characters to show on screen per mail (full text is
# still saved to the output file).
PREVIEW_CHARS = 500
# Where the full informational-newsletter content is stored.
OUTPUT_FILE = "newsletters.json"


def header(message, name):
    """Return the value of a named header, or '(none)' if missing."""
    for h in message.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return "(none)"


def fetch_recent(service, max_results):
    """Return a list of message metadata dicts from the inbox.

    Each dict includes labelIds (CATEGORY_PROMOTIONS, CATEGORY_UPDATES,
    etc.) plus the From and Subject headers. This is a light request -
    no body is downloaded here.
    """
    listing = (
        service.users().messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
        .execute()
    )
    messages = []
    for ref in listing.get("messages", []):
        msg = (
            service.users().messages()
            .get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"],
            )
            .execute()
        )
        messages.append(msg)
    return messages


def fetch_body(service, msg_id):
    """Download a single message in full and return its readable body."""
    full = (
        service.users().messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )
    return extract_body(full["payload"])


def main():
    service = get_gmail_service()
    messages = fetch_recent(service, MAX_RESULTS)

    if not messages:
        print("No messages found in the inbox.")
        return

    # Step 1: classify every message; keep only informational ones.
    informational = []
    for msg in messages:
        subject = header(msg, "Subject")
        sender = header(msg, "From")
        labels = msg.get("labelIds", [])
        category, reason = classify(subject, sender, labels)
        if category == CATEGORY_INFORMATIONAL:
            informational.append(
                {"id": msg["id"], "sender": sender,
                 "subject": subject, "reason": reason}
            )

    print(
        f"=== {len(informational)} informational newsletters "
        f"out of {len(messages)} recent messages ===\n"
    )
    if not informational:
        print("No messages classified as informational newsletters.")
        return

    # Step 2: fetch the full body for each informational newsletter.
    collected = []
    for i, item in enumerate(informational, 1):
        body = fetch_body(service, item["id"])
        collected.append(
            {
                "sender": item["sender"],     # sender
                "subject": item["subject"],   # subject
                "body": body,                 # full body text
            }
        )

        preview = body[:PREVIEW_CHARS]
        truncated = len(body) > PREVIEW_CHARS
        print(f"{i}. From:    {item['sender']}")
        print(f"   Subject: {item['subject']}")
        print(f"   Reason:  {item['reason']}")
        print(f"   Body length: {len(body)} chars")
        print(f"   Preview: {preview}{' ...(truncated)' if truncated else ''}\n")

    # Save the full content for later AI summarization.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(collected)} full bodies to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
