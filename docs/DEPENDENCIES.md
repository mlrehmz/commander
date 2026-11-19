# Dependencies and reproducible setup

Use Python 3.12 or 3.13 with [uv](https://docs.astral.sh/uv/). The committed `uv.lock` fixes resolved versions and artifact hashes. Runtime dependencies are deliberately separate from development and model dependencies.

| Profile | Packages | Install/use |
|---|---|---|
| Runtime | `jsonschema` | `uv sync --locked` |
| Development | `pytest`, `hypothesis`, `ruff` | `uv sync --locked --group dev` |
| CRF research | `python-crfsuite` | `uv sync --locked --group research` |
| Neural research | CPU-only `torch` | `uv sync --locked --group neural` |
| Full checks | All of the above | `uv sync --locked --all-groups`, then `make check` |
| Collection | Separately pinned binary wheels in `collection/requirements.lock` | Only needed to rebuild the constrained collection image; Podman is also required |

The dependency metadata below is the lockfile inventory gathered during development. License labels are package metadata, not legal advice or a substitute for checking the upstream license.

| Package | Version | License metadata |
|---|---|---|
| attrs | 26.1.0 | MIT |
| filelock | 4.2.12 | MIT |
| fsspec | 2026.9.0 | BSD-3-Clause |
| hypothesis | 6.140.3 | MPL-2.0 |
| iniconfig | 2.3.1 | MIT |
| Jinja2 | 3.1.6 | License :: OSI Approved :: BSD License |
| jsonschema | 4.25.1 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| mpmath | 1.3.0 | BSD |
| networkx | 3.7 | BSD-3-Clause |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pytest | 8.4.2 | MIT |
| python-crfsuite | 0.9.12 | MIT License |
| referencing | 0.37.0 | MIT |
| rpds-py | 2026.9.1 | MIT |
| ruff | 0.14.0 | License :: OSI Approved :: MIT License |
| setuptools | 84.2.1 | MIT |
| sortedcontainers | 2.4.0 | Apache 2.0 |
| sympy | 1.14.0 | BSD |
| torch | 2.9.0+cpu | BSD-3-Clause |
| typing_extensions | 4.16.0 | PSF-2.0 |

CPU-only Torch uses the explicit PyTorch CPU package index; runtime dependencies remain separate. Collection dependencies have their own hash-locked file and exact primary-package notices. `make check` exercises the development environment; metadata alone is not a legal review.
