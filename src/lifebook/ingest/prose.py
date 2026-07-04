"""Import the prose backlog (Drive letters + recent Notion-only entries) into life.db.

Pass 1 is prose only: no people, emotions, tags, or structured specials (bingo,
abécédaire, music tops, bucketlist). Drive is the spine; the two sources meet at a
clean date seam (see notion.py). The pipeline per Drive file:

    dedup by body hash -> classify -> split on date headers -> load

A whole-number label ('Lettre N.') is the yearly 'birthday' review. Every other letter
is classified by how many standalone date headers it holds, not by its filename number
(the numbering drifts and is unreliable):
  * 0 headers  -> held out (no date to store; entries.date is NOT NULL)
  * 1 header   -> one 'journal' entry at that date (day precision)
  * 2+ headers -> a monthly journal, split into one 'journal' entry per dated passage

Nothing is dropped silently: letters with no date, and prose that appears before the
first date header of a monthly file, are held out into a report for manual handling.

    uv run python -m lifebook.ingest.prose                 # dry run, writes report
    uv run python -m lifebook.ingest.prose --commit --db <path>
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import sqlite3
import sys
import tomllib
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from ..db import LOCAL_DIR, connect
from . import notion
from .dates import ENTRY_NUMBER, SECTION_HEADER, header_span
from .docx import read_paragraphs

ASSETS = LOCAL_DIR / "assets"
DRIVE_DIR = ASSETS / "drive"
NOTION_DIR = ASSETS / "notion"
REPORT_PATH = LOCAL_DIR / "ingest_unresolved_dates.csv"  # gitignored (private filenames)
# Manual date resolutions for letters the parser can't place on its own (date at the end,
# répertoire, goals block, titled sections). Keyed by source filename, dates DD-MM-YYYY.
OVERRIDES_PATH = LOCAL_DIR / "date_overrides.toml"  # gitignored (private dates)

# Titled letters that are structured content, not prose. Deferred to a later pass.
_SPECIAL = re.compile(
    r"bingo|ab[ée]c[ée]daire|throwback|bucketlist|po[ée]sie|birthday list", re.IGNORECASE
)
# Whole-number label = the yearly fête / year-in-review. The trailing separator drifts
# across years ('Lettre 2..docx' -> '2.', 'Lettre 6_.docx' -> '6_'), so allow a dot,
# an underscore, or nothing after the number.
_REVIEW_LABEL = re.compile(r"^\d+[._]?$")

# Re-downloaded copies are suffixed '(1)', '(2)', ... ('décembre (1).docx'). When two
# files share a body hash the canonical name (no suffix) should win, so it must be
# visited first during dedup.
_DUP_SUFFIX = re.compile(r"\s*\(\d+\)\.docx$", re.IGNORECASE)


@dataclass(frozen=True)
class Entry:
    date: str
    precision: str
    entry_type: str
    title: str | None
    content: str
    source: str
    end_date: str | None = None


@dataclass(frozen=True)
class Holdout:
    source: str
    paragraphs: int
    first_line: str
    reason: str


def _label(filename: str) -> str:
    """'Lettre 3.0.6 - janvier.docx' -> '3.0.6 - janvier'."""
    stem = filename[:-5] if filename.endswith(".docx") else filename
    return stem[7:].strip() if stem.startswith("Lettre ") else stem.strip()


def _scan(paras: list[str]):
    """Walk paragraphs once, yielding classified events, so the skip rule lives here.

    Yields ``('date', span)`` at each date/range header, ``('recap', None)`` when a recap
    header ('Livre du mois :', 'WRAP UPS') is seen (its text is only counted, not used),
    and ``('text', paragraph)`` for kept prose. Blank lines, filing markers ('Entré #184',
    'Entré #92 (suite)'), and the body of a recap block (everything after a recap header
    until the next date) are swallowed. Both the flat-letter and monthly paths consume
    this, so the state machine is defined in one place instead of duplicated by hand.
    """
    skipping = False
    for text in paras:
        if not text:
            continue
        span = header_span(text)
        if span:
            skipping = False
            yield "date", span
        elif ENTRY_NUMBER.match(text):
            continue
        elif SECTION_HEADER.match(text):
            skipping = True
            yield "recap", None
        elif not skipping:
            yield "text", text


def _holdout(source: str, prose: list[str], reason: str) -> Holdout:
    return Holdout(source, len(prose), prose[0][:80] if prose else "", reason)


def _iso(ddmmyyyy: str) -> str:
    """'20-05-2020' -> '2020-05-20'. Raises on a malformed override date."""
    day, month, year = (int(part) for part in ddmmyyyy.split("-"))
    return dt.date(year, month, day).isoformat()


def load_overrides(path: Path = OVERRIDES_PATH) -> dict[str, dict]:
    """Read the manual date-resolution table, keyed by source filename (empty if absent)."""
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _split_by_leading_dates(
    events: list[tuple[str, object]], source: str
) -> tuple[list[Entry], list[str]]:
    """Split events where each date header opens the passage that follows it.

    Returns ``(entries, preamble)``; ``preamble`` is the prose before the first date
    header, which has no day to attach to. This is the plain monthly-journal shape,
    shared by the default path and the preamble/section overrides.
    """
    result: list[Entry] = []
    preamble: list[str] = []
    current: tuple[str, str | None] | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current and buffer:
            content = "\n\n".join(buffer).strip()
            if content:
                date, end = current
                result.append(Entry(date, "day", "journal", None, content, source, end))

    for kind, val in events:
        if kind == "date":
            flush()
            current, buffer = val, []
        elif kind == "text":
            (buffer if current is not None else preamble).append(val)
    flush()
    return result, preamble


_OVERRIDE_MODES = frozenset({"whole", "preamble", "defer_preamble", "end_dates", "sections", "skip"})


def _validate_override(source: str, override: dict) -> None:
    """Fail fast on a malformed hand-authored override, naming the offending file.

    The overrides file is edited by hand, so the one thing a crash must report is *which*
    entry is wrong. Checks the mode is known and the keys each mode needs are present and
    parseable, up front, so every mode reports errors the same helpful way.
    """
    def check_date(value: object, where: str) -> None:
        try:
            _iso(value)  # type: ignore[arg-type]
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"{source}: {where} is not a valid DD-MM-YYYY date: {value!r}") from exc

    mode = override.get("mode")
    if mode not in _OVERRIDE_MODES:
        raise ValueError(
            f"{source}: unknown override mode {mode!r} (expected one of {sorted(_OVERRIDE_MODES)})"
        )
    if mode in ("whole", "preamble"):
        if "date" not in override:
            raise ValueError(f"{source}: {mode} override requires a 'date'")
        check_date(override["date"], "date")
    if mode == "sections":
        secs = override.get("sections")
        if not isinstance(secs, list) or not secs:
            raise ValueError(f"{source}: sections override requires a non-empty 'sections' list")
        for i, sec in enumerate(secs):
            if not isinstance(sec, dict) or "date" not in sec or "title" not in sec:
                raise ValueError(f"{source}: sections[{i}] needs both 'date' and 'title'")
            check_date(sec["date"], f"sections[{i}].date")


def _apply_override(
    events: list[tuple[str, object]], label: str, source: str, stats: Counter, override: dict
) -> tuple[list[Entry], Holdout | None]:
    """Resolve a file the automatic classifier can't place, per its override entry.

    Modes: ``whole`` (one entry at a fixed date, ignoring any internal headers),
    ``preamble`` (the orphan preamble becomes its own entry, the rest splits normally),
    ``defer_preamble`` (drop the preamble, keep the daily entries), ``end_dates`` (a date
    header closes the passage above it, not the one below), ``sections`` (split on the
    detected headers and attach the given titles), and ``skip`` (defer the whole file).
    """
    _validate_override(source, override)
    mode = override["mode"]

    if mode == "skip":
        stats["deferred_files"] += 1
        return [], None

    if mode == "whole":
        prose = [val for kind, val in events if kind == "text"]
        if not prose:
            # A whole override that yields nothing is almost certainly a mistake (wrong file,
            # or the prose lives behind a recap block); surface it, don't silently drop it.
            return [], _holdout(source, [], "whole override but file has no prose")
        date = _iso(override["date"])
        content = "\n\n".join(prose).strip()
        if _REVIEW_LABEL.match(label):
            stats["reviews"] += 1
            return [Entry(date, "year", "birthday", label, content, source)], None
        stats["single_letters"] += 1
        # Match the automatic single-letter path, which titles the entry with its label.
        return [Entry(date, "day", "journal", override.get("title", label), content, source)], None

    if mode in ("preamble", "defer_preamble"):
        result, preamble = _split_by_leading_dates(events, source)
        holdout = None
        if mode == "preamble":
            if preamble:
                date = _iso(override["date"])
                result.insert(0, Entry(date, "day", "journal", None, "\n\n".join(preamble).strip(), source))
            else:
                # The override promised a dated preamble entry but the file has none; the
                # date you set placed nothing. Surface it rather than pass quietly.
                holdout = _holdout(source, [], "preamble override but file has no preamble")
        elif preamble:  # defer_preamble: drop the leading block (e.g. a goals list)
            stats["deferred_preamble"] += len(preamble)
        stats["journal_files"] += 1
        stats["journal_entries"] += len(result)
        stats["ranges"] += sum(1 for entry in result if entry.end_date)
        return result, holdout

    if mode == "end_dates":
        # Same shape as _split_by_leading_dates, but inverted: a date header closes the
        # passage above it instead of opening the one below. Closing headers are assumed to
        # be single dates; a range header would bind its end_date to the passage above.
        result = []
        buffer = []
        for kind, val in events:
            if kind == "date":
                if buffer:
                    date, end = val
                    result.append(Entry(date, "day", "journal", None, "\n\n".join(buffer).strip(), source, end))
                    buffer = []
            elif kind == "text":
                buffer.append(val)
        stats["journal_files"] += 1
        stats["journal_entries"] += len(result)
        stats["ranges"] += sum(1 for entry in result if entry.end_date)
        # Trailing prose with no closing date can't be placed; hold it out, never drop it.
        holdout = _holdout(source, buffer, "prose after last end-date header") if buffer else None
        return result, holdout

    # mode == "sections"
    secs = override["sections"]
    # Strip each section's title line out of the prose stream (it becomes the entry title,
    # not body text). Remove each title only once, at its first occurrence, so a body line
    # that legitimately repeats the short title string later is not also deleted.
    remaining = {sec["title"].strip() for sec in secs}
    kept: list[tuple[str, object]] = []
    for kind, val in events:
        if kind == "text" and val.strip() in remaining:
            remaining.discard(val.strip())
            continue
        kept.append((kind, val))
    result, preamble = _split_by_leading_dates(kept, source)
    if len(result) != len(secs):
        raise ValueError(f"{source}: sections override expected {len(secs)} entries, got {len(result)}")
    titled: list[Entry] = []
    for entry, sec in zip(result, secs):
        want = _iso(sec["date"])
        if entry.date != want:
            raise ValueError(f"{source}: section date {entry.date} does not match override {want}")
        titled.append(replace(entry, title=sec["title"]))
    stats["journal_files"] += 1
    stats["journal_entries"] += len(titled)
    # Prose before the first titled section has no section to attach to; hold it out so this
    # mode keeps the module's "never silently dropped" invariant too.
    holdout = _holdout(source, preamble, "prose before first titled section") if preamble else None
    return titled, holdout


def _split_file(
    paras: list[str], label: str, source: str, stats: Counter, override: dict | None = None
) -> tuple[list[Entry], Holdout | None]:
    events = list(_scan(paras))
    # Count recap blocks that were deferred while processing. A wholesale `skip` never
    # processes the file, so its internal recap headers must not inflate the tally.
    if not (override and override.get("mode") == "skip"):
        stats["section_blocks_deferred"] += sum(1 for kind, _ in events if kind == "recap")
    if override:
        return _apply_override(events, label, source, stats, override)
    spans = [val for kind, val in events if kind == "date"]
    prose = [val for kind, val in events if kind == "text"]

    # Whole-number letter: the year-in-review, one entry at year precision.
    if _REVIEW_LABEL.match(label):
        if not spans:
            return [], _holdout(source, prose, "review: no date")
        if not prose:
            stats["empty_skipped"] += 1
            return [], None
        stats["reviews"] += 1
        date, end = spans[0]
        return [Entry(date, "year", "birthday", label, "\n\n".join(prose), source, end)], None

    # Single reflective letter: one entry at its writing date (or span). All prose is
    # kept, wherever it sits relative to the lone date header.
    if len(spans) <= 1:
        if not spans:
            return [], _holdout(source, prose, "letter: no date")
        if not prose:
            stats["empty_skipped"] += 1
            return [], None
        stats["single_letters"] += 1
        date, end = spans[0]
        if end:
            stats["ranges"] += 1
        return [Entry(date, "day", "journal", label, "\n\n".join(prose), source, end)], None

    # Monthly journal: one entry per dated passage. Prose before the first date header has
    # no day to attach to (often a continuation of the previous month's last entry); it is
    # held out for manual placement, never silently dropped.
    stats["journal_files"] += 1
    result, preamble = _split_by_leading_dates(events, source)
    stats["journal_entries"] += len(result)
    stats["ranges"] += sum(1 for entry in result if entry.end_date)
    if preamble:
        stats["orphan_preamble"] += len(preamble)
        return result, _holdout(source, preamble, "prose before first date header")
    return result, None


def build_entries(
    drive_dir: Path = DRIVE_DIR,
    notion_dir: Path = NOTION_DIR,
    overrides: dict[str, dict] | None = None,
) -> tuple[list[Entry], list[Holdout], Counter]:
    """Parse both sources into entries + a hold-out list, without touching a DB.

    The two source dirs are arguments (defaulting to the real asset paths) so the
    dedup + Drive/Notion merge can be exercised against fixtures. ``overrides`` defaults
    to the on-disk table; pass a dict to exercise the resolutions against fixtures.
    """
    if overrides is None:
        overrides = load_overrides()
    # Drive filenames come off the filesystem in NFD for some accents ('août') and
    # NFC for others, inconsistently; normalize both sides so an override key always matches.
    overrides = {unicodedata.normalize("NFC", key): val for key, val in overrides.items()}
    entries: list[Entry] = []
    holdouts: list[Holdout] = []
    stats: Counter = Counter()
    seen: dict[str, str] = {}
    consumed: set[str] = set()  # override keys that actually matched a processed file

    # Visit canonical names before their '(1)' copies so dedup keeps the canonical source.
    ordered = sorted(drive_dir.glob("Lettre*.docx"), key=lambda p: (bool(_DUP_SUFFIX.search(p.name)), p.name))
    for path in ordered:
        stats["files_total"] += 1
        if _SPECIAL.search(path.name):
            stats["specials_skipped"] += 1
            continue
        paras = read_paragraphs(path)
        body = "\n".join(t for t in paras if t)
        # md5 is a content fingerprint for exact-duplicate detection, not security.
        digest = hashlib.md5(body.encode("utf-8"), usedforsecurity=False).hexdigest()
        if digest in seen:
            stats["dupes_removed"] += 1
            continue
        seen[digest] = path.name

        key = unicodedata.normalize("NFC", path.name)
        override = overrides.get(key)
        if override is not None:
            consumed.add(key)
        file_entries, holdout = _split_file(paras, _label(path.name), path.name, stats, override)
        entries.extend(file_entries)
        if holdout:
            holdouts.append(holdout)

    # An override that matched no file (a typo, or a name that lost the dedup race / is a
    # special) would silently leave that letter to the automatic classifier: you'd believe a
    # date is pinned when it isn't. Surface every leftover key instead of dropping it silently.
    for key in sorted(set(overrides) - consumed):
        stats["overrides_unmatched"] += 1
        holdouts.append(Holdout(key, 0, "", "override key matched no ingested file (typo, lost dedup, or a special)"))

    for recent in notion.collect(notion_dir):
        entries.append(Entry(recent.date, "day", "journal", recent.title, recent.content, recent.source))
        stats["notion_kept"] += 1

    stats["total_entries"] = len(entries)
    return entries, holdouts, stats


def load(con: sqlite3.Connection, entries: list[Entry]) -> int:
    """Insert entries; returns the number of rows written."""
    types = {r["name"]: r["id"] for r in con.execute("SELECT id, name FROM entry_types")}
    con.executemany(
        "INSERT INTO entries "
        "(date, end_date, date_precision, entry_type_id, title, content, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (e.date, e.end_date, e.precision, types[e.entry_type], e.title, e.content, e.source)
            for e in entries
        ],
    )
    return len(entries)


def _write_report(holdouts: list[Holdout], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source", "paragraphs", "first_line", "reason"])
        for h in sorted(holdouts, key=lambda x: x.source):
            writer.writerow([h.source, h.paragraphs, h.first_line, h.reason])


def _print_summary(entries: list[Entry], holdouts: list[Holdout], stats: Counter) -> None:
    print("Drive files:            %3d" % stats["files_total"])
    print("  specials skipped:     %3d" % stats["specials_skipped"])
    print("  exact dupes removed:  %3d" % stats["dupes_removed"])
    print("  reviews (birthday):   %3d" % stats["reviews"])
    print("  single letters:       %3d" % stats["single_letters"])
    print("  monthly journals:     %3d  -> %d dated entries" % (stats["journal_files"], stats["journal_entries"]))
    print("  date-range entries:   %3d" % stats["ranges"])
    print("  recap blocks deferred:%3d" % stats["section_blocks_deferred"])
    print("  empty (skipped):      %3d" % stats["empty_skipped"])
    print("  orphan preamble paras:%3d  (held out, not dropped)" % stats["orphan_preamble"])
    print("  overridden: skip files:%3d  preamble dropped:%3d" % (stats["deferred_files"], stats["deferred_preamble"]))
    print("  overrides unmatched:  %3d  (keys that matched no file)" % stats["overrides_unmatched"])
    print("Notion-only kept:       %3d" % stats["notion_kept"])
    print("Held out (files):       %3d  -> %s" % (len(holdouts), REPORT_PATH))
    print("-" * 40)
    print("TOTAL entries:          %3d" % len(entries))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import the prose backlog into life.db.")
    parser.add_argument("--commit", action="store_true", help="insert into --db (default: dry run)")
    parser.add_argument("--db", type=Path, help="target life.db (required with --commit)")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="hold-out report path")
    args = parser.parse_args(argv)
    if args.commit and not args.db:
        parser.error("--commit requires --db")

    entries, holdouts, stats = build_entries()
    _print_summary(entries, holdouts, stats)
    _write_report(holdouts, args.report)

    if args.commit:
        con = connect(args.db)
        try:
            written = load(con, entries)
            con.commit()
        finally:
            con.close()
        print("committed %d entries to %s" % (written, args.db))
    else:
        print("(dry run; pass --commit --db <path> to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
