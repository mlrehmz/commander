# Corpus expansion and reproduction

This is a provisional collection record, not a frozen benchmark. The survey covers 100 project candidates and records 100 captured help pages. Ten pilot references are source-audited and admitted to training; additional annotations, renderer-family review, leakage grouping and split freeze remain incomplete. The 40 Cobra/clap held-out help pages are kept outside the repository pending redistribution review and must remain unavailable during development.

## Collection controls

Python projects use isolated, hash-locked environments. Native artifacts are recorded by URL and digest. Help is collected only inside constrained offline containers with pinned inputs, bounded runtime/output, and non-root execution. Harvested executables are never run directly on the host. See the [collection protocol](../../docs/COLLECTION_DESIGN.md), and the recorded receipts and plans beside this file.

The source survey distinguishes parser implementation from actual help-renderer family; framework imports alone do not establish the output format. Failed captures retain separate receipts and do not count as valid examples. The dataset inventory and split proposal are provisional until source review and reference audits are complete.

## Reproduce development checks

The standard parser and corpus checks are documented in the repository [README](../../README.md). Collection itself requires Podman and the collection-specific locked dependencies; it is not needed to install or use the library. Follow [collection/README.md](../README.md) for the pilot collector setup and safety boundary.

Raw captures and annotations are research artifacts. Review their source and redistribution status before republishing or using them as evaluation truth. The checked-in ten-page pilot is agent-annotated, adjudicated and audited; it is training-only, not human gold or an independent evaluation set.
