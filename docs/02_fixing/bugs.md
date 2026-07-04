# Bug Log

Track bugs with dates, solutions, and prevention notes. Search this file before debugging familiar-looking issues.

## Format

### YYYY-MM-DD - Brief Bug Description
- **Issue**: What went wrong
- **Root Cause**: Why it happened
- **Solution**: How it was fixed
- **Prevention**: How to avoid it in the future

---

<!-- Add new entries below this line, newest first -->

### 2026-07-04 - Year-in-review letters misclassified when the filename uses '_'
- **Issue**: Year-in-review letters should be `entry_type='birthday'` / `precision='year'`.
  Years 1-5 are filed as `Lettre 2..docx` (label `2.`), but years 6-8 use an underscore,
  `Lettre 6_.docx` (label `6_`). The review regex `^\d+\.$` required a trailing dot, so `6_`
  and `8_` fell through to the single-letter branch and imported as `journal` / `day`. Silent
  misclassification, not a crash.
- **Root Cause**: The regex encoded one filename convention (trailing dot) while `_label()`
  emits several (`2.`, `6_`). `_label` had no direct test, and the review test passed the label
  literally (`"1."`) instead of deriving it from a filename, so the two were never exercised
  together.
- **Solution**: Widened `_REVIEW_LABEL` to `^\d+[._]?$` (dot, underscore, or bare number).
  Added a direct `_label` test and reworked the review test to derive the label via `_label()`
  from real filenames, including the underscore variant. Reviews went 4 -> 6.
- **Prevention**: When a regex classifies the output of another function, test them together on
  real inputs, not on hand-built values that assume the regex's happy path.

### 2026-07-04 - Monthly split silently dropped prose before the first date header
- **Issue**: In the monthly-journal path, paragraphs were only buffered once a date header
  had set the current passage. Any prose before the first header was discarded with no entry,
  no hold-out, and no counter. Measured against the corpus: 101 real paragraphs across 12
  files (e.g. a 28-paragraph list opening `Lettre 2.15`) were vanishing. The single-letter
  path, which keeps all prose, treated the same intro differently, so a file's fate hinged
  only on how many date headers it had.
- **Root Cause**: The split loop's accumulation branch was `elif current and not skipping`,
  and `current` is unset until the first date header. The recap-skip rule was also duplicated
  between this loop and `_prose_paragraphs`, so the two shapes could and did diverge.
- **Solution**: Unified the skip rule into one `_scan` generator that both paths consume.
  Pre-header prose in a monthly file is now collected into a preamble and held out (reason
  "prose before first date header"), never dropped. Also widened `ENTRY_NUMBER` to match
  `Entré #92 (suite)` continuation markers so they are not miscounted as orphan prose.
- **Prevention**: A parser with more than one shape-path must run its filtering through a
  single shared routine. Any paragraph that is neither emitted nor deliberately skipped is a
  silent-loss bug: assert conservation (paragraphs in == kept + held-out + explicitly-skipped).

### 2026-07-04 - Recap-header regex silently deleted prose containing "de l'année"
- **Issue**: The ingestion `SECTION_HEADER` pattern, meant to strip monthly recap headers
  (`Livre du mois :`, `WRAP UPS`, `Livres de l'année`), also matched any paragraph that
  merely contained "de l'année" or "du mois" (e.g. `Bilan de l'année.`). Those paragraphs
  were dropped from the entry content. A unit test on a whole-number review returned 0
  entries, which exposed it.
- **Root Cause**: The alternative `.*\bde l['’]ann[ée]e\b.*` was unanchored, so it matched
  the phrase anywhere in a sentence rather than only on a short standalone header line.
- **Solution**: Narrowed `SECTION_HEADER` to a short `<noun> du mois :` label or the literal
  `WRAP UPS`, and dropped the free "de l'année" alternative (its year-end lists sit under a
  `WRAP UPS` header and are skipped by that). Added a regression test that prose mentioning
  "de l'année"/"du mois" mid-sentence survives.
- **Prevention**: Anchor header patterns to the whole line and keep them narrow. A pattern
  that removes content needs a test proving ordinary prose is kept, not only that headers
  are caught.

### 2026-07-04 - Notion pages parsed to zero (blank line before properties)
- **Issue**: The Notion reader returned 0 kept entries although 14 recent pages exist; the
  date filter never saw a date.
- **Root Cause**: The parser assumed the `Key: value` property block immediately followed
  the H1 title. Notion's export puts a blank line between the title and the properties, so
  the property loop stopped at once and every page had an empty `Date`.
- **Solution**: Skip blank lines between the title and the property block before reading
  properties. Verified 14 entries (Lettre 8.1 to 8.14, Nov 2025 to Jun 2026) come through.
- **Prevention**: When parsing an exported format, check the real file's exact whitespace
  rather than an assumed layout. A "0 results" count is a parser smell, not necessarily
  empty input.

### 2026-06-24 - Date CHECK used GLOB with LIKE wildcards
- **Issue**: `seed_config` failed with `CHECK constraint failed: author_birthdate GLOB '____-__-__'` for the valid date `2000-08-13`. The same broken pattern was on `entries.date`.
- **Root Cause**: SQLite `GLOB` uses Unix-glob wildcards (`?` = one char, `*` = many); `_`/`%` are LIKE wildcards. So `'____-__-__'` matched four *literal* underscores instead of four digits.
- **Solution**: Changed both CHECKs to `GLOB '????-??-??'` in `src/lifebook/db/schema.sql`; rebuilt with `--force` and re-seeded.
- **Prevention**: Use `?`/`*` with GLOB and `_`/`%` with LIKE. For digit-strict checks consider `GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'` if stricter validation is wanted later.
