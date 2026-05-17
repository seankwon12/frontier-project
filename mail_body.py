# Mail body extraction - CS 153 Frontier Systems
#
# Pulls a readable plain-text body out of a Gmail message payload.
# Uses only the Python standard library (base64, html.parser, html, re):
#   - decodes Gmail's base64url-encoded body data
#   - walks the MIME tree, preferring a text/plain part
#   - falls back to stripping tags from a text/html part

import base64
import re
from html.parser import HTMLParser

# Tags whose text content should be dropped entirely.
_SKIP_TAGS = {"script", "style", "head", "title"}

# Block-level tags: emit a line break around them so the stripped
# text keeps some structure instead of running together.
_BLOCK_TAGS = {
    "p", "div", "br", "li", "tr", "ul", "ol", "table", "blockquote",
    "section", "header", "footer", "article", "h1", "h2", "h3", "h4",
    "h5", "h6",
}


def _decode(data):
    """Decode Gmail's base64url body data into a string."""
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data.encode("utf-8"))
    return raw.decode("utf-8", errors="replace")


class _HTMLTextExtractor(HTMLParser):
    """Collects human-readable text from an HTML document."""

    def __init__(self):
        # convert_charrefs=True auto-decodes entities like &amp; &#39;.
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self.parts.append(data)


def strip_html(html_text):
    """Return readable text from an HTML string (tags removed)."""
    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()
    return "".join(parser.parts)


def _clean(text):
    """Collapse stray whitespace and blank lines into tidy text."""
    # Drop zero-width chars; turn non-breaking spaces into normal ones.
    text = text.replace("‌", "").replace("​", "").replace("\xa0", " ")

    cleaned = []
    blank_run = False
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            cleaned.append(line)
            blank_run = False
        elif not blank_run:
            # Keep at most one blank line between paragraphs.
            cleaned.append("")
            blank_run = True
    return "\n".join(cleaned).strip()


def _collect_parts(payload, plain, html):
    """Walk the MIME tree, appending decoded text to the given lists."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data")

    if mime == "text/plain" and data:
        plain.append(_decode(data))
    elif mime == "text/html" and data:
        html.append(_decode(data))

    for part in payload.get("parts", []):
        _collect_parts(part, plain, html)


def extract_body(payload):
    """Return the readable plain-text body of a Gmail message payload.

    Prefers any text/plain part; otherwise strips tags from text/html.
    Returns an empty string if no text body is found.
    """
    plain, html = [], []
    _collect_parts(payload, plain, html)

    if plain:
        text = "\n".join(plain)
    elif html:
        text = strip_html("\n".join(html))
    else:
        text = ""
    return _clean(text)
