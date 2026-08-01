#!/usr/bin/env python3
"""Inject data-i18n attributes into index.html from js/i18n-dict.json (or .js).

Matches exact Spanish (es) strings on leaf elements and selected attributes.
Preserves HTML formatting via regex/stdlib path (avoids BeautifulSoup reformat).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
JSON_PATH = ROOT / "js" / "i18n-dict.json"
JS_PATH = ROOT / "js" / "i18n-dict.js"

# Prefer more specific / longer keys when the same Spanish string maps to many keys.
KEY_PRIORITY = (
    "brand.",
    "nav.",
    "hero.",
    "banner.",
    "skip",
    "meta.",
    "footer.",
    "sec.",
)


def load_dict() -> dict[str, dict[str, str]]:
    if JSON_PATH.is_file():
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    text = JS_PATH.read_text(encoding="utf-8")
    m = re.search(r"window\.I18N_DICT\s*=\s*(\{.*\})\s*;?\s*\Z", text, re.S)
    if not m:
        raise SystemExit(f"Could not parse I18N_DICT from {JS_PATH}")
    return json.loads(m.group(1))


def norm_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def key_rank(key: str) -> tuple[int, int, str]:
    for i, prefix in enumerate(KEY_PRIORITY):
        if key.startswith(prefix) or key == prefix:
            return (i, len(key), key)
    return (len(KEY_PRIORITY), len(key), key)


def pick_key(candidates: list[str]) -> str:
    return sorted(candidates, key=key_rank)[0]


def is_template(es: str) -> bool:
    return bool(re.search(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", es))


def inject_stdlib(html: str, by_es: dict[str, list[str]]) -> tuple[str, int]:
    """Regex-based leaf element tagging; preserves original formatting."""
    script_style = [
        (m.start(), m.end())
        for m in re.finditer(r"<(script|style)\b[^>]*>.*?</\1>", html, flags=re.I | re.S)
    ]

    def in_skip(pos: int) -> bool:
        return any(s <= pos < e for s, e in script_style)

    replacements: list[tuple[int, int, str]] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(a: int, b: int) -> bool:
        return any(a < e and b > s for s, e in occupied)

    def accept(s: int, e: int, frag: str) -> None:
        if overlaps(s, e):
            return
        replacements.append((s, e, frag))
        occupied.append((s, e))

    tag_re = re.compile(
        r"<(?P<tag>[a-zA-Z][\w:-]*)(?P<attrs>[^>]*)>(?P<body>[^<]*)</(?P=tag)\s*>",
        re.S,
    )

    # Longest Spanish strings first when scanning tags (order of accept is by position later)
    for m in tag_re.finditer(html):
        if in_skip(m.start()):
            continue
        attrs = m.group("attrs")
        if re.search(r"\bdata-i18n\s*=", attrs, re.I):
            continue
        body = m.group("body")
        t = norm_ws(body)
        if t not in by_es:
            continue
        key = pick_key(by_es[t])
        tag = m.group("tag")
        new_frag = f'<{tag}{attrs} data-i18n="{key}">{body}</{tag}>'
        accept(m.start(), m.end(), new_frag)

    # meta description (content attr)
    for m in re.finditer(
        r"<meta\b([^>]*\bname\s*=\s*[\"']description[\"'][^>]*)>",
        html,
        flags=re.I | re.S,
    ):
        full = m.group(0)
        if re.search(r"\bdata-i18n\s*=", full, re.I):
            continue
        cm = re.search(r"content\s*=\s*([\"'])(.*?)\1", full, re.I | re.S)
        if not cm:
            continue
        t = norm_ws(cm.group(2))
        if t not in by_es:
            continue
        key = pick_key(by_es[t])
        # i18n.js applies meta.description specially; still mark for completeness
        new_tag = full[:-1] + f' data-i18n="{key}" data-i18n-attr="content:{key}">'
        accept(m.start(), m.end(), new_tag)

    # title
    tm = re.search(r"<title([^>]*)>([^<]*)</title>", html, flags=re.I)
    if tm and not re.search(r"\bdata-i18n\s*=", tm.group(0), re.I):
        t = norm_ws(tm.group(2))
        if t in by_es:
            key = pick_key(by_es[t])
            new_tag = f'<title{tm.group(1)} data-i18n="{key}">{tm.group(2)}</title>'
            accept(tm.start(), tm.end(), new_tag)

    # Attribute-only: aria-label, placeholder, title, alt
    for attr in ("aria-label", "placeholder", "title", "alt"):
        for m in re.finditer(
            rf"<([a-zA-Z][\w:-]*)([^>]*\s{attr}=([\"'])(.*?)\3[^>]*)/?>",
            html,
            flags=re.I | re.S,
        ):
            if in_skip(m.start()):
                continue
            full = m.group(0)
            if re.search(r"\bdata-i18n-attr\s*=", full, re.I):
                continue
            if re.search(rf"\bdata-i18n-{re.escape(attr)}\s*=", full, re.I):
                continue
            t = norm_ws(m.group(4))
            if t not in by_es:
                continue
            key = pick_key(by_es[t])
            # If this opening tag span already got a text data-i18n replacement, skip
            if overlaps(m.start(), m.end()):
                continue
            # Prefer data-i18n-attr="attr:key" (matches i18n.js apply()).
            if full.endswith("/>"):
                new_tag = full[:-2].rstrip() + f' data-i18n-attr="{attr}:{key}" />'
            else:
                new_tag = full[:-1] + f' data-i18n-attr="{attr}:{key}">'
            accept(m.start(), m.end(), new_tag)

    # Apply from end to start
    result = html
    for s, e, frag in sorted(replacements, key=lambda x: x[0], reverse=True):
        result = result[:s] + frag + result[e:]

    return result, len(replacements)


def main() -> int:
    data = load_dict()
    by_es: dict[str, list[str]] = {}
    for key, entry in data.items():
        es = entry.get("es")
        if not es or is_template(es):
            continue
        n = norm_ws(es)
        by_es.setdefault(n, []).append(key)

    html = HTML_PATH.read_text(encoding="utf-8")
    out, injected = inject_stdlib(html, by_es)
    HTML_PATH.write_text(out, encoding="utf-8")
    print(f"keys={len(data)}")
    print(f"injected={injected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
