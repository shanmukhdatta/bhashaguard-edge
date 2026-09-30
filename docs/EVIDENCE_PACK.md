# Evidence pack specification (schema version 1)

The loader requires `schema_version`, `pack_id`, `version`, `kind` and `entries`.
`kind` is `synthetic_fixture` or `reviewed_evidence`. Changing this field does not validate the contents.

Each entry requires non-empty strings for:

| Field | Meaning |
|---|---|
| `id` | Unique stable evidence ID |
| `language` | `te`, `ta` or `kn` |
| `locale` | An exact scope key, agreed by curators |
| `source_url` | Source URL, or `fixture://` for synthetic data only |
| `source_title` | Human-readable source title |
| `excerpt` | Short licensed evidence passage |
| `translation_en` | Reviewed English translation/gloss, with uncertainty if needed |
| `license` | Terms permitting this use |
| `reviewer` | Reviewer identifier without unnecessary personal data |
| `reviewed_on` | Review date; ISO YYYY-MM-DD recommended |

`supported_forms` is a non-empty array of whole-claim strings. Optional `contradicted_forms` contains explicitly reviewed false forms **in the same scope**. Optional `valid_variants` contains accepted alternate forms; document the geographic/temporal scope in the source excerpt. Never generate contradiction lists by assuming an unlisted practice is false.

The current implementation requires exact locale keys and has no time-range inference. Include time restrictions in the evidence and curated forms where needed. Do not label timeless generalizations as supported based on a dated or narrowly scoped source.

The report includes the exact pack SHA-256 hash. Version the pack whenever its content changes. The loader rejects duplicate IDs, malformed forms and fixture URLs in a reviewed pack. It does not independently validate sources, dates, licences or reviewer qualifications.

For a real study, obtain two native-language annotations and adjudicate disagreements. Keep test labels and answer forms out of the evaluated system's pack to avoid lookup leakage. The bundled demo intentionally uses curated forms for software regression testing and cannot establish held-out benchmark accuracy.
