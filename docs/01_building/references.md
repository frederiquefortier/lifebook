# References

External links consulted during research, design, and implementation. A reference here does
not imply adoption.

<!-- Add links below -->

## Data layer
- [SQLite](https://www.sqlite.org/) — single-file database chosen as the source of truth ([ADR-001](decisions.md)).

## Processing layer
- [Python](https://www.python.org/) — processing/scripting language.
- [spaCy](https://spacy.io/) — NLP for entity (people) extraction and analysis; use a French model ([`fr_core_news_*`](https://spacy.io/models/fr)) per [ADR-007](decisions.md).
- [Hugging Face Transformers](https://huggingface.co/docs/transformers) — theme and emotion classification (French-capable models).

## Curation app
- [React](https://react.dev/) + [TipTap](https://tiptap.dev/) — editor frontend ([ADR-006](decisions.md)).
- [FastAPI](https://fastapi.tiangolo.com/) — thin local backend over `life.db`.
- [Leaflet](https://leafletjs.com/) / [MapLibre](https://maplibre.org/) — candidate libs for the **map module** (location tagging + the map cartography). Geocoding (place search → lat/lng) is an implementation-time choice; prefer something that can run offline / self-hosted to keep with the local-first principle.

## Publication layer
- [Adobe InDesign](https://www.adobe.com/products/indesign.html) — print layout / render engine.
- [Affinity Publisher](https://affinity.serif.com/publisher/) — alternative layout / render engine.

## Editorial inspiration
- *Twilight* (book interior) — inspiration for the minimalist monthly separator pages (see [product.md](../00_briefing/product.md)).

## Backup targets
- [Google Drive](https://drive.google.com/), [Dropbox](https://www.dropbox.com/), [iCloud](https://www.icloud.com/) — candidate cloud copies for the 3-2-1 rule ([ADR-004](decisions.md)).
