.PHONY: sync lint fmt fmt-check typecheck smoke vuln lock-check build run check clean

sync:
	uv sync

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

fmt-check:
	uv run ruff format --check .

typecheck:
	uv run mypy

smoke:
	uv run python -m scripts.smoke_test

# Scans the runtime dependencies that ship in the wheel, as pinned in uv.lock.
vuln:
	uv export --frozen --no-dev --no-emit-project --format requirements-txt \
		| uv run pip-audit --strict --disable-pip -r /dev/stdin

lock-check:
	uv lock --check

build:
	uv build

run:
	uv run proxmox-mcp

# Everything CI runs, in CI order.
check: fmt-check lint lock-check typecheck smoke vuln

clean:
	rm -rf dist/ .mypy_cache/ .ruff_cache/
