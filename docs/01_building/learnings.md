# Learnings

Document new concepts, techniques, and knowledge gained. Reference this file to build on past learning and find resources for deeper understanding.

## Format

### YYYY-MM-DD - Learning Title

**What Was New:**
- Core concept or technique learned
- Context of when it came up

**Key Points:**
- Important details to remember
- How it works or why it matters

**Sources:**
- Documentation links
- Articles or tutorials referenced
- Code examples or repositories

**Where to Learn More:**
- Advanced resources
- Related topics to explore
- Practice exercises or projects

**Applied In:**
- Where/how this was used in practice (optional)

---

<!-- Add new entries below this line, newest first -->

### 2026-06-24 - pathlib, functions/type hints, and a single DB front door

**What Was New:**
- Concepts from `lifebook/db/__init__.py`: robust file paths, function definitions with
  type hints, and centralizing DB connections.

**Key Points:**
- **Robust paths with `pathlib`:** `Path(__file__).resolve().parent` gives the folder of
  the current file; walking `.parent` upward derives the repo root. Building paths this
  way means commands work regardless of the current working directory (vs hard-coding
  `"data/local/life.db"`). `__file__` ≈ Node's `__filename`.
- **`/` joins Path segments:** `REPO_ROOT / "data" / "seed"` ≈ `path.join(...)`, and it
  uses the OS-correct separator. UPPERCASE names = "constant" convention; leading `_`
  (e.g. `_DB_DIR`) = "internal, don't import elsewhere" convention.
- **Functions & type hints:** `def connect(path: Path | str = LIFE_DB_PATH) -> sqlite3.Connection:`.
  Here `path: Path | str` is a type hint (optional, TypeScript-style; `|` = "or"),
  `= LIFE_DB_PATH` is a default argument, `-> ...` is the return type. `from __future__
  import annotations` at the top enables modern hint syntax (boilerplate).
- **Single DB front door:** every client opens the DB via `connect()`, which always runs
  `PRAGMA foreign_keys = ON` (FK enforcement is per-connection + OFF by default in
  SQLite) and sets `row_factory = sqlite3.Row` (read columns by name, `row["slug"]`,
  instead of by index `row[0]`). Define the safety/convenience once, get it everywhere.

**Sources:**
- [pathlib](https://docs.python.org/3/library/pathlib.html),
  [typing](https://docs.python.org/3/library/typing.html),
  [sqlite3.Row](https://docs.python.org/3/library/sqlite3.html#sqlite3.Row).

**Applied In:**
- `src/lifebook/db/__init__.py` (`connect()` + path constants).

### 2026-06-24 - Python modules, packages, __init__.py, docstrings

**What Was New:**
- What makes a folder an importable package, and why `__init__.py` files exist.

**Key Points:**
- **Module** = a single `.py` file. **Package** = a *folder* marked by an `__init__.py`
  file (which can contain sub-packages). The folder/file names are the import names.
- `__init__.py` signals "this folder is an importable package" and runs once on first
  import: the natural home for package-level setup or just a docstring. Rough Node
  analogy: `__init__.py` ≈ a folder's `index.js` (the entry point when you import a folder).
- Ours is intentionally empty except a docstring: existence makes `lifebook`
  importable; we deliberately don't re-export anything, so imports stay explicit
  (`from lifebook.db import connect`) and cheap.
- **Docstring** = a `"""triple-quoted"""` string at the top of a module/function; Python
  keeps it as the object's official documentation (like JSDoc, but a real string).
- Import dots map to the folder tree: `from lifebook.db import connect` = package →
  sub-package → name. "Dunder" = double-underscore, Python's marker for special names
  (`__init__`, `__name__`, …).

**Sources:**
- [Python tutorial: Modules & Packages](https://docs.python.org/3/tutorial/modules.html),
  [PEP 257: docstrings](https://peps.python.org/pep-0257/).

**Applied In:**
- `src/lifebook/__init__.py` and every sub-package's `__init__.py`.

### 2026-06-24 - Pinning the Python version (.python-version)

**What Was New:**
- The role of the one-line `.python-version` file, and how it differs from
  `requires-python` ([ADR-008](decisions.md)).

**Key Points:**
- `.python-version` is a one-line file (`3.12`) naming the exact Python the project
  develops on. `uv` reads it and uses that version, even auto-downloading it if the
  machine doesn't have it (we saw it fetch CPython 3.12.13).
- Distinct from `pyproject.toml`'s `requires-python = ">=3.12"`, which sets the minimum
  allowed. So: `.python-version` = "the exact one we use"; `requires-python` = "the
  floor we support".
- Committed to Git so the pin travels with the project, with no "which Python?" drift across
  machines. Especially valuable here, where the box has 2.7 (`python`) and 3.11 (`py`).
- Roughly the Python equivalent of `.nvmrc` for Node.

**Sources:**
- [uv: Python versions](https://docs.astral.sh/uv/concepts/python-versions/).

**Applied In:**
- `.python-version` (repo root) + `requires-python` in `pyproject.toml`.

### 2026-06-24 - Python build backends (and why hatchling)

**What Was New:**
- Came up explaining `pyproject.toml`'s `[build-system]` block ([ADR-008](decisions.md)).

**Key Points:**
- Making code an installable package (so `import lifebook` works after `uv sync`)
  requires a **build backend**: the tool that turns the source folder into an
  installable "wheel". It's what `[build-system]` names.
- Python splits this in two (PEP 517): a build **frontend** (the tool you run, `uv` or
  `pip`) calls a build **backend** (does the actual building, `hatchling`). You interact
  with the frontend constantly and the backend essentially never.
- **Why hatchling here:** it's uv's default, needs minimal config (our whole build is one
  line, `packages = ["src/lifebook"]`), is standards-based (pure `pyproject.toml`, no
  `setup.py`), and well-maintained.
- **Low-stakes / swappable:** the backend only affects how the package is *built/installed*;
  it does not change how the code *runs*. Alternatives: `setuptools` (older, more powerful, noisier
  config), `flit-core` (minimal), `maturin` (for Rust). Switching later is a few lines.

**Sources:**
- [Hatchling](https://hatch.pypa.io/latest/), [PEP 517 (build backends)](https://peps.python.org/pep-0517/),
  [packaging overview](https://packaging.python.org/en/latest/).

**Applied In:**
- `pyproject.toml` `[build-system]` + `[tool.hatch.build.targets.wheel]`.

### 2026-06-24 - SQLite gotchas + Python packaging (uv, src-layout)

**What Was New:**
- Concepts that shaped the data-layer foundation ([sessions.md](sessions.md),
  [ADR-008/009/010](decisions.md)).

**Key Points:**
- **`PRAGMA foreign_keys` is per-connection and defaults OFF** in SQLite. FK constraints
  are silently *not enforced* unless every connection turns it on; hence the shared
  `lifebook.db.connect()` helper.
- **`GLOB` ≠ `LIKE` wildcards.** `GLOB` uses `?` (one char) / `*` (many); `LIKE` uses `_`
  / `%`. Mixing them silently breaks pattern CHECKs (see [bugs.md](../02_fixing/bugs.md)).
- **No native date type.** Dates are stored as `TEXT` ISO-8601 (`YYYY-MM-DD`), which sorts
  chronologically and reads forever; `date_precision` controls rendering.
- **`AUTOINCREMENT` prevents id reuse.** Plain `INTEGER PRIMARY KEY` can reuse the id of a
  deleted highest row; `AUTOINCREMENT` guarantees monotonic, never-reused ids.
- **No `ON UPDATE` for columns.** `updated_at` is maintained by a per-table `AFTER UPDATE`
  trigger, with a `WHEN OLD.updated_at = NEW.updated_at` guard to avoid recursion.
- **uv + src-layout.** uv pins the interpreter (`.python-version`) so `uv run` always uses
  the right Python; the **src-layout** (`pyproject.toml` at root, package under `src/`)
  means code is imported only when installed: tests run against the installed package,
  catching packaging mistakes.

**Sources:**
- SQLite: [foreign keys](https://www.sqlite.org/foreignkeys.html),
  [GLOB/LIKE](https://www.sqlite.org/lang_expr.html#like),
  [AUTOINCREMENT](https://www.sqlite.org/autoinc.html),
  [date/time](https://www.sqlite.org/lang_datefunc.html).
- Python: [uv docs](https://docs.astral.sh/uv/),
  [src-layout vs flat](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).

**Applied In:**
- `src/lifebook/db/` (schema.sql, connect(), build/seed scripts) and the project layout.
