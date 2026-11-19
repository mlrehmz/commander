.PHONY: check assembler-gate final-evaluation
check:
	uv run --locked --group dev --group research --group neural ruff check src tests collection/*.py
	uv run --locked --group dev --group research --group neural ruff format --check src tests collection/*.py
	uv run --locked --group dev --group research --group neural pytest -q
	uv run --locked python -m helpcat.experiment validate

assembler-gate:
	uv run --locked python -m helpcat.experiment assembler-gate

final-evaluation:
	uv run --locked python -m helpcat.experiment final
