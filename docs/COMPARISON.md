# Comparison status

No final experimental result is available. The ten-page collection and annotation
pilot is complete, including independent primary/blind agent passes, source
adjudication and source-only audit. The pilot is training data, not human gold.

[Training-pilot diagnostics](PILOT_DIAGNOSTIC.json) recover all 290 advertised flag
spellings and all 205 alias groups with both reference labels and rules labels,
with zero flagged evidence-audit issues. These examples were used to fix the
assembler: the result is a regression check, not a generalization estimate or a
passed development gate. It does not evaluate other catalog fields, model gains,
confidence intervals or resource limits. No engine qualifies for release.

The 100-project corpus, actual development gate, learned record calibration,
three-seed experiment and engine/test freeze remain incomplete. The precision
objective is not demonstrated. No neural-vs-rules claim or negative research
result is made.

Implemented: canonicalization, shared assembler, rules baseline, CRF I/O and
training primitive, manifest validation, oracle-label development gate, bounded
offline container collection, license receipts, independently audited source-only
annotations, token/provenance/transformation audits and hash-bound admission.
CPU neural architecture/inference, overlapping windows, versioned feature cache
with corruption checks, and atomic model/optimizer/RNG checkpoints are implemented
and smoke tested. They have not been trained or evaluated on the research corpus.

Pending: project survey and maintenance/license checks for all prior art;
remaining collection/annotation; full dataset audit and freeze; semantic inference
rules; assembler gate on actual dev references; training orchestration and overfit
gate; three-budgeted seeds and ablations; calibration;
freeze; full metrics, clustered confidence intervals, risk–coverage, error audit,
and cold/warm resource benchmarking. Final evaluation command refuses to run
until these are implemented. It never prints fabricated scores.
