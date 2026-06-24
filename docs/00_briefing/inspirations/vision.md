# Vision

## The project is not a book — it is a system

The goal is not simply to produce a printed book from years of personal writing.
It is to build a **durable autobiographical system** capable of evolving across an
entire lifetime.

The printed book is only a **snapshot** of that system at a point in time. The data,
the analyses, and the tools remain alive and reusable for the decades to come.

## What the system must enable

Centralize, preserve, analyze, publish, reproduce, and own — see the full goal list in
the [project brief](../brief.md#goals).

## Long-term horizon

Publication happens in **volumes** — each a chosen **date range** rendered from the one
continuous archive:

```
volume 1  →  volume 2  →  volume 3  →  …
```

A volume's span is undecided and flexible — a decade, five years, or a single year,
depending on size and printing. The cadence is a render-time choice, not a property of
the data: any date range can be reconstructed from the underlying archive. The book
becomes a **periodic publication of a personal memory** — versioned, analyzed, typeset.

The priority is not only to tell a life, but to build an archive that is:

- **durable** — readable in decades, independent of any single vendor;
- **maintainable** — clean data, scripted processing, reproducible output;
- **reusable** — capable of accompanying its author's evolution over many decades.

## Guiding tension: two times

The system runs on two parallel clocks that the book deliberately places side by side:

- **Calendar time** — years, months, events, the journal.
- **Personal time** — birthday to birthday: words of the year, letters, life reviews.

This dual temporality is the conceptual heart of the work. See
[product.md](../product.md) for how it shapes the book.

## Principles

The enduring principles that fall out of this vision and guide product and engineering
decisions. **North star:** the book is a snapshot; the data lives for decades.

- **Data is the single source of truth.** The canonical memory lives in `life.db`
  (SQLite), never in the layout tool. Every output (print, web, export) is regenerable
  from it; the workflow flows one way (`SQLite → Python → Export → InDesign → PDF`) and
  is never re-imported from a typeset file.
- **Durability over convenience.** Prefer formats and tools still readable in decades:
  a single-file database, open formats, and 3-2-1 backups (local + cloud + cold). No
  lock-in to anything that needs a live service to read.
- **Full ownership.** The author owns 100% of the data and the pipeline. Self-hosted,
  local-first, no mandatory cloud dependency — never hostage to a third party.
- **Reproducible for any date range.** Any volume is reconstructable from the data with
  the same scripted (not manual) process. All volumes share one system, not bespoke
  per-volume workflows; the span (decade / 5-year / yearly) is just a render-time filter.
- **Privacy is a first-class feature.** Sensitive content is modeled in the data
  (a graded `nsfw_level` + tags) and signposted clearly in the book — the
  goal is informed reader consent, not censorship.
- **Two clocks, side by side.** Honor both calendar time and personal
  (birthday-to-birthday) time; never flatten them into a single chronological stream.
  Mirrored in the schema by `yearly_reviews` (calendar) and the `birthday`
  entries placed by age via `config.author_birthdate` (personal).
