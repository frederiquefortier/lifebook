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

### 2026-06-24 - Bootstrap the theme list from the corpus

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
- [x] Proposed
- [ ] In Progress
- [ ] Completed
- [ ] Deferred

---

### 2026-06-24 - Closed-set classifier for themes & emotions (local LLM)

**Description:**
- Implement the analysis layer as classification against the closed label lists
  ([ADR-005](../01_building/decisions.md)): per entry, assign multi-label themes and
  emotions with confidence, plus a supporting quote.

**Motivation:**
- Produces consistent, aggregatable, evaluable labels — the basis for the heatmap,
  theme-evolution, and emotion curves in the final cartography.
- Keeps intimate content private and the author in control.

**Potential Approach:**
- A **local** open-weight LLM fed the list (names + `definition` glosses from the seed
  CSVs), returning `{labels, confidence, quote}`; optional embeddings/similarity first
  pass as a cheap cross-check.
- Store discrete emotion labels *and* the continuous `valence` score for smooth
  heatmaps / mood curves.
- Stamp each tag with the `list_version` it was produced under.
- Keep outputs as suggestions gated by `confidence`; spot-review low-confidence rows.
- Build a small hand-labeled gold set (~100 entries) to measure accuracy and tune
  thresholds.

**Priority:**
- [x] High - Critical improvement
- [ ] Medium - Nice to have
- [ ] Low - Future consideration

**Dependencies:**
- Frozen theme list (the bootstrap task above) and emotion set, seeded into the DB.
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
