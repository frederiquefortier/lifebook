# data/seed/: closed label lists (source of truth)

These CSVs are the source of truth for the three classifier-read label lists.
`seed_labels.py` loads them into the `themes` / `emotions` / `nsfw_tags` tables in
`life.db` (the runtime copy). Edit a CSV, re-run the seed.

- **Format:** comma-delimited, UTF-8, RFC-4180 quoting. `slug` is a stable English key;
  `name` / `definition` are French. `status` is `active` | `deprecated`.
- **Sync rule:** the CSV is fully authoritative. A slug present sets its fields and
  status; a slug removed from the CSV is marked `deprecated` (never deleted), so
  historical tags stay valid. Re-add a slug as `active` to reactivate it.

`themes.csv` is a frozen, full-life set with immutable meanings: a theme is an *aboutness*
(a subject an entry is about). It is never a mode of writing or a feeling. It grows only by
appending a new life-domain; there is no `other`. Emotions differ: their
`valence` / `arousal` anchors are re-tunable by `slug` on re-seed.

Editorial lists with no classifier behind them (people, events, places, `top_categories`)
are not here. They're managed in the app and live only in the DB.
