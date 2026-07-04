"""Read the recent, Notion-only entries we keep.

Drive covers the backlog through mid-August 2025 (the year-8 'août' journal, last
dated 2025-08-16). The author then resumed writing directly in Notion in November
2025; the September-October window is empty in both sources. Earlier Notion entries
duplicate the Drive letters (the hand-transfer), so the cutover is a deliberate dedup
boundary: keep only Notion Lettres dated on/after 2025-11-01, which exist nowhere in
Drive. The gap-free seam is pinned by a test (test_ingest). Each Notion page is a
markdown file: an H1 title, a block of 'Key: value' properties, a blank line, then
the prose body.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

CUTOVER = dt.date(2025, 11, 1)  # dedup boundary: Notion-only entries start here

# Notion exports dates in English ('November 14, 2025'). Parse explicitly rather
# than via strptime('%B'), which is locale-dependent and would fail off en_US.
_EN_MONTHS = {
    m: i
    for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"],
        start=1,
    )
}


@dataclass(frozen=True)
class NotionEntry:
    title: str
    date: str  # ISO 'YYYY-MM-DD'
    journal: str
    content: str
    source: str  # filename


def _parse_en_date(raw: str) -> dt.date | None:
    try:
        month_word, rest = raw.strip().split(" ", 1)
        day, year = rest.replace(",", "").split()
        return dt.date(int(year), _EN_MONTHS[month_word], int(day))
    except (ValueError, KeyError):
        return None


def _parse_page(path: Path) -> NotionEntry | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        return None
    title = lines[0][2:].strip()

    props: dict[str, str] = {}
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1  # skip blank lines between the title and the property block
    while i < len(lines) and lines[i].strip():
        key, sep, value = lines[i].partition(":")
        if sep:
            props[key.strip()] = value.strip()
        i += 1
    body = "\n".join(lines[i + 1 :]).strip()  # everything after the blank line

    date = _parse_en_date(props.get("Date", ""))
    if date is None:
        return None
    journal = props.get("Journal", "").split(" (")[0]
    return NotionEntry(title, date.isoformat(), journal, body, path.name)


def collect(notion_dir: Path) -> list[NotionEntry]:
    """Recent Notion-only prose entries: dated >= CUTOVER and in the Lettres journal.

    The Lettres filter drops the recent Bingo / Abécédaire pages, which are
    structured specials handled in a later pass, not prose.
    """
    kept: list[NotionEntry] = []
    for md in sorted(notion_dir.glob("*.md")):
        entry = _parse_page(md)
        if entry and entry.journal.startswith("Lettres") and entry.content:
            if dt.date.fromisoformat(entry.date) >= CUTOVER:
                kept.append(entry)
    return kept
