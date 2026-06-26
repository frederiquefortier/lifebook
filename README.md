# Lifebook

**Lifebook turns years of French journals and notes into one queryable SQLite archive, enriches it with NLP, and renders any date range into a print-ready book.**

The book is just a snapshot; the real product is the archive beneath it, built so the data outlives every tool that touches it.

<!-- Hero media: add as the assets exist. A sample spread or a short capture-to-print clip belongs here. -->
<!-- ![A sample typeset book spread](docs/assets/hero.png) -->
<!-- ![Curation app: entry editor and NLP review panel](docs/assets/app.png) -->

## Highlights

- 🗄️ **One SQLite file holds the entire life archive.** Print, web, and exports all regenerate from it, so no rendered output is ever the original.
- ➡️ **Entries flow one way and are never edited in place.** `SQLite → Python → Export → InDesign → PDF`. The layout tool renders the book and never writes back.
- 📊 **A `health` tag means the same thing in 2044 as in 2024.** Themes and emotions come from fixed, versioned vocabularies, so a decade of entries actually adds up.
- 🇫🇷 **Every entry is read in French, not translated.** People, themes, and emotions are extracted with French models and prompts, so nothing is approximated through English.
- 🔒 **Sensitive text is processed on the author's own machine.** Cloud models help build the pipeline but never see a journal entry.

## Overview

Lifebook runs as a one-way pipeline around a single database.

1. Entries are captured in the curation app or imported from the Word and Notion backlog.
2. Python enriches each entry with people, themes, emotions, and statistics. The NLP output is a set of suggestions the author confirms in the app.
3. A chosen date range is exported, typeset in InDesign or Affinity, and printed.

The data only moves forward. A typeset file is never read back into the database, so any volume can be rebuilt years later by re-running the pipeline against the same data.

## Problem

Years of personal writing pile up in scattered Word documents and Notion. Turning them into a keepsake book is usually a one-off job that dies with the layout tool it was made in. The tool owns the content, nothing is queryable or analyzable, and the next book starts over.

What's missing is the system underneath the book: something that preserves the writing, analyzes it, and can reproduce a volume for any span. It also has to respect two things most tools ignore. The content is intimate and in French, and it has to stay owned and private rather than sitting in a vendor's cloud.

## Goals

- Centralize all personal writing in one place.
- Preserve it in durable, open formats that stay readable for decades.
- Analyze it automatically: people, themes, emotions, statistics.
- Publish any volume (a chosen date range) and reproduce it later from the same data.
- Keep full ownership, local-first, with no mandatory cloud.

## Architecture

`life.db` (SQLite) is the single source of truth, and Python is the only language allowed to write it. The curation app and the publication step are both clients of that file. Two constraints sit underneath the design: the content is private and French, and the schema has to keep working for a lifetime.

```
                 Curation app (React/TipTap + local FastAPI)
                              │ read/write
                              ▼
   Python (import, NLP, stats) ──►  life.db  ──► InDesign / Affinity ──► PDF
                                source of truth         render engine
```

Two writers touch the database, and neither is authoritative. The app writes human-authored data (entries, metadata, people decisions, accept/reject verdicts). Python writes machine-generated data (imported entries and confidence-gated theme/emotion suggestions). `life.db` is the truth; both are clients.

```
repo/
  pyproject.toml  README.md  .gitignore
  src/lifebook/{db,ingest,nlp,stats,export,api}/   # the only DB-writing package
  frontend/                                        # React/TipTap curation app
  data/{seed,local}/                               # seed CSVs (Git) + life.db (gitignored)
  docs/                                            # brief, vision, architecture, ADRs, journal
  tests/
```

### Stack

| Layer | Role | Tech |
|---|---|---|
| Data | Authoritative single-file archive | SQLite (`life.db`) |
| Processing | Import, clean, extract, analyze, export | Python 3.12, spaCy, Transformers, local LLM, uv |
| Curation app | Write entries, review NLP suggestions | React + TipTap, local FastAPI |
| Publication | Typographic polish for print | InDesign / Affinity Publisher to PDF |

As a result, regenerating a past volume just re-runs the pipeline against the same database, and the layout tool never holds anything that can't be reproduced. Full schema in [database.md](docs/01_building/database.md), rationale in the [ADRs](docs/01_building/decisions.md).

## Challenges

- **Aggregating a decade of fuzzy, first-person text.** Free-form extraction gives labels that can't be compared across years (`career anxiety` one year, `professional stress` the next). Entries are classified against closed, versioned lists instead, which keeps the analysis aggregatable and measurable.
- **French-first NLP.** Most tooling defaults to English and degrades on French. Date parsing, NER, classifier prompts, and label glosses are all tuned for French.
- **Privacy under analysis.** The content is intimate, so the classifier that reads entries has to run locally. Cloud models help build the pipeline but never see the text.
- **A schema that has to last a lifetime.** It stays easy to edit now and switches to additive, numbered migrations the moment it holds irreplaceable data.
- **Durability across decades.** No tool or format outlives a life reliably, so the archive is one open file, the pipeline is scripted, and backups follow an encrypted 3-2-1 rule.

These constraints shaped nearly every decision below.

## Key Decisions

Full context, alternatives, and trade-offs live in the [architectural decision records](docs/01_building/decisions.md).

- **SQLite as the single source of truth** ([ADR-001](docs/01_building/decisions.md)). One portable file holds the whole archive. A client/server database would need a server and back up worse for a personal project; flat files give no relational integrity.
- **InDesign / Affinity as a render engine only** ([ADR-003](docs/01_building/decisions.md)). The pipeline runs one way. Authoring directly in the layout tool would couple the archive to proprietary software and make it impossible to reproduce.
- **Closed, versioned label lists** ([ADR-005](docs/01_building/decisions.md), [ADR-011](docs/01_building/decisions.md), [ADR-012](docs/01_building/decisions.md)). Themes and emotions are fixed vocabularies (CSV in Git, runtime copy in the DB). Free-form extraction was rejected because its labels can't be aggregated or measured.
- **Local-first app and a local classifier** ([ADR-006](docs/01_building/decisions.md)). Capture and review happen offline, and private text never reaches a cloud API. A hosted app would send intimate content off the machine.
- **French-first tooling** ([ADR-007](docs/01_building/decisions.md)). Content is stored verbatim in French and processed with French models. English-first models and translation passes both lose meaning on the real text.

## Future Work

Tracked in [improvements.md](docs/03_planning/improvements.md).

- **Ingestion.** Import the Word and Notion backlog, parsing French dates and text.
- **Closed-set classifier.** A local LLM assigns themes and emotions with confidence and a supporting quote, measured against a small hand-labeled gold set.
- **Curation app.** The React/TipTap and FastAPI capture-and-review tool.
- **Automated layout and a web renderer.** Generate InDesign-ready exports from Python, and maybe a web edition from the same database, so regenerating a volume stops being manual.
- **Reproducibility pass.** Parameterize the pipeline by date range and snapshot the environment so any later volume is one scripted run.

## Lessons Learned

- A label system lives or dies on where you draw the boundaries, not on the code. Most of the design work went into deciding what a theme actually is (a subject, not a mood or a feeling) so each fact has exactly one home.
- SQLite hides sharp edges that only bite at scale: foreign keys are off per connection until you enable them, there is no native date type, and `updated_at` needs a trigger. A single shared connection helper is the cleanest place to absorb that.
- Deferring schema migrations until real data exists kept early iteration fast, as long as the rule "never rebuild once data exists" is enforced in code rather than remembered.
- Choosing durable formats up front (one open file, CSV seed lists, ISO-8601 dates) is a cheap decision now that pays off only decades later, which is exactly when it can't be retrofitted.
- A src-layout that keeps the package importable only when installed means the tests exercise the real packaging, so build mistakes surface early.
