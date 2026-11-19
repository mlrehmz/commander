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
CRF is not a selected or calibrated engine. No neural architecture, training run,
overfit gate, feature cache, checkpoint recovery, or ablation is implemented yet.
Those remain downstream of the unpassed assembler/data gates.
