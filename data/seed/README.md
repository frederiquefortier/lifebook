# data/seed/ — closed label lists (source of truth)

These CSVs are the **source of truth** for the three classifier-read label lists
(ADR-005). `seed_labels.py` loads them into the `themes` / `emotions` / `nsfw_tags`
tables in `life.db` (the runtime copy). Edit a CSV, re-run the seed.

- **Format:** comma-delimited, UTF-8, RFC-4180 quoting. `slug` is a stable English key;
  `name` / `definition` are French (ADR-007). `status` is `active` | `deprecated`.
- **Sync rule:** the CSV is fully authoritative — a slug present sets its fields and
  status; a slug removed from the CSV is marked `deprecated` (never deleted), so
  historical tags stay valid. Re-add a slug as `active` to reactivate it.

> **`themes.csv` is frozen, not provisional ([ADR-012](../../docs/01_building/decisions.md)).**
> It is a stable, full-life set with **immutable meanings**: a theme is an *aboutness* (a
> subject an entry is *about*), never a mode of writing or a feeling. The list grows only by
> **appending** a genuinely new life-domain — existing slugs/meanings are never redrawn or
> deleted — and there is **no `other`**: an entry that fits no theme simply carries none.
> By contrast, emotions' `valence`/`arousal` anchors *are* re-tunable by `slug` on re-seed
> (ADR-011).

Editorial lists with no classifier behind them (people, events, places,
`top_categories`) are **not** here — they're managed in the app and live only in the DB.
