lint:
	uvx ty check
	uvx ruff format
	uvx ruff check --fix --unsafe-fixes

autograder:
	uv run autograder.py

test:
	uv run pytest -vls
