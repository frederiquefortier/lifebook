# Database

The complete schema for `life.db` (SQLite), the single source of truth. See
[architecture.md](architecture.md) for how this layer fits the system and
[ADR-001](decisions.md) for why SQLite.

Design notes:
- **The atomic unit is one entry = one date.** Anything multi-dated is split into one
  entry per date; *grouping* (by calendar year, personal/birthday year, month, type, a
  shared title…) is done by filtering, never by storing things pre-grouped. This is
  the single most important modeling rule.
- People, themes, emotions, relationships, and NSFW tags are normalized into their
  own tables and linked via many-to-many join tables.
- Each person exists only once; alternate names are handled by `person_aliases`,
  enabling automatic consolidation during import.
- **Double temporality:** calendar time = an entry's `date` (+ `yearly_reviews`);
  personal time = age, derived from `date − config.author_birthdate` (e.g. the
  `birthday` entries). Both are just views over the same atomic entries.
- A single-row `config` table holds the one project constant that can't be derived:
  the author's birthdate.

---

## Schema conventions (how the DDL realizes this in SQLite)

The tables below are described conceptually; the authoritative DDL is
[`src/lifebook/db/schema.sql`](../../src/lifebook/db/schema.sql), built by
`lifebook.db.build_db`. Conventions applied across the whole schema (ADR-008/009/010):

- **Stamped `PRAGMA user_version = 1`**: the migration baseline (ADR-010).
- **All `id` columns are `INTEGER PRIMARY KEY AUTOINCREMENT`**: ids are never reused,
  honoring the "stable internal key, may have gaps" rule.
- **Every table carries `created_at` and `updated_at`** (TEXT, ISO-8601 via
  `CURRENT_TIMESTAMP`), even where not listed in the per-table columns below. An
  `AFTER UPDATE` trigger per table keeps `updated_at` current (a `WHEN` guard prevents
  trigger recursion).
- **Dates are stored as `TEXT` in ISO-8601 `YYYY-MM-DD`** (SQLite has no native date
  type). `date_precision` controls rendering. `entries.date` and `config.author_birthdate`
  carry a `CHECK (… GLOB '????-??-??')` shape guard; `created_at`/`updated_at` are
  datetime text.
- **Foreign keys:** enforcement is per-connection, enabled by `lifebook.db.connect()`.
  Join rows `ON DELETE CASCADE` with their `entries` row; references to dimension rows
  (people / themes / emotions / places / events / nsfw_tags / categories / types) use
  `ON DELETE RESTRICT` so a still-referenced dimension can't be deleted. Owned children
  (`person_aliases`, `person_relationships`, `top_list_items`, `book_citations`,
  `alphabet_items`, `bingo_cells`) cascade from their parent.
- **Indexes** on `entries.date` and every FK column used for joins/lookups.

---

## Project config

### `config`
A single-row table. Just the author's birthdate, which is what makes personal
time (age, birthday-to-birthday) computable at all.

| Field | Type |
|---|---|
| author_birthdate | DATE |

> **No "decade" here.** A volume (decade / 5-year / 1-year; undecided, depends on
> print size) is just a `date_range_start … date_range_end` filter applied at
> app/export time rather than stored state. The app always shows the whole archive and
> navigates by year; the book is whatever date range is chosen at publication.

---

## Core content

### `entries`
The atomic unit: one dated, taggable, analyzable piece of content. Covers the
prose-shaped types (see `entry_types`). Structured artifacts (`books`, `alphabets`,
`bingos`, `bucketlist_items`) live in their own tables further down.

| Field | Type |
|---|---|
| id | INTEGER |
| date | DATE |
| end_date | DATE |
| date_precision | TEXT |
| entry_type_id | INTEGER |
| place_id | INTEGER |
| title | TEXT |
| content | TEXT |
| source | TEXT |
| nsfw_level | INTEGER |
| created_at | DATETIME |
| updated_at | DATETIME |

`date_precision` is `day` \| `week` \| `month` \| `year`. Many entries are only known to
a week (fun facts), a month, or a year (the `birthday`). `date` stores the
best/anchor date; precision tells rendering whether to show "jeudi 1 décembre 2022" vs
"décembre 2022".

`end_date` is normally null. A few passages cover a span of days ("1 au 23 novembre
2022"); those store the range's start in `date` and its end in `end_date` (with a
`CHECK` that it is a valid date not before `date`), so the span is never lost.

`source` records where a bulk-imported entry came from (its `.docx` or Notion page), so
the one-way import stays traceable to verify against the originals. Entries later created
in the app leave it null.

`place_id` → `places` = where you were for this entry (nullable; most entries are
home or unknown). One place per entry; the geography of a trip is derived by filtering
on the `events` tag. See [Places](#places).

`title` is optional: used by the longer subject letters (and as a display label where a
type wants one); most journal entries have none.

`id` is the **stable internal key**: never reused, may have gaps. The book's *visible*
entry number is not `id`; it's a clean 1..N chronological sequence computed at render
time. A backdated insert simply shifts the numbering in the next edition (fine, since
each book is a snapshot).

`nsfw_level` is a graded sensitivity score from 0 to 3. It drives *how* the book
treats a section. The categories (*what* the content is) live in `entry_nsfw_tags`. See
the [NSFW section](#nsfw) below.

### `entry_types`
Normalized list of entry types. These are the prose-shaped types stored in
`entries`:

| Field | Type |
|---|---|
| id | INTEGER |
| name | TEXT |

`name` is an English slug (display labels like *Lettre* / *Fête* are an app/UI
concern). The types:

| Slug | What it is | Notes |
|---|---|---|
| `journal` | Generic dated entry (the *Lettres*): date, text, tags, people, emotions | The core of the book. Long subject letters use `title`. |
| `birthday` | Personal year-in-review *by age* (the *Fêtes*) | Personal-time anchor; usually `year` precision. Replaces the old `birthday_reviews` table. |
| `fun_fact` | A single fact | Often `week` precision; no specific day. |
| `prompt` | A question + its answer | `title` = question, `content` = answer. |

Named happenings (trips, places, milestones like *Suisse 2024*) are a tag that
groups entries. See [Events](#events).

Books, alphabets, bingo, and the bucketlist are not entries; they have their own
structured tables (see [Structured content](#structured-content)).

---

## People & relationships

### `people`
Canonical list of individuals. A person exists only once in the database.

| Field | Type |
|---|---|
| id | INTEGER |
| display_name | TEXT |

### `person_aliases`
Alternative names used throughout the years. Allows automatic consolidation during
import.

| Field | Type |
|---|---|
| id | INTEGER |
| person_id | INTEGER |
| alias | TEXT |

Example: all aliases below resolve to one person (`person_id = 1`):
`Mom`, `Maman`, `Mother`, `Louise`.

### `relationship_types`
Normalized relationship taxonomy. New categories can be added later without schema
changes.

| Field | Type |
|---|---|
| id | INTEGER |
| name | TEXT |

Examples: `family`, `romantic`, `friendship`, `work`, `school`.

### `person_relationships`
Tracks how relationships evolve over time. A single person may hold multiple
relationships simultaneously (e.g. `friendship` and `work` can coexist).

| Field | Type |
|---|---|
| id | INTEGER |
| person_id | INTEGER |
| relationship_type_id | INTEGER |
| start_date | DATE |
| end_date | DATE |

Example (one person, evolving over time):

| person | relationship | start |
|---|---|---|
| Julie | school | 2015 |
| Julie | friendship | 2017 |
| Julie | work | 2023 |

---

## Analysis dimensions

Themes and emotions are closed, versioned label lists ([ADR-005](decisions.md)).
Their source of truth is flat CSV files in Git (`data/seed/themes.csv`,
`data/seed/emotions.csv`); the tables below are the runtime copy, seeded from those
CSVs by `seed_labels.py` and never hand-edited. The tables exist so the join tables can
reference stable `id`s and so labels can be aggregated in SQL.

### `themes`
Runtime copy of the theme list (seeded from `data/seed/themes.csv`).

| Field | Type |
|---|---|
| id | INTEGER |
| slug | TEXT |
| name | TEXT |
| definition | TEXT |
| status | TEXT |

`slug` is the stable key matched against the CSV; `definition` is the gloss used by the
embeddings / LLM prompt; `status` is `active` or `deprecated` (deprecated rows are kept,
never deleted, so historical tags stay valid).
Examples: `identity`, `travel`, `ambition`, `family`, `creativity`, `grief`, `love`.

### `emotions`
Runtime copy of the emotion list (seeded from `data/seed/emotions.csv`). 35 felt states
([ADR-011](decisions.md)).

| Field | Type |
|---|---|
| id | INTEGER |
| slug | TEXT |
| name | TEXT |
| definition | TEXT |
| status | TEXT |
| valence | REAL |
| arousal | REAL |
| family | TEXT |

`valence` (unpleasant ↔ pleasant, −1…+1) and `arousal` (calm ↔ activated, 0…1) place each
emotion on the 2-D **mood meter**: `valence` × each entry's `intensity` gives the smooth
"emotional climate" curve, while `arousal` separates calm from energetic states at the same
valence (e.g. `serenity` vs `excitement`). `family` is the emotion's slug in the **9-family
wheel** (named after each prototype emotion), used to roll the 35 discrete labels up into
readable grouped charts without losing capture detail:

| Family | French | Tone |
|---|---|---|
| `joy` | Joie | active pleasant |
| `tenderness` | Tendresse | felt warmth / connection |
| `serenity` | Sérénité | calm pleasant |
| `sadness` | Tristesse | low-energy unpleasant |
| `anger` | Colère | activated unpleasant |
| `fear` | Peur | threat |
| `disgust` | Dégoût | aversion |
| `shame` | Honte | self-conscious |
| `surprise` | Surprise | neutral |

The families split the *pleasant* side as finely as the *unpleasant* side (3 vs 5), avoiding
the negativity bias of a raw Ekman-6 grouping. Slugs are English nouns; `name`/`definition`
are French ([ADR-007](decisions.md)). **`love` is not here**: the felt warmth is `affection`
(family `tenderness`); the *bond* is `people` + relationship_type; love *as a subject* is the
`love` theme.
Examples: `joy`, `sadness`, `anxiety`, `anger`, `gratitude`, `nostalgia`.

---

## Events

A named happening that groups entries: a trip, a place, a milestone (e.g. *Suisse
2024*, *Espagne 2016*). Several entries can share one event. It's distinct from a
theme: a theme is an abstract recurring subject, an event is one specific named
happening.

Like `people` and `top_categories`, events are author-managed in the app
(select-or-add), not seeded from Git and not classifier-driven. Values are real
labels (often French), so there's no English slug: just an `id` and `name`, like
`people`.

### `events`
| Field | Type |
|---|---|
| id | INTEGER |
| name | TEXT |
| start_date | DATE |
| end_date | DATE |

`start_date` / `end_date` are optional: a bounded trip has them (and they let the app
*suggest* the tag for entries in that range); an open-ended one leaves them null.

### `entry_events`
| Field | Type |
|---|---|
| entry_id | INTEGER |
| event_id | INTEGER |

---

## Places

Geographic locations with coordinates, the backbone of the map module. A canonical
list (like `people`): a place is stored once and reused. Distinct from an `event`: an
event is a named happening ("Espagne 2016"); a place is a point on the map ("Barcelona")
that can recur across many events and years.

Author-managed in the app (pick a point / search, or confirm an NLP-suggested place);
not seeded from Git. Real names, so no English slug: `id` + `name`.

### `places`
| Field | Type |
|---|---|
| id | INTEGER |
| name | TEXT |
| lat | REAL |
| lng | REAL |
| kind | TEXT |

`kind` is optional (`home`, `city`, `country`, `venue`…), handy for map zoom/clustering.
Entries link via `entries.place_id`. The map for any slice (an entry, a year, an
`events` trip, or the whole span) is just those entries' places, derived by filtering,
no extra link tables.

---

## Join tables (many-to-many)

### `entry_people`
| Field | Type |
|---|---|
| entry_id | INTEGER |
| person_id | INTEGER |

### `entry_themes`
| Field | Type |
|---|---|
| entry_id | INTEGER |
| theme_id | INTEGER |
| confidence | REAL |
| list_version | INTEGER |

### `entry_emotions`
| Field | Type |
|---|---|
| entry_id | INTEGER |
| emotion_id | INTEGER |
| intensity | REAL |
| confidence | REAL |
| list_version | INTEGER |

`list_version` records which version of the label list produced each tag, so a list
change in a later decade can be re-tagged honestly ([ADR-005](decisions.md)).

---

## NSFW

Two separate things: a **level** (intensity → how the book warns) on the entry, and
**tags** (topic → what the content is) via the join table.

### Sensitivity levels (`entries.nsfw_level`)
A fixed 0–3 scale, each tied to a concrete book treatment:

| Level | Meaning | Book treatment |
|---|---|---|
| 0 | None / safe | No warning. The vast majority of entries. |
| 1 | Mild / personal | Sensitive but not graphic. Subtle marker, no warning page. |
| 2 | Mature | Content warning + visual separation before the section. |
| 3 | Explicit / heavy | Full warning page; clearly skippable; most protected. |

### `nsfw_tags`
Closed list of sensitivity categories (the *topic* of sensitive content), seeded
from `data/seed/nsfw_tags.csv`, same source-vs-runtime-copy pattern as themes /
emotions ([ADR-005](decisions.md)).

| Field | Type |
|---|---|
| id | INTEGER |
| slug | TEXT |
| name | TEXT |
| definition | TEXT |
| status | TEXT |

Starting set (topic-based, multi-label, edit once ingestion shows what's really there):
`sexual`, `substance_use`, `violence`, `self_harm`, `abuse`, `trauma`,
`mental_health`, `grief`.

> Note: `explicit` was dropped (that's intensity → the *level*), and `nudity` folded
> into `sexual`.

### `entry_nsfw_tags`
Many-to-many relationship.

| Field | Type |
|---|---|
| entry_id | INTEGER |
| nsfw_tag_id | INTEGER |

A sensitive entry combines its level with its categories:
```json
{ "nsfw_level": 3, "nsfw_tags": ["sexual", "trauma"] }
```
while most entries are simply:
```json
{ "nsfw_level": 0 }
```

See the [NSFW handling section](../00_briefing/product.md) for how this is
surfaced in the book.

---

## Yearly summary (calendar time)

### `yearly_reviews`
Calendar-year scalars that don't belong to any single entry.

| Field | Type |
|---|---|
| year | INTEGER |
| word_of_year | TEXT |
| retrospective | TEXT |
| annual_stats_json | TEXT |

The year's *événements marquants* for the separator page are the `events` tagged in
that year (optionally a curated subset). No separate column needed. The yearly
"top N" lists (songs, games, books, …) live in `top_lists` / `top_list_items` below.

> The personal-time counterpart (the year-in-review *by age*) is a `birthday` entry
> rather than a table, on the personal-time axis via `date − config.author_birthdate`.

---

## Yearly tops

Per-year ranked lists whose topic and length vary year to year: top 10 songs one
year; top 5 games by hours played and top 3 books another. Modeled as typed lists with
ranked items so the final cartography can trace any one category (music, games, …)
across the whole span, while still allowing each year to have whatever lists it had.

### `top_categories`
The kinds of top list (`songs`, `games`, `books`, `reddit`, `films`, …). Managed in
the app rather than seeded from Git: the editor shows a select of existing categories and
lets you add a new one on the fly.

| Field | Type |
|---|---|
| id | INTEGER |
| slug | TEXT |
| name | TEXT |

> **Two kinds of controlled list.** Themes, emotions, and `nsfw_tags` are *seeded from
> Git CSVs* because the pipeline/classifier reads them and they need definitions +
> versioning ([ADR-005](decisions.md)). `top_categories` is the other kind: pure
> author-entered editorial data with no classifier behind it, so it lives only in the
> DB and is managed in the app (select + add-new), like `people` / `person_aliases`.

### `top_lists`
One ranked list for one year (e.g. "Top 10 chansons 2018").

| Field | Type |
|---|---|
| id | INTEGER |
| year | INTEGER |
| category_id | INTEGER |
| title | TEXT |

`category_id` → `top_categories`. Referencing a stable id (not free text) is what lets
a category be aggregated across years even if its display `name` is later edited.
`title` is an optional per-list display label.

### `top_list_items`
The ranked rows of a list. There is no fixed N: top 3 or top 10 is just how many
rows exist.

| Field | Type |
|---|---|
| id | INTEGER |
| list_id | INTEGER |
| rank | INTEGER |
| label | TEXT |
| detail | TEXT |

`label` is the item (song / game / book name); `detail` is optional extra (artist,
author, "1 200 h played", …).

> **Source:** the tops are mostly already written in the Word docs, so they arrive via
> normal [ingestion](ingestion.md); exact parsing is figured out when we see them.

---

## Structured content

Content with internal structure that doesn't fit the prose `entries` shape. These are
editorial artifacts: they are not run through the people/themes/emotions analysis
(that's for the prose entries).

### Books (`livres`)
A book read, with one or more citations.

**`books`**: `id`, `title`, `author`, `commentary`, `date`, `date_precision`
(often `month`).
**`book_citations`**: `id`, `book_id`, `rank`, `text`, `reflection` (a book can have
several citations; `reflection` optional).

### Alphabets (*abécédaires*)
26 letters, each with a word and a short text (some years have one).

**`alphabets`**: `id`, `year`, `title`.
**`alphabet_items`**: `id`, `alphabet_id`, `position` (A–Z), `letter`, `word`,
`text`. Example: `P` · *Planchette* · "Expression artistique à la suisse…".

### Bingo
A 5×5 grid per calendar year; cells get checked off (nice check animation in the app).

**`bingos`**: `id`, `year`.
**`bingo_cells`**: `id`, `bingo_id`, `row`, `col`, `label`, `icon`, `checked_at`
(null = unchecked).

### Bucketlist
A single **running list** (not per year): goals added, checked, or removed over time.

**`bucketlist_items`**: `id`, `number`, `text`, `status` (`active` \| `done` \|
`removed`), `added_date`, `done_date`.

Counts like "28 / 97 done (4 removed, excluded from total)" and the add-history are
derived from these rows (`added_date`, `status`, `done_date`) rather than stored as a
separate ledger.

---

> **Media is out of scope for now**: no `media` table yet. Artwork, images, and other
> files will be added later when the book actually needs them; at that point the schema
> gains a `media` table and the files live outside the DB (only references stored).
