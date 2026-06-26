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

### 2026-06-24 - Date CHECK used GLOB with LIKE wildcards
- **Issue**: `seed_config` failed with `CHECK constraint failed: author_birthdate GLOB '____-__-__'` for the valid date `2000-08-13`. The same broken pattern was on `entries.date`.
- **Root Cause**: SQLite `GLOB` uses Unix-glob wildcards (`?` = one char, `*` = many); `_`/`%` are LIKE wildcards. So `'____-__-__'` matched four *literal* underscores, not four digits.
- **Solution**: Changed both CHECKs to `GLOB '????-??-??'` in `src/lifebook/db/schema.sql`; rebuilt with `--force` and re-seeded.
- **Prevention**: Use `?`/`*` with GLOB and `_`/`%` with LIKE. For digit-strict checks consider `GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'` if stricter validation is wanted later.
