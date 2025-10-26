lint:
	uvx ruff format
	uvx ruff check --fix --unsafe-fixes

type:
	uvx ty check

autograder: result
	uv run autograder.py

result:
	uv run gg_api.py

test:
	uv run pytest -vls
