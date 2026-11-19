.PHONY: check assembler-gate final-evaluation
check:
	uv run --locked --group dev --group research ruff check src tests
	uv run --locked --group dev --group research ruff format --check src tests
	uv run --locked --group dev --group research pytest -q
	uv run --locked python -m helpcat.experiment validate

assembler-gate:
	uv run --locked python -m helpcat.experiment assembler-gate

final-evaluation:
	uv run --locked python -m helpcat.experiment final
