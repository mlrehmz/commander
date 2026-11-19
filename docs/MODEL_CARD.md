# Experimental rules engine v1

No trained release model. Default selection scores are constant 1.0 rule scores,
not calibrated probabilities or catalog confidence. Unknown value arity, required
presence, defaults, choices, and types remain unknown unless a notation rule is
implemented. Only explicit argument notation currently supplies value arity.

Intended use: supplied English conventional help; file/stdin only. No command
execution or hierarchy discovery. Not validated for production precision.
Known limits: unindented option lists, wrapped metavariables, single-space
ambiguous layouts, semantic prose, duplicate-description reconciliation, and
unusual command/positional layouts may be omitted. Unsupported sections may not
always be recognized. Unknown optional semantics alone do not cause partial.

CRF training/inference code has a real tiny-fixture integration test only. The
CRF is not a selected or calibrated engine. A CPU-only neural implementation now
combines a 16-dimensional byte embedding and parallel kernel-3/kernel-5 CNNs
(32 channels each) with ten numeric features, followed by a two-layer bidirectional
GRU (128 hidden units/direction, dropout .1) and linear head. Feature-only mode
supports the planned no-CNN ablation. Only first 48 bytes enter the CNN; full
source stays available to assembly. Packed sequences exclude line padding.

Inference batches at most eight 256-line windows with 32 overlap, choosing each
line's prediction from the window providing most context (earlier window wins
ties). Features are keyed by text/config hashes; payload corruption rebuilds the
cache. Atomic checkpoints save model/optimizer, Python/Torch RNG states, seed,
step, elapsed budget, feature/model config, Torch version and code revision.
A smoke test proves exact next-step recovery and revision mismatch rejection.

No trained neural weights, overfit result, calibrated policy or seed comparison is
available. Training orchestration, training gates, checkpoint scheduling and
ablations remain unrun/unimplemented as described in COMPARISON.md. Neural line
probabilities are not record confidence. `--engine neural` is experimental and
requires a checkpoint plus an explicit uncalibrated policy. Runtime rules never
import neural dependencies.
