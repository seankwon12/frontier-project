# Newsletter classifier - CS 153 Frontier Systems
#
# Rule-based classification of a Gmail message into one of three
# buckets, using only deterministic signals (no external AI):
#
#   "informational" - informational newsletters (news, digests, content)
#   "promotion"     - promotions and ads (sales, coupons, deals)
#   "personal"      - personal/system mail (notifications, account mail)
#
# Signals used: Gmail category labels, sender domain, subject keywords.
#
# NOTE: This is the v1 rule-based version. The keyword/domain lists
# and the rule order below are deliberately kept small and separate
# so they are easy to tweak. Planned next step: upgrade to AI-based
# classification.

CATEGORY_INFORMATIONAL = "informational"
CATEGORY_PROMOTION = "promotion"
CATEGORY_PERSONAL = "personal"

# --- Rule inputs: edit these lists to tune the v1 classifier ---

# Subject keywords that strongly indicate a promotion / ad.
PROMO_KEYWORDS = [
    "sale", "% off", " off ", "off select", "deal", "deals", "coupon",
    "discount", "clearance", "save $", "save up to", "lowest price",
    "할인", "쿠폰", "특가", "세일", "프로모션", "최저가", "사은품",
]

# Subject keywords that indicate a personal / system / account mail.
SYSTEM_KEYWORDS = [
    "security alert", "verify", "verification", "sign-in", "sign in",
    "password", "receipt", "invoice", "보안", "개인정보", "약관",
    "인증", "결제", "영수증", "안내",
]

# Sender substrings that indicate an automated / system address.
SYSTEM_SENDER_HINTS = [
    "no-reply", "noreply", "notifications@", "notification@",
    "accounts.google.com", "donotreply",
]

# Sender substrings that indicate a newsletter platform / publisher.
NEWSLETTER_SENDER_HINTS = [
    "newsletter", "beehiiv", "stibee", "substack", "mailchimp",
    "mailerlite", "ghost.io", "news@", "digest", "weekly",
]


def _find_keyword(text, keywords):
    """Return the first keyword from `keywords` found in `text`, else None."""
    for kw in keywords:
        if kw in text:
            return kw
    return None


def _find_sender_hint(sender, hints):
    """Return the first hint substring found in `sender`, else None."""
    for hint in hints:
        if hint in sender:
            return hint
    return None


def classify(subject, sender, labels):
    """Classify one message. Returns (category, reason).

    `category` is one of the CATEGORY_* constants above.
    `reason`   is a short human-readable explanation (English).

    Rules are applied in priority order; the first match wins.
    """
    subject_l = (subject or "").lower()
    sender_l = (sender or "").lower()
    labels = set(labels or [])

    # Rule 1: personal/system mail flagged by a subject keyword.
    kw = _find_keyword(subject_l, SYSTEM_KEYWORDS)
    if kw:
        return (CATEGORY_PERSONAL,
                f"Subject contains system/account keyword '{kw}'")

    # Rule 2: promotion flagged by a subject keyword.
    kw = _find_keyword(subject_l, PROMO_KEYWORDS)
    if kw:
        return (CATEGORY_PROMOTION,
                f"Subject contains promotion keyword '{kw.strip()}'")

    # Newsletter senders get the benefit of the doubt in later rules,
    # so detect that signal once up front.
    newsletter_hint = _find_sender_hint(sender_l, NEWSLETTER_SENDER_HINTS)

    # Rule 3: automated/system sender (unless it's a newsletter platform).
    system_hint = _find_sender_hint(sender_l, SYSTEM_SENDER_HINTS)
    if system_hint and not newsletter_hint:
        return (CATEGORY_PERSONAL,
                f"Automated/system sender address ('{system_hint}')")

    # Rule 4: Gmail's own Personal/Social category.
    if ("CATEGORY_PERSONAL" in labels or "CATEGORY_SOCIAL" in labels) \
            and not newsletter_hint:
        return (CATEGORY_PERSONAL, "Gmail category: Personal/Social")

    # Rule 5: recognised newsletter platform or publisher domain.
    if newsletter_hint:
        return (CATEGORY_INFORMATIONAL,
                f"Newsletter sender signal ('{newsletter_hint}')")

    # Rule 6: Gmail's Updates/Forums category -> treat as informational.
    if "CATEGORY_UPDATES" in labels or "CATEGORY_FORUMS" in labels:
        return (CATEGORY_INFORMATIONAL, "Gmail category: Updates/Forums")

    # Rule 7: Gmail's Promotions category with no other signal.
    if "CATEGORY_PROMOTIONS" in labels:
        return (CATEGORY_PROMOTION, "Gmail category: Promotions")

    # Default: no strong signal -> treat as personal so it is not
    # mistaken for a curated newsletter.
    return (CATEGORY_PERSONAL, "No strong classification signal (default)")
