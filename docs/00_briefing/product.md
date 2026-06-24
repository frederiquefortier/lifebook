# Product

The specification for the printed book — its structure, content layers, and
reader experience. The system (data + tooling) is described in
[architecture.md](../01_building/architecture.md); this document describes what the
book *is*.

**Working title:** TBD (*Décade* was a candidate when a volume was assumed to be ten
years).

Each **volume** covers a chosen **date range** — a decade, five years, or a single
year, depending on size and printing (undecided). It is primarily **chronological**,
but carries several layers of content on top of that spine.

---

## Double temporality

The project rests on two time systems, deliberately set in parallel:

| Calendar time | Personal time |
|---|---|
| Years | Birthday to birthday |
| Months | Words of the year |
| Named events / trips | Fête (year-in-review by age) |
| The journal | Life reviews / personal evolution |

The book places **civil time** and **lived time** side by side. This duality is the
conceptual heart of the work (see [vision.md](inspirations/vision.md)).

---

## General structure

### Yearly separators
Each year opens with a distinctive page or double-page spread. It may contain:
- the **word of the year**;
- a **retrospective**;
- **notable events** — the named events/trips tagged in that year (see [Events](#named-events--trips));
- **annual statistics**.

Years are visually differentiated with color pages or a distinct graphic treatment.

### Monthly separators
Each month begins with a minimalist page, inspired by the style used in *Twilight*:

```
JANVIER

...
```

These pages act as **visual breathing room**.

### Main entries (the *Lettres*)
The journal entries are the core of the book. Characteristics:
- **one entry = one date** — a passage with several dates under it is split into one
  entry per date; grouping (e.g. a personal-time "month letter") is done by filtering,
  not by storing them together;
- **unique numbering** — a clean 1..N chronological sequence assigned at render time
  (not the database `id`; see [database.md](../01_building/database.md));
- an optional **title** for the longer subject letters;
- a **date** (precise to the day, or only to a week / month / year);
- **variable length** — some entries are very short, others span several pages.

---

## Complementary content layers

### Books & citations (*Livres*)
A book read, kept with: **title**, **author**, **one or more citations**, an optional
**short commentary**, and a **date** (often only a month).

### Prompts
A **question and its answer**, with a date.

### Weekly fun facts
Interesting facts collected over the years — usually dated to a **week**, not a specific
day. Keep each at its real date *and* produce an annual compilation.

### Abécédaires
Some years include an alphabet, treated as a special interlude — 26 letters, each with a
word (first letter bold) and a short text:

```
P — Planchette : Expression artistique à la suisse. Fromage, charcuterie,
    cornichons. Ma passion du moment.
```

### Bingo
A **5×5 grid per calendar year**; each cell has a label and maybe an icon, checked off
over the year (a satisfying check animation in the app).

### Named events / trips
A **named happening that groups entries** — a trip or place like *Suisse 2024* or
*Espagne 2016*, or a milestone. It's a **tag**: many ordinary entries share the same
event (distinct from a theme — a theme is an abstract recurring subject, an event is one
specific named happening). Lets the book (and app) gather "everything from Espagne 2016"
and surface a year's notable events. Stored as the `events` tag dimension (see
[database.md](../01_building/database.md#events)).

### Bucketlist
A single **running list** of goals — added, checked off, or removed over time, with the
add-history preserved (e.g. "28 / 97 done, 4 removed"). Not tied to one year.

### Yearly tops
Each year carries one or more ranked "top" lists — and **the topics and lengths vary
year to year**:
- top 10 **songs** (the *soundtrack of the year*) — optionally artists/genres;
- top 5 **games** by hours played;
- top 3 **books**;
- **reddit**, films, podcasts, … whatever was tracked that year.

Some years have many lists, some few; some are top 10, others top 3. Modeled flexibly
(see [database.md — Yearly tops](../01_building/database.md#yearly-tops)). Source: these
are mostly already written in the Word docs, so they arrive via normal ingestion.

### Monthly artwork
An artwork associated with each month — an image, a reproduction, and/or a personal
commentary. *(Depends on media, which is out of scope for now.)*

### Fête — year-in-review by age
Each personal year (birthday to birthday) produces a special *Fête*: a year-in-review
**by age**, with a **unique visual treatment**.
Approach retained:
- **no** real physical envelope;
- design that **evokes a sealed letter**;
- a distinct typeface or style;
- must remain **print-compatible**.

---

## Final cartography (analytical section)

At the end of the book sits an analytical section. It is **not part of the main
narrative** — it exists to observe the volume's whole span at once.

### Presences in my life
Analysis of the people appearing in the writings. Possible visualizations:
frequency, duration, narrative importance, relational network.
Examples: people present across the whole span; brief but defining relationships;
recurring figures.

### Themes
Automatic theme analysis (love, identity, work, ambition, solitude, travel,
creation…). Visualizations: evolution over time, thematic clustering, relative
importance.

### Emotions
Global emotional analysis. Visualizations: heatmap, time curves, periods of
stability, periods of intensity. Goal: observe the **emotional climate** of the
whole span.

### Tops over time
Visualization of the yearly tops across the span — musical evolution (songs, artists,
genres), but also games, books, and any other recurring category. Each category that
appears in enough years can trace its own arc.

### Places / map
A map of **where you were** over the span, from each entry's location. Filterable —
a single trip ("Espagne 2016"), a year, or everywhere at once — and showable as pins, a
heat-map of time spent, or routes. In the app this is an interactive **map module** for
*tagging* location; in the book it becomes a printed map spread.

### Synthesis of life years
Compilation of words of the year, *fêtes* (the by-age year-in-reviews), and major transitions.

---

## NSFW handling

Some entries contain very personal content. Goals: **respect intimacy** and **warn a
potential reader clearly**.

**At the data level** — each entry carries a graded sensitivity **level** (0–3, *how*
sensitive) plus **categories** (*what* the content is):

```json
{ "nsfw_level": 3, "nsfw_tags": ["sexual"] }
```
while most entries are simply:
```json
{ "nsfw_level": 0 }
```

**At the book level** — the level drives the treatment:

| Level | Treatment |
|---|---|
| 0 — None | No warning. |
| 1 — Mild | Subtle marker, no warning page. |
| 2 — Mature | Content warning + visual separation. |
| 3 — Explicit | Full warning page; clearly skippable section. |

The reader is explicitly invited to skip a flagged section if they prefer not to read
it. Categories let the reader know *what kind* of content they'd be skipping.
See the [Privacy principle](inspirations/vision.md#principles) and the
[data model](../01_building/database.md) for the underlying schema.
