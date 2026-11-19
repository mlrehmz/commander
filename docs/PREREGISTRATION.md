# Preregistration v1 — 2026-11-19

Status: registered before evaluation; no real corpus or test results yet.
The committed SPEC.md is the full protocol and takes precedence over this summary.

100 projects, at most three invocations each. Leakage groups include forks,
copied templates, near duplicates, and synthetic descendants. Reserve 20 Cobra
and 20 clap projects, with 36/12/12 train/dev/familiar-test projects elsewhere.
Synthetic descendants are training-only. Unknown families are never family-transfer
evidence. Freeze SHA-256 manifests after adjudication. Double-annotate >=20% of
projects blindly; report human/agent identity and adjudication history honestly.

Match exact spelling and invocation scope; score alias sets separately. Normalize
only whitespace for description scoring; evidence is checked exactly. Unsupported
semantic additions are separate from wrong interpretations. Report pooled and
project-macro precision/recall, line macro-F1, field support/accuracy, family and seed
results, selection rate, page status rates, risk–coverage (accepted flags / all
candidate flags), project-bootstrap 95% intervals (2000 draws), and up to 100 errors.

Assembler gate on reference dev labels: precision >=.99, recall >=.90, all emitted
evidence valid. Do not begin substantial training before passing or explicitly
narrowing the supported scope. Neural overfit gate: >=.995 line accuracy on eight
training pages. Seeds: 17, 29, 43; 90 CPU minutes per seed; two threads; atomic,
resumable checkpoints every 600 seconds. Architecture and optimizer are exactly
those in SPEC.md; checkpoint selection uses dev only. Initial ablations: no CNN;
real-only vs mixed. CRF: LBFGS, c1=.1, c2=.1, 100 iterations, possible transitions.

Calibrate record selection on end-to-end dev correctness: maximize macro recall
subject to pooled precision >=.99 and >=500 accepted records. Prefer simplest
qualifying engine. Neural promotion requires >=.03 absolute macro recall gain
and warm p95 <=500ms on <=200-line pages, RSS <=512MiB, artifacts <=50MiB.
No qualifying engine means experimental rules; never weaken criteria after results.

Freeze engine, threshold, schema, matching and evaluator before one final run on
both test tracks. Post-test changes are exploratory. Benchmark fixed dev pages,
two threads, 10 warm-ups and 100 timed repetitions; record OS, CPU, Python,
revision, RSS, artifact bytes, cold subprocess startup separately. Bootstrap by
project, not record. Report sparse-error uncertainty and all unmet gates.
