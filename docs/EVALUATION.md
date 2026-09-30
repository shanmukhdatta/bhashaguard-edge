# Evaluation plan and leakage boundaries

## Software regression suite

The bundled synthetic fixtures exercise four labels across three languages. They are deliberately present in the evidence pack and are not held-out evaluation data. Passing these tests establishes selected software behaviours only.

Additional tests cover script exclusions, empty denominators, Unicode offsets, added negation, evidence-label conflicts, locale mismatch, unsafe endpoint rejection, local HTTP analysis, CSRF/origin checks and traversal rejection.

## Proposed research evaluation

Start with a native-speaker-reviewed Telugu set. A later target is 300 prompt-response cases per language with supported facts, contradictions, script errors, missing evidence, prompt/context mismatch and valid regional variants. This dataset has not been collected here.

Use two annotators with adjudication, document disagreement and keep dialect/locale labels explicit. Split topics/entities and source families to reduce leakage. Freeze test labels, source snapshots and the evidence-pack version. Avoid placing exact test answers or contradictory forms into the pack used by the evaluated system.

Compare script-only checking, lexical/embedding retrieval, an ungrounded local-model judge and the full proposed guard. Measure macro-F1, per-language precision/recall, valid-variant false alarms, retrieval Recall@k, claim-extraction recall, citation validity and abstention versus error. Report denominators and confidence intervals.

The current exact-form baseline will abstain on many unseen paraphrases. That limitation should remain visible. Do not interpret its synthetic-case success as general cultural accuracy.

## Risk calibration

Keep categorical findings until sufficient independent labelled data exists. If a later version fits a risk probability, separate development/calibration/test splits, define the target event and report calibration error or Brier score on held-out cases. Missing evidence is a coverage limitation, not proof of hallucination.

## Runtime evaluation

`python -m bhashaguard benchmark` measures whole-analysis warm latency on the bundled CPU fixtures. It records platform, Python, backend and pack hash. The timing includes script checking, matching and retrieval. It excludes process startup and model loading. Memory, power and CPU/NPU comparisons remain separate work described in SNAPDRAGON.md.
