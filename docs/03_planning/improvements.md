# Improvements

Track future enhancements and feature ideas. Review this file during planning sessions to prioritize next steps.

## Format

### YYYY-MM-DD - Improvement Title

**Description:**
- What the improvement would do
- Problem it would solve or value it would add

**Motivation:**
- Why this would be beneficial
- Use cases or scenarios

**Potential Approach:**
- Initial thoughts on implementation
- Technologies or patterns to consider

**Priority:**
- [ ] High - Critical improvement
- [ ] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- Prerequisites or related work needed
- Blockers or considerations

**Status:**
- [ ] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred

---

<!-- Add new entries below this line, newest first -->

### 2026-07-04 - First-class handling for répertoires, goal-bilans, and prompts

**Description:**
- A set of letters are not journal prose: répertoires (curated overviews of other letters or
  of a person, e.g. 3.8, 4.5, 4.6, 5.5), goal lists with a bilan (5.1, 5.4, and the "Mai
  Goals" block inside 3.0.10), and prompts (2.7, 2.15, 7.0.5). They are currently *deferred*
  via `date_overrides.toml` ([ADR-015](../01_building/decisions.md)) as `skip`, or collapsed
  into one `whole` entry, so they stop polluting the corpus with bogus daily entries.
- Give them a proper representation instead of skip-or-blob.

**Motivation:**
- These carry real content that belongs in the book, but not as fake journal entries: the
  répertoires especially (the author: "I love it, but I don't know how to keep it as is").
- `entry_types` already has `prompt`; the goal lists relate to the `goals` table in the
  schema. Only the répertoire has no natural home yet.

**Potential Approach:**
- Decide a representation per kind: prompts -> `entry_type = 'prompt'`; goal lists -> the
  `goals` table (added / checked / removed over time); répertoires -> a new entry type or a
  dedicated render block.
- Once modeled, replace the `skip` / `whole` overrides for those files with real ingestion.
- Chase the "there should be more than 2" goal-bilan files: the override scan already flags
  candidates (multi-month, non-chronological headers); confirm and route them here.

**Owner / when:** the author decides the répertoire representation during the special-types
pass, once the curation app ([ADR-006](../01_building/decisions.md)) exists to review these by
hand; until then the `skip` overrides are the deliberate holding pattern, not an oversight.

**Priority:**
- [ ] High - Critical improvement
- [x] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- Schema decisions on new/extended entry types; the override layer
  ([ADR-015](../01_building/decisions.md)) is the current holding pattern.

**Status:**
- [x] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred

---

### 2026-06-24 - Bootstrap the theme list from the corpus

> **Superseded by [ADR-012](../01_building/decisions.md) (2026-06-25).** The author chose to
> anticipate a stable, full-life theme set up front instead of discovering it from a corpus
> sample, and dropped the `other` bucket. `data/seed/themes.csv` is frozen at 21 themes with
> immutable, append-only meanings. Kept below for history.

**Description:**
- Before freezing the closed theme list (see [ADR-005](../01_building/decisions.md)),
  run a discovery pass over a representative sample of entries to find the *actual*
  recurring themes of the life, then curate that into `data/seed/themes.csv`.

**Motivation:**
- A life's themes are idiosyncratic; a generic, a-priori list will both miss real
  themes and include ones that never occur.
- Aggregation quality (the whole point of the cartography) depends on the list
  matching reality.

**Potential Approach:**
- Embed a sample of entries; cluster (e.g. topic modeling / embedding clusters) to
  surface candidate themes; review and name the clusters.
- Write v1 into `data/seed/themes.csv` (with `definition` glosses), seed it into the DB
  via `seed_labels.py`, and tag the full corpus against it under `list_version` 1.
- Periodically review the `other` bucket to grow later versions.

**Priority:**
- [x] High - Critical improvement
- [ ] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- A populated `entries` table (ingestion done) and the closed-list decision
  ([ADR-005](../01_building/decisions.md)).

**Status:**
- [ ] Proposed
- [ ] In Progress
- [ ] Completed
- [x] Deferred: superseded by ADR-012

---

### 2026-06-24 - Closed-set classifier for themes & emotions (local LLM)

**Description:**
- Implement the analysis layer as classification against the closed label lists
  ([ADR-005](../01_building/decisions.md)): per entry, assign multi-label themes and
  emotions with confidence, plus a supporting quote.

**Motivation:**
- Produces consistent, aggregatable, evaluable labels: the basis for the heatmap,
  theme-evolution, and emotion curves in the final cartography.
- Keeps intimate content private and the author in control.

**Potential Approach:**
- A local open-weight LLM fed the list (names + `definition` glosses from the seed
  CSVs), returning `{labels, confidence, quote}`; optional embeddings/similarity first
  pass as a cheap cross-check.
- Store discrete emotion labels *and* the continuous `valence` score for smooth
  heatmaps / mood curves.
- Stamp each tag with the `list_version` it was produced under.
- Allow zero themes per entry: there is no `other` bucket; an entry that fits no theme
  gets none ([ADR-012](../01_building/decisions.md)). Confidence gating must never force a pick.
- Keep outputs as suggestions gated by `confidence`; spot-review low-confidence rows.
- Build a small hand-labeled gold set (~100 entries) to measure accuracy and tune
  thresholds.

**Priority:**
- [x] High - Critical improvement
- [ ] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- Frozen theme list ([ADR-012](../01_building/decisions.md)) and emotion set, seeded into the DB.
- Populated `entries`; `entry_themes` / `entry_emotions` join tables.

**Status:**
- [x] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred

---

### 2026-06-24 - Automated layout / digital renderer

**Description:**
- Automate the export → layout step, and/or build a digital (web) book renderer as an
  additional render target for the same data.

**Motivation:**
- Today the InDesign step is manual and redone if a decade is regenerated.
- A scripted renderer would make "reconstruct any decade from the data" closer to
  one command, and enable an interactive web edition.

**Potential Approach:**
- Generate InDesign-ready exports (IDML/tagged text) from Python.
- In parallel, develop a web renderer fed by the same `life.db` exports.

**Priority:**
- [ ] High - Critical improvement
- [x] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- Stable data export format from the processing layer ([architecture.md](../01_building/architecture.md)).

**Status:**
- [x] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred

---

### 2026-06-24 - Future-volume reproducibility pass

**Description:**
- Harden the pipeline so any future volume (next date range) can be produced by
  re-running the same scripted process with minimal manual setup.

**Motivation:**
- The core vision is repeated publication from the same durable system.
- Reproducibility is the difference between an archive and a one-off book.

**Potential Approach:**
- Parameterize scripts by date range (the volume = `date_range_start … date_range_end`).
- Snapshot tool versions; document the environment for the Future Self persona.

**Priority:**
- [ ] High - Critical improvement
- [ ] Medium - Nice to have
- [x] Low - Future consideration

**Dependencies:**
- A working end-to-end first-volume pipeline.

**Status:**
- [x] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred
