# Ingestion

How existing writings get into `life.db`. This is the unglamorous majority of the work
— getting messy, multi-source history cleanly into the schema. See
[architecture.md](architecture.md) for where this sits and [database.md](database.md)
for the target tables.

## Sources

The writings currently live in two places, in **two different shapes**:

- **Notion** — already split roughly the way we want (one item per piece), but most
  items lack tags / people / emotions.
- **Word documents in Google Drive** — the bulk, in a denser shape: a numbered entry
  header followed by **several dated passages**, e.g.

  ```
  Entré #184
  Jeudi, 1 décembre 2022
  Lorem ipsum…

  Vendredi, 2 décembre 2022
  Lorem ipsum…
  ```

Both are imported by Python scripts in the processing layer. After import **and
verification**, the originals are retired (archived, then removed) — `life.db` becomes
the source of truth, and keeping the cloud originals is redundant exposure
([ADR-004](decisions.md)).

### The numbering scheme is filing, not storage
The originals are filed with a manual numbering system (`Lettre 2.0.5`, where `2` = year
2 / 2018, `0` = the monthly birth-calendar grouping, etc.). That scheme is **how the
author organized files** — it is *not* stored. The DB stores atomic dated entries; the
"month letter by personal year" grouping is reproduced later by **filtering** on date +
personal time. Don't try to preserve the numbers.

## Two regimes

1. **Backlog (one-time):** the years of existing Word + Notion content. Messy, varied
   formatting, inconsistent date conventions. This is where the hard parsing work is.
2. **Steady-state (ongoing):** new entries created going forward — these come in
   through the [curation app](architecture.md#curation-app--capture--review), not this
   importer. Ingestion is mostly about the backlog.

## Pipeline (backlog)

1. **Extract** raw text per source:
   - Word: read `.docx` (e.g. `python-docx`), preserving entry boundaries.
   - Notion: export or pull via API; normalize blocks to text.
2. **Delimit & split to one entry per date.** A single Word "Entré #N" with several
   dated passages becomes **one `entries` row per date** (the atomic rule — see
   [database.md](database.md)). The original entry number is dropped.
3. **Parse dates + precision.** Normalize the varied (French) date formats — e.g. *12
   janvier 2018* — to ISO `DATE` ([ADR-007](decisions.md)), and set `date_precision`
   (`day` / `week` / `month` / `year`): fun facts are often a week, books a month, the
   *fête* a year. Flag ambiguous/missing dates for manual fixing rather than guessing.
4. **Clean.** Strip artifacts (encoding gremlins, stray formatting), keep the content.
5. **Classify entry type / target table.** Map each item to its `entry_type` (`journal`,
   `birthday`, `fun_fact`, `prompt`) or to a structured table (`books`,
   `alphabets`, `bingos`, `bucketlist_items`). Often inferable from the source section;
   default to `journal` and refine in the app. Named trips/places (*Espagne 2016*) become
   `events` tags, not entries.
6. **Load.** Prose → `entries` (`nsfw_level` defaults to 0; tagged later). Structured
   types → their own tables (e.g. a book + its citations).
7. **Stage analysis.** People / theme / emotion extraction runs over the prose entries
   as *suggestions* (confidence-gated) for later human review — it finalizes nothing here.

## People & alias resolution

The schema keeps each person once (`people`) with alternate names in `person_aliases`,
so the same individual mentioned as *Mom / Maman / Louise* collapses to one record.

- **Automatic first pass:** match mentions against known aliases; propose merges for
  near-matches.
- **Human confirmation:** the actual "is this the same person?" decision happens in the
  curation app's consolidation queue ([architecture.md](architecture.md#curation-app--capture--review)),
  not blindly in the importer. Aliases grow as new spellings appear.

## Verification before retiring sources

Don't delete the cloud originals until import is checked:
- entry counts reconcile (source vs. `entries`);
- spot-check a sample for content fidelity and correct dates;
- ambiguous-date and unclassified queues are cleared.

Only then archive + remove the Word/Notion originals.

## Open questions (decide when looking at the real files)

- The exact entry-delimiter rule(s) per source.
- How complementary content (quotes, fun facts, yearly tops, letters) is structured in
  the originals and which `entry_type` (or `top_lists` category) each maps to.
- Whether Notion content overlaps/duplicates the Word docs (dedup strategy).
