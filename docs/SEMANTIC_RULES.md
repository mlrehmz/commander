# Rules v2: evidence and supported interpretations

All taggers share these assembler policies. None uses a formatter-specific adapter.
Canonical text, tabs, Unicode coordinates and exact literals are preserved.

- Explicitly grouped aliases use declaration punctuation or columns in a bordered
  row. A substring of a long alias is not a separately advertised short alias.
- `<dir>`, `NAME`, lowercase placeholders, compound `PROTOCOL:ADDRESS`, nested
  `USER[:PASS] | TOKEN`, repeated `d [d ...]` and `INTEGER RANGE` remain literal
  metavars. Their presence supplies required value arity without semantic typing.
- `[=WHEN]` and separate uppercase `[CONFIG]` supply optional value notation.
  Bracketed pipe alternatives leave arity unknown because formatter conventions
  differ. No metavar alone does not establish arity none.
- Literal choices are exposed only for explicit comma-delimited `{a,b}` or
  pipe-delimited `[a|b]` notation with simple word/dot/plus/minus members. Choices
  retain the exact interior string; no typed list or value validation is inferred.
- A single complete inline `(default: VALUE)` or `[default: VALUE]` in description
  evidence supplies a direct string default. Whitespace around VALUE is excluded.
  Nested same-delimiter values, wrapped markers, multiple markers and prose-only
  defaults abstain. Literal `None`, `False`, `[]` and numbers are strings with
  evidence, distinct from an unknown field (`null`). Dynamic defaults stay unknown.
- Description spans may cross blank lines and contain examples/flag-like text.
  Their normalized wrapped value collapses whitespace; literals/spans retain it.
  Bordered-row padding and borders are excluded from description spans.
- Standalone advertised names may have descriptions on following lines.
  Parenthesized command aliases are emitted as separate explicitly printed names.
  No hierarchy, ordering, occurrence limits or required option presence is inferred.
- Unseparated short clusters and single-dash long names are not guessed as a short
  alias plus an attached bare metavar. Explicit `-I<dir>` remains supported.

Reference auditing additionally checks transformations, provenance and token
boundaries. Original drafts can fail this stronger audit while remaining valid
JSON with substring-fidelity evidence; adjudication preserves and corrects their
errors rather than rewriting the drafts. Source audits are not model confidence.
