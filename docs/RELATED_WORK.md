# Related work — initial notes

[Fish's man-page extractor](https://github.com/fish-shell/fish-shell/blob/master/share/tools/create_manpage_completions.py)
uses deterministic document parsing to create shell completions. Completion files
can supply metadata but have a different contract from evidence-backed catalogs.
[help2man](https://github.com/coreutils/coreutils/blob/master/man/help2man) converts
help into manual-page material. Neither observation establishes extraction accuracy.

[CRFs](https://home.cs.colorado.edu/~mozer/Teaching/syllabi/6622/papers/LaffertyMcCallumPereira2001.pdf)
are an established structured prediction technique. HelpCat proposes to compare
line taggers while holding assembly and semantics fixed, using evidence fidelity,
abstention, project grouping, and unseen-family tests. This comparison is the
planned contribution, not a new CRF or completion-generation algorithm. The
comparison has not yet been run; these notes make no novelty or accuracy claim.
