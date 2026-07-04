"""Unit tests for the prose ingestion parsing/splitting/load logic.

Runs on synthetic paragraphs, never the private data/local assets, so it is
reproducible in any checkout. The real life.db is never touched.
"""

from __future__ import annotations

import datetime as dt
import io
import sqlite3
import unicodedata
import zipfile
from collections import Counter

import pytest

from lifebook.db import SCHEMA_PATH, connect
from lifebook.ingest import notion, prose
from lifebook.ingest.dates import (
    ENTRY_NUMBER,
    SECTION_HEADER,
    header_span,
    parse_header,
    parse_range,
)
from lifebook.ingest.docx import read_paragraphs


def test_parse_header_accepts_every_era_format():
    assert parse_header("1 janvier 2021") == "2021-01-01"          # bare (year 3)
    assert parse_header("Samedi, 1er janvier 2022") == "2022-01-01"  # weekday + ordinal
    assert parse_header("Lundi, 1e janvier 2024") == "2024-01-01"
    assert parse_header("13(14) août 2021") == "2021-08-13"          # inline correction


def test_parse_header_rejects_non_dates_and_inline_mentions():
    assert parse_header("Antoine... c’est un autre sujet.") is None
    # A date quoted mid-sentence must not be read as a passage boundary.
    assert parse_header("On s’est vus le 2 janvier 2020 chez lui.") is None
    assert parse_header("32 janvier 2021") is None  # invalid day


def test_parse_range_borrows_month_and_year_from_the_right_side():
    # Left side omits the year; it inherits from the right.
    assert parse_range("1e novembre au 23 novembre 2022") == ("2022-11-01", "2022-11-23")
    # Both sides carry weekday + year.
    assert parse_range("Samedi, 6 mai 2023 au lundi, 15 mai 2023") == ("2023-05-06", "2023-05-15")
    # Not a range.
    assert parse_range("6 mai 2023") is None
    # Reversed / invalid ranges are refused.
    assert parse_range("15 mai 2023 au 6 mai 2023") is None


def test_header_span_reports_single_and_range():
    assert header_span("29 février 2020") == ("2020-02-29", None)
    assert header_span("1e novembre au 23 novembre 2022") == ("2022-11-01", "2022-11-23")


def test_range_passage_carries_end_date():
    paras = ["1e novembre au 23 novembre 2022", "Un mois résumé."]
    entries, holdout = prose._split_file(paras, "5.0.4 - novembre", "f.docx", Counter())
    assert holdout is None
    assert len(entries) == 1
    assert entries[0].date == "2022-11-01"
    assert entries[0].end_date == "2022-11-23"


def test_monthly_journal_splits_per_date_and_drops_noise():
    paras = [
        "Entré #132",
        "Samedi, 1er janvier 2022",
        "Premier jour.",
        "Dimanche, 2 janvier 2022",
        "Deuxième jour.",
        "Livre du mois :",         # recap block header -> deferred
        "Dune, de Frank Herbert.",  # value under the deferred header
        "Ma critique du livre.",   # still part of the deferred block
        "Lundi, 3 janvier 2022",
        "Troisième jour.",
    ]
    stats: Counter = Counter()
    entries, holdout = prose._split_file(paras, "3.0.6 - janvier", "f.docx", stats)

    assert holdout is None
    assert [(e.date, e.content) for e in entries] == [
        ("2022-01-01", "Premier jour."),
        ("2022-01-02", "Deuxième jour."),
        ("2022-01-03", "Troisième jour."),
    ]
    assert all(e.entry_type == "journal" and e.precision == "day" for e in entries)
    assert stats["section_blocks_deferred"] == 1


def test_prose_mentioning_recap_words_is_not_dropped():
    # A daily passage that merely mentions 'du mois' / 'de l'année' must survive:
    # only true standalone recap headers are deferred.
    paras = [
        "1 janvier 2021",
        "Le plus beau moment de l’année, sans doute le plat du mois au resto.",
        "2 janvier 2021",
        "Suite.",
    ]
    entries, _ = prose._split_file(paras, "3.0.6 - janvier", "f.docx", Counter())
    assert entries[0].content == "Le plus beau moment de l’année, sans doute le plat du mois au resto."
    assert len(entries) == 2


def test_label_strips_prefix_and_extension():
    assert prose._label("Lettre 1. .docx") == "1."     # year 1: dot + trailing space
    assert prose._label("Lettre 2..docx") == "2."      # double dot
    assert prose._label("Lettre 6_.docx") == "6_"      # year 6+: underscore variant
    assert prose._label("Lettre 3.0.6 - janvier.docx") == "3.0.6 - janvier"


def test_whole_number_letter_is_a_year_review():
    # Derive the label through _label() from the real filename, so the review regex and
    # _label are exercised together (a mismatch here is what hid a misclassification bug).
    for filename in ["Lettre 2..docx", "Lettre 6_.docx"]:
        paras = ["Bilan de l’année.", "1e septembre 2018"]
        entries, holdout = prose._split_file(paras, prose._label(filename), filename, Counter())
        assert holdout is None
        assert len(entries) == 1, filename
        assert entries[0].entry_type == "birthday", filename
        assert entries[0].precision == "year"
        assert entries[0].date == "2018-09-01"


def test_single_dated_letter_is_one_journal_entry():
    paras = ["29 février 2020", "Une lettre.", "Encore."]
    entries, holdout = prose._split_file(paras, "2.5", "Lettre 2.5.docx", Counter())
    assert holdout is None
    assert len(entries) == 1
    assert entries[0].entry_type == "journal"
    assert entries[0].content == "Une lettre.\n\nEncore."


def test_dateless_letter_is_held_out_not_dropped():
    paras = ["Cher E.N,", "Je pense à toi."]
    entries, holdout = prose._split_file(paras, "4.3", "Lettre 4.3.docx", Counter())
    assert entries == []
    assert holdout is not None
    assert holdout.source == "Lettre 4.3.docx"
    assert holdout.reason == "letter: no date"


def test_entry_number_matches_markers_including_suite():
    for marker in ["Entré #184", "Entrée #5", "Entré #92 (suite)", "Entré #50 - suite", "Entré #42 – suite"]:
        assert ENTRY_NUMBER.match(marker), marker
    assert not ENTRY_NUMBER.match("Entré dans la maison")


def test_prose_sentence_with_au_is_not_read_as_a_range():
    # parse_range runs on every non-date paragraph; the anchor must reject prose.
    assert parse_range("On est allés au chalet du 6 au 8.") is None
    assert header_span("On est allés au chalet du 6 au 8.") is None


def test_du_mois_line_is_a_recap_header_but_prose_is_not():
    # Documents the accepted edge: a standalone '<noun> du mois :' line is a recap header
    # (its block is deferred); a sentence that merely mentions it is left alone.
    assert SECTION_HEADER.match("Plat du mois : pizza")
    assert not SECTION_HEADER.match("On a mangé le plat du mois.")


def test_monthly_preamble_is_held_out_not_dropped():
    paras = [
        "Ceci est une intro sans date.",  # prose before any date header
        "Encore de l’intro.",
        "1 janvier 2021",
        "Jour un.",
        "2 janvier 2021",
        "Jour deux.",
    ]
    stats: Counter = Counter()
    entries, holdout = prose._split_file(paras, "3.0.6 - janvier", "f.docx", stats)
    assert [e.date for e in entries] == ["2021-01-01", "2021-01-02"]
    assert holdout is not None
    assert holdout.reason == "prose before first date header"
    assert holdout.paragraphs == 2
    assert stats["orphan_preamble"] == 2


def test_range_round_trips_through_db_and_check_rejects_reversed(tmp_path):
    con = connect(tmp_path / "t.db")
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    con.commit()
    entry = prose.Entry("2022-11-01", "day", "journal", None, "corps", "5.0.4.docx", end_date="2022-11-23")
    prose.load(con, [entry])
    con.commit()

    row = con.execute("SELECT date, end_date, source FROM entries").fetchone()
    assert (row["date"], row["end_date"], row["source"]) == ("2022-11-01", "2022-11-23", "5.0.4.docx")

    with pytest.raises(sqlite3.IntegrityError):  # end_date before date is refused
        con.execute(
            "INSERT INTO entries (date, end_date, date_precision, entry_type_id, content) "
            "VALUES ('2022-11-23', '2022-11-01', 'day', 1, 'x')"
        )
    con.close()


def test_load_is_idempotent_and_spares_app_rows(tmp_path):
    con = connect(tmp_path / "t.db")
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # An app-authored row has no source; the importer must never touch it.
    con.execute(
        "INSERT INTO entries (date, date_precision, entry_type_id, content, source) "
        "VALUES ('2023-01-01', 'day', 1, 'saisi dans l app', NULL)"
    )
    con.commit()

    imported = [prose.Entry("2022-11-01", "day", "journal", None, "corps", "5.0.4.docx")]
    prose.load(con, imported)
    con.commit()
    prose.load(con, imported)  # re-run: must replace, not duplicate
    con.commit()

    assert con.execute("SELECT count(*) FROM entries WHERE source IS NOT NULL").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM entries WHERE source IS NULL").fetchone()[0] == 1
    con.close()


def test_override_whole_collapses_internal_headers():
    # A letter with mid-text date lines becomes a single entry; the date lines are dropped.
    paras = ["Cher X,", "Corps un.", "17 mai 2020", "Corps deux.", "20 mai 2020."]
    override = {"mode": "whole", "date": "20-05-2020"}
    entries, holdout = prose._split_file(paras, "2.12", "Lettre 2.12.docx", Counter(), override)
    assert holdout is None
    assert len(entries) == 1
    entry = entries[0]
    assert (entry.date, entry.entry_type, entry.precision) == ("2020-05-20", "journal", "day")
    assert entry.content.startswith("Cher X,")
    assert "17 mai 2020" not in entry.content and "20 mai 2020" not in entry.content


def test_override_whole_review_stays_a_birthday():
    # A whole-number label keeps its year-in-review classification, just with a fixed date.
    paras = ["Bilan de mes 20 ans.", "12... nop 13 août 2020."]
    entries, holdout = prose._split_file(
        paras, "3.", "Lettre 3..docx", Counter(), {"mode": "whole", "date": "13-08-2020"}
    )
    assert holdout is None
    assert (entries[0].entry_type, entries[0].precision, entries[0].date) == ("birthday", "year", "2020-08-13")


def test_override_preamble_becomes_a_standalone_entry():
    paras = ["Intro sans date.", "13 août 2020", "Jour 13.", "14 août 2020", "Jour 14."]
    entries, holdout = prose._split_file(
        paras, "3.0.1", "f.docx", Counter(), {"mode": "preamble", "date": "22-08-2020"}
    )
    assert holdout is None
    assert [(e.date, e.content) for e in entries] == [
        ("2020-08-22", "Intro sans date."),
        ("2020-08-13", "Jour 13."),
        ("2020-08-14", "Jour 14."),
    ]


def test_override_defer_preamble_drops_it_but_keeps_dailies():
    paras = ["Mai Goals ---", "objectif un", "1e mai 2021", "Jour un."]
    stats: Counter = Counter()
    entries, holdout = prose._split_file(paras, "3.0.10", "f.docx", stats, {"mode": "defer_preamble"})
    assert holdout is None
    assert [(e.date, e.content) for e in entries] == [("2021-05-01", "Jour un.")]
    assert stats["deferred_preamble"] == 2


def test_override_end_dates_binds_content_to_the_date_below_it():
    # The parser's default would misdate these by one; end_dates fixes the association.
    paras = ["Réflexion du nouvel an.", "18 janvier 2025", "Après le 18.", "3 février 2025"]
    entries, holdout = prose._split_file(paras, "7.0.6-7", "f.docx", Counter(), {"mode": "end_dates"})
    assert holdout is None
    assert [(e.date, e.content) for e in entries] == [
        ("2025-01-18", "Réflexion du nouvel an."),
        ("2025-02-03", "Après le 18."),
    ]


def test_override_end_dates_holds_out_trailing_prose():
    paras = ["Corps.", "18 janvier 2025", "Sans date de fermeture."]
    entries, holdout = prose._split_file(paras, "x", "f.docx", Counter(), {"mode": "end_dates"})
    assert [e.date for e in entries] == ["2025-01-18"]
    assert holdout is not None and holdout.reason == "prose after last end-date header"


def test_override_sections_attaches_titles_and_strips_them():
    paras = ["Titre A", "3 février 2020", "Corps A.", "Titre B", "13 février 2020", "Corps B."]
    override = {
        "mode": "sections",
        "sections": [
            {"date": "03-02-2020", "title": "Titre A"},
            {"date": "13-02-2020", "title": "Titre B"},
        ],
    }
    entries, holdout = prose._split_file(paras, "2.2.2", "f.docx", Counter(), override)
    assert holdout is None
    assert [(e.date, e.title, e.content) for e in entries] == [
        ("2020-02-03", "Titre A", "Corps A."),
        ("2020-02-13", "Titre B", "Corps B."),
    ]


def test_override_skip_yields_no_entries_and_no_holdout():
    paras = ["18 juillet 2020.", "Un prompt.", "4 mars 2021.", "Suite."]
    stats: Counter = Counter()
    entries, holdout = prose._split_file(paras, "2.15", "f.docx", stats, {"mode": "skip"})
    assert entries == [] and holdout is None
    assert stats["deferred_files"] == 1


def test_override_whole_titles_the_entry_with_its_label():
    # Overriding only the date must not blank the title; it defaults to the label.
    paras = ["Une lettre sans date."]
    entries, _ = prose._split_file(paras, "4.3", "f.docx", Counter(), {"mode": "whole", "date": "08-09-2022"})
    assert entries[0].title == "4.3"
    # An explicit title still wins.
    entries, _ = prose._split_file(
        paras, "4.3", "f.docx", Counter(), {"mode": "whole", "date": "08-09-2022", "title": "Cher E.N"}
    )
    assert entries[0].title == "Cher E.N"


def test_override_whole_without_prose_is_held_out_not_dropped():
    paras = ["17 mai 2020"]  # a lone date header, no prose to keep
    entries, holdout = prose._split_file(paras, "x", "f.docx", Counter(), {"mode": "whole", "date": "20-05-2020"})
    assert entries == []
    assert holdout is not None and holdout.reason == "whole override but file has no prose"


def test_override_unknown_mode_raises_with_source():
    with pytest.raises(ValueError, match=r"f\.docx: unknown override mode"):
        prose._split_file(["x"], "l", "f.docx", Counter(), {"mode": "bogus"})


def test_override_bad_date_raises_with_source():
    with pytest.raises(ValueError, match=r"f\.docx: date is not a valid DD-MM-YYYY date"):
        prose._split_file(["x"], "l", "f.docx", Counter(), {"mode": "whole", "date": "2020-05-20"})


def test_override_sections_length_mismatch_raises_with_source():
    paras = ["Titre A", "3 février 2020", "Corps A."]  # only one dated section
    override = {
        "mode": "sections",
        "sections": [
            {"date": "03-02-2020", "title": "Titre A"},
            {"date": "13-02-2020", "title": "Titre B"},
        ],
    }
    with pytest.raises(ValueError, match=r"f\.docx: sections override expected 2 entries, got 1"):
        prose._split_file(paras, "l", "f.docx", Counter(), override)


def test_override_sections_date_mismatch_raises_with_source():
    paras = ["Titre A", "9 février 2020", "Corps A."]  # header date != override date
    override = {"mode": "sections", "sections": [{"date": "03-02-2020", "title": "Titre A"}]}
    with pytest.raises(ValueError, match=r"f\.docx: section date 2020-02-09 does not match override 2020-02-03"):
        prose._split_file(paras, "l", "f.docx", Counter(), override)


def test_override_sections_holds_out_stray_prose_before_the_first_title():
    # An intro line before the first title/date has no section; it must be held out, not dropped.
    paras = ["Intro sans titre.", "Titre A", "3 février 2020", "Corps A."]
    override = {"mode": "sections", "sections": [{"date": "03-02-2020", "title": "Titre A"}]}
    entries, holdout = prose._split_file(paras, "l", "f.docx", Counter(), override)
    assert [(e.date, e.title, e.content) for e in entries] == [("2020-02-03", "Titre A", "Corps A.")]
    assert holdout is not None and holdout.reason == "prose before first titled section"
    assert holdout.paragraphs == 1


def test_override_sections_strips_a_title_only_once():
    # A body line that repeats the title string after the heading survives.
    paras = ["Titre A", "3 février 2020", "Corps A.", "Titre A"]
    override = {"mode": "sections", "sections": [{"date": "03-02-2020", "title": "Titre A"}]}
    entries, _ = prose._split_file(paras, "l", "f.docx", Counter(), override)
    assert entries[0].content == "Corps A.\n\nTitre A"


def test_override_preamble_without_a_preamble_is_signaled():
    # Specifying a preamble date for a file that has none is a no-op that contradicts intent.
    paras = ["13 août 2020", "Jour 13."]
    entries, holdout = prose._split_file(
        paras, "3.0.1", "f.docx", Counter(), {"mode": "preamble", "date": "22-08-2020"}
    )
    assert [e.date for e in entries] == ["2020-08-13"]
    assert holdout is not None and holdout.reason == "preamble override but file has no preamble"


def test_load_overrides_parses_ddmmyyyy_table(tmp_path):
    path = tmp_path / "date_overrides.toml"
    path.write_text('["Lettre 2.13.docx"]\nmode = "whole"\ndate = "11-06-2020"\n', encoding="utf-8")
    assert prose.load_overrides(path) == {"Lettre 2.13.docx": {"mode": "whole", "date": "11-06-2020"}}
    assert prose.load_overrides(tmp_path / "absent.toml") == {}


def test_recap_block_in_single_letter_is_dropped():
    # The recap-skip rule must apply to flat letters too, not only monthly journals.
    paras = ["3 mai 2022", "Vraie prose.", "Livre du mois :", "Un roman.", "Ma note."]
    entries, _ = prose._split_file(paras, "2.9", "Lettre 2.9.docx", Counter())
    assert len(entries) == 1
    assert entries[0].content == "Vraie prose."


# ── docx.py ──────────────────────────────────────────────────────────────────

def _docx(paragraphs_xml: str) -> io.BytesIO:
    doc = (
        '<?xml version="1.0"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + paragraphs_xml + "</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("word/document.xml", doc)
    buf.seek(0)
    return buf


def test_read_paragraphs_separates_breaks_and_tabs_and_normalizes_nbsp():
    xml = (
        "<w:p><w:r><w:t>Bonjour</w:t></w:r><w:r><w:br/></w:r><w:r><w:t>monde</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>a</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>b</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Livre du mois :</w:t></w:r></w:p>"
    )
    assert read_paragraphs(_docx(xml)) == ["Bonjour\nmonde", "a\tb", "Livre du mois :"]


def test_read_paragraphs_does_not_double_text_box_paragraphs():
    # A text box nests <w:p> inside a run of an outer paragraph; the nested text must be
    # emitted once (folded into its container), never twice.
    xml = (
        "<w:p><w:r><w:t>Avant.</w:t></w:r>"
        "<w:r><w:txbxContent><w:p><w:r><w:t>Encadré.</w:t></w:r></w:p></w:txbxContent></w:r>"
        "<w:r><w:t>Après.</w:t></w:r></w:p>"
    )
    paras = read_paragraphs(_docx(xml))
    assert "\n".join(paras).count("Encadré.") == 1
    assert len(paras) == 1  # the nested paragraph is not emitted separately


# ── notion.py ────────────────────────────────────────────────────────────────

def _notion_page(directory, filename, title, date, journal, body):
    # Notion export: H1, a BLANK line, then the property block, a blank line, the body.
    text = f"# {title}\n\nOn this day?: No\nJournal: {journal} (x.md)\nDate: {date}\n\n{body}\n"
    (directory / filename).write_text(text, encoding="utf-8")


def test_parse_en_date():
    assert notion._parse_en_date("November 14, 2025") == dt.date(2025, 11, 14)
    assert notion._parse_en_date("14 novembre 2025") is None  # not the English form
    assert notion._parse_en_date("garbage") is None


def test_parse_page_reads_properties_after_the_blank_line(tmp_path):
    _notion_page(tmp_path, "x.md", "Lettre 8.2", "November 14, 2025", "Lettres", "Fenêtre close.\nBanc chauffant.")
    entry = notion._parse_page(tmp_path / "x.md")
    assert entry is not None
    assert (entry.date, entry.journal) == ("2025-11-14", "Lettres")
    assert entry.content == "Fenêtre close.\nBanc chauffant."


def test_collect_keeps_only_recent_lettres_with_content(tmp_path):
    _notion_page(tmp_path, "a.md", "Lettre 8.2", "November 14, 2025", "Lettres", "Récent.")
    _notion_page(tmp_path, "b.md", "Lettre 7.9", "August 1, 2025", "Lettres", "Duplique Drive.")
    _notion_page(tmp_path, "c.md", "Bingo", "December 1, 2025", "Bingo", "Un special.")
    _notion_page(tmp_path, "d.md", "Vide", "December 2, 2025", "Lettres", "")
    kept = notion.collect(tmp_path)
    assert [e.title for e in kept] == ["Lettre 8.2"]
    assert (kept[0].date, kept[0].content) == ("2025-11-14", "Récent.")


def test_collect_cutover_is_inclusive_and_gap_free(tmp_path):
    # Spec for the seam: Nov 1 2025 is kept (>=), Oct 31 is dropped as a Drive duplicate.
    assert notion.CUTOVER == dt.date(2025, 11, 1)
    _notion_page(tmp_path, "on.md", "Lettre 8.1", "November 1, 2025", "Lettres", "Le seuil.")
    _notion_page(tmp_path, "before.md", "Lettre 7.99", "October 31, 2025", "Lettres", "La veille.")
    assert {e.title for e in notion.collect(tmp_path)} == {"Lettre 8.1"}


# ── build_entries (Drive + Notion seam) ──────────────────────────────────────

def _write_docx(directory, filename, *texts):
    body = "".join(f"<w:p><w:r><w:t>{t}</w:t></w:r></w:p>" for t in texts)
    doc = (
        '<?xml version="1.0"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + body + "</w:body></w:document>"
    )
    with zipfile.ZipFile(directory / filename, "w") as archive:
        archive.writestr("word/document.xml", doc)


def test_build_entries_merges_sources_and_dedups(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    notion_dir = tmp_path / "notion"
    notion_dir.mkdir()
    _write_docx(drive, "Lettre 9.0.1 - août.docx", "1 août 2025", "Jour un.", "2 août 2025", "Jour deux.")
    # exact byte-duplicate download: must be deduped, not imported twice
    _write_docx(drive, "Lettre 9.0.1 - août (1).docx", "1 août 2025", "Jour un.", "2 août 2025", "Jour deux.")
    # a recent Notion-only entry on the far side of the seam
    _notion_page(notion_dir, "n.md", "Lettre 9.1", "December 1, 2025", "Lettres", "Écrit dans Notion.")

    entries, holdouts, stats = prose.build_entries(drive, notion_dir)

    assert sorted(e.date for e in entries) == ["2025-08-01", "2025-08-02", "2025-12-01"]
    assert stats["dupes_removed"] == 1
    assert stats["notion_kept"] == 1
    # Dedup keeps the canonical name, not the '(1)' copy, even though '(1)' sorts first.
    sources = {e.source for e in entries}
    assert sources == {"Lettre 9.0.1 - août.docx", "n.md"}


def test_build_entries_flags_an_override_key_that_matched_no_file(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    notion_dir = tmp_path / "notion"
    notion_dir.mkdir()
    _write_docx(drive, "Lettre 9.2.docx", "1 août 2025", "Jour un.")
    overrides = {"Lettre 9.2.docx": {"mode": "whole", "date": "01-08-2025"},
                 "Lettre 9.9.docx": {"mode": "whole", "date": "01-08-2025"}}  # names no real file

    entries, holdouts, stats = prose.build_entries(drive, notion_dir, overrides)

    assert stats["overrides_unmatched"] == 1
    leftovers = [h for h in holdouts if h.reason.startswith("override key matched no ingested file")]
    assert [h.source for h in leftovers] == ["Lettre 9.9.docx"]


def test_build_entries_matches_override_across_nfc_nfd_filenames(tmp_path):
    # Drive stores 'août' decomposed (NFD); the override key is composed (NFC). They must match.
    drive = tmp_path / "drive"
    drive.mkdir()
    notion_dir = tmp_path / "notion"
    notion_dir.mkdir()
    nfd_name = unicodedata.normalize("NFD", "Lettre 9.3 - août.docx")
    nfc_key = unicodedata.normalize("NFC", "Lettre 9.3 - août.docx")
    assert nfd_name != nfc_key  # guard: the two forms really differ
    _write_docx(drive, nfd_name, "Une lettre sans date.")
    overrides = {nfc_key: {"mode": "whole", "date": "31-07-2022"}}

    entries, holdouts, stats = prose.build_entries(drive, notion_dir, overrides)

    assert stats["overrides_unmatched"] == 0
    assert [(e.date, e.content) for e in entries] == [("2022-07-31", "Une lettre sans date.")]


def test_load_writes_rows_that_satisfy_the_schema(tmp_path):
    con = connect(tmp_path / "t.db")
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    con.commit()
    entries = [
        prose.Entry("2022-01-01", "day", "journal", None, "corps", "f.docx"),
        prose.Entry("2018-09-01", "year", "birthday", "1.", "bilan", "Lettre 1.docx"),
    ]
    written = prose.load(con, entries)
    con.commit()

    assert written == 2
    rows = con.execute(
        "SELECT et.name, e.date, e.date_precision FROM entries e "
        "JOIN entry_types et ON et.id = e.entry_type_id ORDER BY e.date"
    ).fetchall()
    assert [tuple(r) for r in rows] == [
        ("birthday", "2018-09-01", "year"),
        ("journal", "2022-01-01", "day"),
    ]
    con.close()
