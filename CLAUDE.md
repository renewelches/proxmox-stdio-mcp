# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STDIO-based MCP server that exposes the Proxmox VE API to AI assistants. Uses `proxmoxer` for API access and `mcp[cli]` (FastMCP) for the MCP protocol. Runs as a CLI entry point `proxmox-mcp`.

## Commands

```bash
uv sync              # Install dependencies
uv run proxmox-mcp   # Run the server
uv build             # Build wheel
uv run mypy .        # Type checking (no test suite exists)
```

Always use `uv` — never `pip`. Use modern `uv` commands (`uv add`, `uv sync`, `uv tool`) not legacy `uv pip` equivalents.

## Architecture

- **`proxmox_mcp/server.py`** — Entry point. Creates `FastMCP` instance and registers all modules.
- **`proxmox_mcp/auth.py`** — Builds `ProxmoxAPI` client from env vars. Supports password or API token auth.
- **`proxmox_mcp/formatting.py`** — Converts raw API byte/uptime values to human-readable strings.
- **`proxmox_mcp/errors.py`** — `handle_proxmox_error(required_permission)` decorator. Catches `proxmoxer.core.ResourceException` and converts 403/401/404/500 into clear messages naming the missing Proxmox permission.
- **`proxmox_mcp/resources/`** — Read-only GET operations (nodes, LXC, QEMU, cluster). Each module has a `register(mcp)` function.
- **`proxmox_mcp/tools/`** — Mutation operations: lifecycle (start/stop/reboot), package updates, task tracking. Same `register(mcp)` pattern.

## Resources vs Tools — strict rule

**GET operations MUST be MCP resources (`@mcp.resource()`), never tools.**

- Use `@mcp.resource("proxmox://some/uri")` for any read-only Proxmox API call (HTTP GET).
- Use `@mcp.resource("proxmox://path/{param}/sub")` with URI template parameters for parameterised reads. URI params must exactly match function parameter names. They arrive as `str` regardless of Proxmox type — do not type-hint them as `int`.
- Use `@mcp.tool()` only for operations with side effects (POST/PUT/DELETE).

This maps directly onto the MCP spec: resources are safe, idempotent reads; tools are effectful actions.

## Error Handling

Every resource function and tool must be decorated with `@handle_proxmox_error(permission)` from `proxmox_mcp/errors.py`, where `permission` is the Proxmox permission check string for that endpoint, e.g. `'["perm", "/vms/{vmid}", ["VM.Audit"]]'`. Look up the exact check in the [Proxmox API viewer](https://pve.proxmox.com/pve-docs/api-viewer/).

Decorator order matters — `@mcp.resource()` or `@mcp.tool()` must be outermost:

```python
@mcp.resource("proxmox://nodes/{node}/status")
@handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
def get_node_status(node: str) -> str:
    ...
```

## Adding New Endpoints

1. **Read-only (GET):** add to a module in `resources/`, use `@mcp.resource()` + `@handle_proxmox_error()`
2. **Mutating (POST/PUT/DELETE):** add to a module in `tools/`, use `@mcp.tool()` + `@handle_proxmox_error()`
3. Implement `register(mcp: FastMCP)` and import/call it in `server.py`
