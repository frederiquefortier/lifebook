"""Parse the French date headers that delimit journal passages.

Across eras the header format drifts: '1 janvier 2021' (bare) early, then
'Samedi, 1er janvier 2022' with a weekday prefix later. One anchored regex covers
both, so a date quoted mid-sentence is never mistaken for a passage boundary.
"""

from __future__ import annotations

import datetime as dt
import re

_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
_WEEKDAYS = "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"

# A paragraph that is *only* a date: an optional weekday prefix, a '1er'/'1e'
# ordinal, month, year. Anchored to the whole paragraph on purpose.
# The day may carry an inline correction the author wrote, e.g. '13(14) août 2021';
# we keep the primary number and ignore the parenthetical.
DATE_HEADER = re.compile(
    r"^\s*(?:(?:%s)\s*,?\s*)?(\d{1,2})\s*(?:\(\d{1,2}\))?\s*(?:er|e)?\s+(%s)\s+(\d{4})\s*\.?\s*$"
    % (_WEEKDAYS, "|".join(_MONTHS)),
    re.IGNORECASE,
)

# 'Entré #184' / 'Entrée #184' filing markers (the numbering scheme, not stored),
# with an optional '(suite)' / '- suite' when an entry continues across month files.
ENTRY_NUMBER = re.compile(
    r"^\s*entr[ée]e?\s*#?\s*\d+\s*(?:[-–(]\s*suite\s*\)?)?\s*\.?\s*$", re.IGNORECASE
)

# Year-6+ monthly recap headers embedded in the daily journal: a short '<noun> du
# mois :' label, or the year-end 'WRAP UPS' block. Kept deliberately narrow (a few
# words ending in 'du mois :', or the literal wrap-up header) so ordinary prose that
# merely mentions 'du mois' or 'de l'année' is never mistaken for a header and dropped.
# Content under a WRAP UPS header is skipped until the next date, which also covers its
# 'Livres de l'année' sub-lists.
# Known edge: a standalone daily line shaped like 'Plat du mois : pizza' would be read as
# a recap header and its following text skipped. Accepted: these headers are structural in
# the source, and a whole entry written that way has never occurred in the corpus.
SECTION_HEADER = re.compile(
    r"^\s*(?:\S+(?:\s+\S+){0,2}\s+du mois\s*:|wrap\s*ups?)\s*.*$",
    re.IGNORECASE,
)


def parse_header(text: str) -> str | None:
    """Return ISO 'YYYY-MM-DD' if the paragraph is a standalone date, else None."""
    match = DATE_HEADER.match(text)
    if not match:
        return None
    day, month, year = int(match.group(1)), _MONTHS[match.group(2).lower()], int(match.group(3))
    try:
        return dt.date(year, month, day).isoformat()
    except ValueError:
        return None


# One side of a range: 'day (month)? (year)?', month/year optional so the left side
# of '1 au 23 novembre 2022' can borrow them from the right side.
_PARTIAL = re.compile(
    r"^\s*(?:(?:%s)\s*,?\s*)?(\d{1,2})\s*(?:\(\d{1,2}\))?\s*(?:er|e)?\s*(%s)?\s*(\d{4})?\s*\.?\s*$"
    % (_WEEKDAYS, "|".join(_MONTHS)),
    re.IGNORECASE,
)


def _partial(text: str) -> tuple[int, int | None, int | None] | None:
    match = _PARTIAL.match(text)
    if not match:
        return None
    month = _MONTHS[match.group(2).lower()] if match.group(2) else None
    year = int(match.group(3)) if match.group(3) else None
    return int(match.group(1)), month, year


def parse_range(text: str) -> tuple[str, str] | None:
    """Return (start_iso, end_iso) for a '… au …' range, else None.

    The right side must be a full date; the left side inherits its month/year when
    omitted ('1e novembre au 23 novembre 2022', 'Samedi, 6 mai 2023 au lundi, 15 mai 2023').
    """
    parts = re.split(r"\bau\b", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None
    left, right = _partial(parts[0]), _partial(parts[1])
    if not left or not right or right[1] is None or right[2] is None:
        return None
    lday, lmonth, lyear = left
    end_day, end_month, end_year = right
    start_month = lmonth if lmonth is not None else end_month
    start_year = lyear if lyear is not None else end_year
    try:
        start = dt.date(start_year, start_month, lday)
        end = dt.date(end_year, end_month, end_day)
    except (ValueError, TypeError):
        return None
    if end < start:
        return None
    return start.isoformat(), end.isoformat()


def header_span(text: str) -> tuple[str, str | None] | None:
    """Boundary date for a passage: (date, end_date). end_date is None unless a range."""
    single = parse_header(text)
    if single:
        return single, None
    return parse_range(text)
