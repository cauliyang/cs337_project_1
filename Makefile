lint:
	uvx ruff format
	uvx ruff check --fix --unsafe-fixes

type:
	uvx ty check

autograder:
	uv run autograder.py

test:
	uv run pytest -vls
